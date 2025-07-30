# Video-Streaming-Thumbnail

# 📺 Media Center - Video/Image Upload with HLS, Thumbnail & pHash

A Django-based media backend that supports:
- ✅ Uploading videos and images
- 🎞️ Automatic HLS playlist generation (for video streaming)
- 🖼️ Thumbnail creation
- 🔐 Perceptual Hashing (pHash) for media similarity detection
- 🧵 Asynchronous processing via Celery & Redis

---

## 🧰 Tech Stack

- **Backend:** Django + Django Rest Framework
- **Task Queue:** Celery + Redis
- **Media Tools:** ffmpeg, imagehash (pHash)
- **Storage:** Local or AWS S3 compatible
- **Frontend:** (Not included here)

---

## 🚀 Features

- Upload videos or images via API
- Automatically:
  - Generate HLS playlist for videos
  - Create thumbnails
  - Compute pHash for similarity detection
- Async processing of media using Celery workers
- Configurable media host URL for public access

---

## 📦 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/media-center.git
cd media-center
```

### 2. Create Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Apply Migrations and Runserver
```
python manage.py migrate
python manage.py runserver
```

### 🧪 API Usage
You can use Postman or Browser to test the API.

#### Upload Video/Image

POST http://localhost:8008/api/v1/media/
Content-Type: multipart/form-data

Form Data:
  - type: <photo/video>
  - file: <photo/video file>

Response will include thumbnail, HLS URL (if video), and pHash.

Note: This works successfully in the local environment. For the production environment, production setup and credentials will be needed.


















