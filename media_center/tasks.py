import mimetypes
import os
import shutil
import subprocess
import tempfile

import boto3
import requests
from celery import shared_task
from django.conf import settings

from .models import Media


@shared_task
def generate_hls_for_media(video_url: str, media_id: int):
    print(f"📥 Downloading video from: {video_url}")

    input_file = download_video_to_temp_file(video_url)
    if not input_file:
        print("❌ Aborting: download failed.")
        return

    output_dir = os.path.join(settings.MEDIA_ROOT, "hls", str(media_id))
    os.makedirs(output_dir, exist_ok=True)

    bitrates = {
        "360p": {"scale": "640:360", "bitrate": "800k", "maxrate": "856k", "bufsize": "1200k"},
        "480p":  {"scale": "854:480",  "bitrate": "1400k", "maxrate": "1498k", "bufsize": "2100k"},
        "720p":  {"scale": "1280:720", "bitrate": "2800k", "maxrate": "2996k", "bufsize": "4200k"},
        "1080p": {"scale": "1920:1080","bitrate": "5000k", "maxrate": "5350k", "bufsize": "7500k"},
    }

    for label, config in bitrates.items():
        transcode_to_hls_variant(input_file, output_dir, label, config)

    create_master_playlist(output_dir, bitrates)

    # upload hls directory to remote server
    dest_path = f'media/v1/video-files/{media_id}_v2'
    upload_folder_to_spaces(output_dir, dest_path)

    # update media hls_playlist field
    media = Media.objects.get(id=media_id)
    hls_base_url = f"{settings.HLS_PLAYLIST_SERVER}/media"
    media.hls_playlist = f"{hls_base_url}/v1/video-files/{media.id}_v1/master_playlist.m3u8"
    media.save(update_fields=['hls_playlist'])

    print(f"✅ HLS generated and uploaded for media {media_id}")


def download_video_to_temp_file(url: str) -> str | None:
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
            response = requests.get(url, stream=True)
            if response.status_code != 200:
                print(f"❌ Failed to download video: HTTP {response.status_code}")
                return None

            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)

            print(f"✅ Downloaded to: {temp_file.name}")
            return temp_file.name
    except Exception as e:
        print(f"❌ Exception during download: {e}")
        return None


def transcode_to_hls_variant(input_file: str, base_dir: str, label: str, config: dict):
    output_dir = os.path.join(base_dir, label)
    os.makedirs(output_dir, exist_ok=True)

    output_playlist = os.path.join(output_dir, "playlist.m3u8")
    segment_pattern = os.path.join(output_dir, "segment_%03d.ts")

    ffmpeg_cmd = [
        "ffmpeg", "-i", input_file,
        "-vf", f"scale={config['scale']}",
        "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2", "-profile:a", "aac_low",
        "-c:v", "libx264", "-profile:v", "main",
        "-crf", "20", "-sc_threshold", "0",
        "-g", "48", "-keyint_min", "48",
        "-movflags", "+faststart",
        "-preset", "fast", "-threads", "0",
        "-b:v", config["bitrate"],
        "-maxrate", config["maxrate"],
        "-bufsize", config["bufsize"],
        "-hls_time", "6",
        "-hls_segment_filename", segment_pattern,
        "-hls_playlist_type", "vod",
        output_playlist
    ]

    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print(f"✅ Transcoded {label}")
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg failed for {label}: {e}")


def create_master_playlist(base_dir: str, bitrates: dict):
    master_path = os.path.join(base_dir, "master_playlist.m3u8")
    with open(master_path, "w") as f:
        f.write("#EXTM3U\n#EXT-X-VERSION:3\n")
        for label, config in bitrates.items():
            w, h = config["scale"].split(":")
            bandwidth = int(config["bitrate"][:-1]) * 1000
            f.write(f'#EXT-X-STREAM-INF:BANDWIDTH={bandwidth},RESOLUTION={w}x{h}\n')
            f.write(f'{label}/playlist.m3u8\n')
    print(f"🎞️ Master playlist created: {master_path}")


def upload_folder_to_spaces(local_dir: str, dest_path: str):
    if settings.DEBUG:
        print("⚠️ DEBUG mode: Skipping upload to DigitalOcean Spaces.")
        return

    session = boto3.session.Session()
    client = session.client(
        "s3",
        region_name=settings.HLS_PLAYLIST_REGION,
        endpoint_url=settings.HLS_PLAYLIST_DOMAIN,
        aws_access_key_id=settings.SPACES_ACCESS_KEY,
        aws_secret_access_key=settings.SPACES_SECRET_KEY
    )

    for root, _, files in os.walk(local_dir):
        for file in files:
            local_path = os.path.join(root, file)
            relative_path = os.path.relpath(local_path, local_dir)
            s3_key = os.path.join(dest_path, relative_path)

            content_type, _ = mimetypes.guess_type(local_path)
            content_type = content_type or 'application/octet-stream'

            client.upload_file(
                local_path,
                settings.SPACES_BUCKET_NAME,
                s3_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "ACL": "public-read" 
                    }
            )
            print(f"☁️ Uploaded: {s3_key}")

    try:
        shutil.rmtree(local_dir)
        print(f"🧹 Deleted local folder: {local_dir}")
    except Exception as e:
        print(f"⚠️ Could not delete {local_dir}: {e}")
