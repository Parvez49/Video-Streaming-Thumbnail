import os
import subprocess
from io import BytesIO

from PIL import Image
from django.core.files.base import ContentFile
from imagehash import phash

from .models import Media


def generate_thumbnail(file_field, media_type, size=(640, 640), time_frame=1):
    """
    Generates a high-quality thumbnail and perceptual hash (pHash) from an image or video.

    Args:
        file_field: Django FileField (image/video).
        media_type: Media.Type.PHOTO or Media.Type.VIDEO.
        size: Max dimensions for thumbnail.
        time_frame: Timestamp (in seconds) for extracting frame from video.

    Returns:
        (ContentFile: JPEG thumbnail, str: perceptual hash)
    """
    try:
        if media_type == Media.Type.PHOTO:
            image = Image.open(file_field).convert('RGB')
            image.thumbnail(size, Image.Resampling.LANCZOS)
            phash_value = str(phash(image))

        elif media_type == Media.Type.VIDEO:
            input_path = (
                file_field.temporary_file_path()
                if hasattr(file_field, 'temporary_file_path')
                else save_to_temp_file(file_field)
            )
            output_path = f'{input_path}_thumbnail.jpg'

            subprocess.run(
                [
                    "ffmpeg",
                    "-ss", str(time_frame),     # Seek early for faster processing
                    "-i", input_path,
                    "-frames:v", "1",           # Only 1 frame
                    "-q:v", "1",                # Highest JPEG quality
                    "-vf", "scale=-1:720",      # Optional: Limit height to 720px while keeping aspect ratio
                    output_path,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            image = Image.open(output_path).convert('RGB')
            image.thumbnail(size, Image.Resampling.LANCZOS)
            phash_value = str(phash(image))

            # Cleanup
            if os.path.exists(output_path):
                os.remove(output_path)
            if os.path.exists(input_path) and not hasattr(file_field, 'temporary_file_path'):
                os.remove(input_path)

        else:
            raise ValueError('Unsupported media type')

        # Save thumbnail to BytesIO
        thumb_io = BytesIO()
        image.save(thumb_io, format='JPEG')
        thumbnail_name = f'thumb_{os.path.splitext(os.path.basename(file_field.name))[0]}.jpg'
        thumbnail_file = ContentFile(thumb_io.getvalue(), name=thumbnail_name)

        return thumbnail_file, phash_value

    except Exception as e:
        raise ValueError(f'Error generating thumbnail/phash: {e}')


def save_to_temp_file(file_field):
    """Save in-memory file to a temporary file."""
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False)
    temp_file.write(file_field.read())
    temp_file.close()
    return temp_file.name
