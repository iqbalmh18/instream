# InStream Instagram Live Streaming Manager

InStream is a Flask-based web application for managing Instagram live streaming sessions. It provides a comprehensive dashboard and interactive control panel for uploading, selecting, and managing videos, as well as controlling live broadcasts with real-time analytics and engagement features.

## Overview

This tool is designed for content creators who require full control over their Instagram Live broadcasts from a mobile-friendly interface. The application offers secure authentication, video management, live stream control, and real-time monitoring capabilities.

## Key Features

**Authentication & Security**
- Secure cookie-based authentication for Instagram sessions
- Session validation and management
- Secure storage of streaming credentials

**Video Management**
- Upload videos with drag and drop support
- Download videos from Instagram URLs
- Organize and manage video library
- Delete or clear videos from library

**Live Stream Control**
- Start and stop streams with custom titles
- Set custom stream duration with auto-stop capability
- Real-time stream management and monitoring

**Real-Time Analytics & Monitoring**
- Live viewer count tracking
- Comment monitoring and management
- Broadcast duration tracking
- Live comment feed with posting capability

**Dashboard**
- Analytics overview
- Stream status indicators
- Quick action controls
- Application health monitoring
- Dark mode support

## Requirements

- Python 3.8 or higher
- Flask web framework
- Virtual environment support

## Installation

### Step 1: Clone Repository

```bash
git clone https://github.com/iqbalmh18/instream.git
cd instream
```

### Step 2: Set Up Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

On Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
export FLASK_HOST=0.0.0.0
export FLASK_PORT=5000
export FLASK_DEBUG=true
```

On Windows (Command Prompt):
```bash
set FLASK_HOST=0.0.0.0
set FLASK_PORT=5000
set FLASK_DEBUG=true
```

## Configuration

All application configuration is managed through the `config.py` file using the `Config` class. Key settings include:

**Application Settings**
- `LOG_FOLDER`: Directory location for application logs
- `LOG_LEVEL`: Logging verbosity level
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 1GB)

**Streaming Settings**
- Instagram API configuration
- Streaming protocol settings
- Custom implementation via `utils.LiveStreamManager`

For detailed configuration options, refer to the `config.py` file in the project root.

## Usage

### Starting the Application

```bash
python3 app.py
```

Access the application at `http://localhost:5000`

### Setting Up Instagram Cookies

1. Navigate to the Home page
2. Enter your Instagram session cookies in the provided field
3. Click Save and test to validate cookies

### Preparing Your Video

Select one of the following methods:
- Upload a video file from your computer
- Download a video from Instagram using its URL
- Select an existing video from your library

### Starting a Stream

1. Enter a custom title for your stream
2. Set the stream duration
3. Click Start to begin streaming
4. Monitor live statistics in real-time

### Managing the Stream

- Post comments to engage with viewers
- Stop the stream manually at any time
- Allow automatic stop after the specified duration
- Monitor viewer count and engagement metrics

## API Endpoints

### Stream Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Home page and stream control interface |
| GET | `/dashboard` | Dashboard with analytics and overview |
| POST | `/api/start` | Start a new live stream |
| POST | `/api/stop` | Stop the current live stream |
| GET | `/api/info` | Retrieve current stream information |
| GET | `/api/status` | Get current streaming status |

### Video Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/upload` | Upload video file |
| POST | `/api/download` | Download video from Instagram URL |
| DELETE | `/api/delete/<video_id>` | Delete specific video |
| GET | `/videos` | Fetch complete video library |

### Session Management

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/validate-cookies` | Validate Instagram session cookies |

### Engagement

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/comment` | Post comment to live stream |

### Monitoring

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/health` | Application health status |

## Troubleshooting

**Upload Fails with File Size Error**

The upload was rejected due to file size limits. To resolve this:
1. Increase `MAX_CONTENT_LENGTH` value in `config.py`
2. Ensure your video file meets the size requirements
3. Try uploading again

**Invalid Cookies Error When Saving**

Ensure your Instagram cookies are correctly extracted:
1. Open Instagram in your browser
2. Access Developer Tools (F12 or right-click > Inspect)
3. Navigate to Application tab
4. Select Cookies
5. Copy the session cookie values
6. Paste them into the application

**Dashboard Shows Offline Status**

If the dashboard indicates offline status despite active streaming:
1. Check the browser console for error messages
2. Verify the `/api/info` endpoint response
3. Confirm backend server is running
4. Review application logs in the LOG_FOLDER directory

**Video Upload Timeout**

If video uploads are timing out:
1. Check your network connection
2. Try uploading a smaller file first
3. Verify the Flask server is responsive
4. Check available disk space

## Project Structure

```
instream/
├── app.py                 # Main Flask application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── utils.py               # Utility functions and LiveStreamManager
├── templates/             # HTML templates
├── static/                # CSS and JavaScript files
├── uploads/               # Video upload directory
└── logs/                  # Application logs
```

## Development

### Running in Debug Mode

```bash
export FLASK_DEBUG=true
python3 app.py
```

### Viewing Logs

Application logs are stored in the configured `LOG_FOLDER`. Check these logs for detailed error messages and system information.

### Testing Endpoints

Use tools like curl or Postman to test API endpoints:

```bash
curl -X POST http://localhost:5000/api/validate-cookies \
  -H "Content-Type: application/json" \
  -d '{"cookies": "your_cookie_string"}'
```

## Contributing

To contribute to this project:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

This project is licensed under the MIT License. See the LICENSE file for complete license information.

## Support

For issues, questions, or feature requests, please open an issue on the GitHub repository or contact the development team.

## Disclaimer

This tool is intended for personal use and educational purposes. Ensure compliance with Instagram's Terms of Service and community guidelines when using this application.