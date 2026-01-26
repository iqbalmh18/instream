# InStream
Instagram Live Streaming Manager

![light](https://i.postimg.cc/MzjkT3Dy/20250812-153206.png)
![dark](https://i.postimg.cc/8182rdKx/20250812-153359.png)

## Introduction
InStream is a Flask-based web application for managing Instagram live streaming sessions.  
It provides a **modern dashboard** and **interactive control panel** to:
- Upload, select, and manage videos
- Looping video based on duration
- Start and stop live streams
- View live analytics (viewers, comments, duration)
- Post comments in real-time
- Monitor application health

This tool is designed for content creators who want **full control over their Instagram Live broadcasts** from a mobile-friendly interface.

---

## Table of Contents
- [Features](#features)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Endpoints](#endpoints)
- [Troubleshooting](#troubleshooting)
- [License](#license)

---

## Features
- **Secure Cookie Authentication**: Save and validate Instagram session cookies.
- **Video Management**:
  - Upload videos (drag & drop support)
  - Download Instagram videos via URL
  - Select from an uploaded video library
  - Delete or clear all videos
- **Live Stream Control**:
  - Start/stop streams with custom title and duration
  - Auto-stop after a specified time
- **Real-time Monitoring**:
  - View viewer count, comment count, and broadcast duration
  - Live comment feed with posting capability
- **Dashboard Analytics**:
  - Total uploaded videos
  - Current stream status
  - Quick actions and health checks
- **Dark Mode** toggle

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/iqbalmh18/instream.git
cd instream
```

### 2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Set environment variables
```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_DEBUG=true
```

---

## Configuration

All configuration is handled in `config.py` (via `Config` class), including:
- `LOG_FOLDER` location for application logs
- `LOG_LEVEL` logging verbosity
- `MAX_CONTENT_LENGTH` max upload size (default: 1GB)
- Instagram API and streaming settings (custom implementation in `utils.LiveStreamManager`)

---

## Usage

### 1. Start the application
```bash
python3 app.py
```
Access the app in your browser at:
```
http://localhost:5000
```

### 2. Set up Instagram cookies
- Navigate to the **Home** page
- Paste your Instagram session cookies into the cookie input
- Save & test cookies

### 3. Prepare your video
- Upload from your PC
- Download from Instagram by URL
- Select from your library

### 4. Start streaming
- Set your stream title and duration
- Click **Start** and monitor stats in real-time

### 5. Manage the stream
- Post comments
- Stop stream manually or let it auto-stop after duration

---

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Home page (stream control) |
| `GET`  | `/dashboard` | Dashboard & analytics |
| `POST` | `/api/upload` | Upload video file |
| `POST` | `/api/download` | Download Instagram video |
| `DELETE` | `/api/delete/<filename>` | Delete a video |
| `POST` | `/api/validate-cookies` | Validate Instagram cookies |
| `POST` | `/api/start` | Start live stream |
| `POST` | `/api/stop` | Stop live stream |
| `GET`  | `/api/info` | Get current stream info |
| `POST` | `/api/comment` | Post a comment to the stream |
| `GET`  | `/videos` | Fetch video library list |
| `GET`  | `/health` | Application health check |
| `GET`  | `/status` | Current stream status |

---

## Troubleshooting

**Issue:** Upload fails with "File too large"  
**Solution:** Increase `MAX_CONTENT_LENGTH` in `config.py`.

**Issue:** "Invalid cookies" when saving session  
**Solution:** Make sure cookies are copied correctly from browser DevTools â†’ Application â†’ Cookies.

**Issue:** Dashboard shows "Offline" despite streaming  
**Solution:** Check `/api/info` response in browser console for backend errors.

---

## License
This project is licensed under the MIT License.  
See the `LICENSE` file for details.