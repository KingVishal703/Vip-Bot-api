# 🎬 Terabox Complete API - Setup & Usage Guide

**Pass terabox link → Get download + stream links instantly!**

---

## 📦 Package Contents

```
terabox-complete-api/
├── terabox_direct_api.py      ← Main API code
├── requirements.txt            ← Dependencies
├── Dockerfile                  ← Docker configuration
├── docker-compose.yml          ← Docker Compose setup
├── .dockerignore               ← Docker ignore patterns
├── README.md                   ← Quick guide
└── SETUP.md                    ← This file
```

---

## ⚡ Super Quick Start (1 minute)

### Option 1: Python Direct

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run API
python terabox_direct_api.py

# 3. Open browser
http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
```

✅ **Done!**

---

### Option 2: Docker

```bash
# 1. Build
docker build -t terabox-api .

# 2. Run
docker run -p 8000:8000 terabox-api

# 3. Test
http://localhost:8000/api?url=YOUR_TERABOX_LINK
```

✅ **Done!**

---

### Option 3: Docker Compose

```bash
# 1. Just run
docker-compose up -d

# 2. Access
http://localhost:8000/api?url=YOUR_TERABOX_LINK

# 3. Stop
docker-compose down
```

✅ **Done!**

---

## 🎯 API Usage

### Get All Links
```
GET /api?url=TERABOX_LINK
```

**Example:**
```
http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
```

**Response:**
```json
{
  "status": "success",
  "service": "1024terabox.com",
  "share_id": "10LHRppa8fMO6NJhuiRMkWA",
  "download_link": "https://...",
  "stream_link": "https://..."
}
```

---

### Get Download Link Only
```
GET /download?url=TERABOX_LINK
```

---

### Get Stream Link Only
```
GET /stream?url=TERABOX_LINK
```

---

## 💻 Code Examples

### Python
```python
import requests

url = "https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA"

response = requests.get(
    "http://localhost:8000/api",
    params={"url": url}
)

data = response.json()
print(f"Download: {data['download_link']}")
print(f"Stream: {data['stream_link']}")
```

### JavaScript
```javascript
const url = "https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA";

fetch(`http://localhost:8000/api?url=${encodeURIComponent(url)}`)
  .then(res => res.json())
  .then(data => {
    console.log("Download:", data.download_link);
    console.log("Stream:", data.stream_link);
  });
```

### cURL
```bash
curl "http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA"
```

---

## 🔧 Installation Details

### Requirements
- Python 3.7+
- pip or conda
- Docker (optional, for containerization)

### Install Python Dependencies
```bash
pip install -r requirements.txt
```

**What gets installed:**
- fastapi==0.104.1
- uvicorn==0.24.0
- requests==2.31.0

### Verify Installation
```bash
python -c "import fastapi; print('✅ FastAPI installed')"
python -c "import uvicorn; print('✅ Uvicorn installed')"
python -c "import requests; print('✅ Requests installed')"
```

---

## 🚀 Running the API

### Local Development
```bash
python terabox_direct_api.py
```

Output:
```
======================================================================
🎬 TERABOX DIRECT LINK EXTRACTOR API
======================================================================
📡 API Running: http://localhost:8000
📚 Documentation: http://localhost:8000/docs
🧪 Try: http://localhost:8000/api?url=YOUR_TERABOX_LINK
======================================================================
```

### With Custom Port
```bash
# Modify in code or use environment variable
UVICORN_PORT=9000 python terabox_direct_api.py
```

### Background Execution
```bash
# Linux/Mac
nohup python terabox_direct_api.py > api.log 2>&1 &

# Windows
start python terabox_direct_api.py
```

---

## 🐳 Docker Usage

### Build Image
```bash
docker build -t terabox-api:latest .
```

### Run Container
```bash
docker run -d \
  --name terabox-api \
  -p 8000:8000 \
  terabox-api:latest
```

### View Logs
```bash
docker logs -f terabox-api
```

### Stop Container
```bash
docker stop terabox-api
```

### Remove Container
```bash
docker rm terabox-api
```

---

## 🐋 Docker Compose Usage

### Start Services
```bash
docker-compose up -d
```

### View Logs
```bash
docker-compose logs -f
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

---

## 🌐 Access API

### Browser
```
http://localhost:8000/docs
```

Interactive API documentation - try endpoints directly!

### Command Line
```bash
curl "http://localhost:8000/api?url=YOUR_URL"
```

### Python
```python
import requests
response = requests.get("http://localhost:8000/api", 
                       params={"url": "YOUR_URL"})
print(response.json())
```

---

## 📊 API Response Format

### Success Response
```json
{
  "status": "success",
  "service": "1024terabox.com",
  "share_id": "10LHRppa8fMO6NJhuiRMkWA",
  "original_url": "https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
  "download_link": "https://...",
  "stream_link": "https://...",
  "message": "Links extracted successfully"
}
```

### Error Response
```json
{
  "status": "error",
  "message": "URL must be a terabox link",
  "example": "GET /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA"
}
```

---

## 🎯 Real-World Examples

### 1. Download a File
```bash
# Get download link from API
DOWNLOAD_LINK=$(curl "http://localhost:8000/api?url=YOUR_LINK" | grep -o '"download_link":"[^"]*' | cut -d'"' -f4)

# Download file
wget "$DOWNLOAD_LINK"
```

### 2. Stream Video in VLC
```bash
# Get stream link from API
STREAM_LINK=$(curl "http://localhost:8000/api?url=YOUR_LINK" | grep -o '"stream_link":"[^"]*' | cut -d'"' -f4)

# Open in VLC
vlc "$STREAM_LINK"
```

### 3. Batch Download
```bash
# Create links.txt with terabox URLs
for link in $(cat links.txt); do
  DOWNLOAD_LINK=$(curl "http://localhost:8000/api?url=$link" | grep -o '"download_link":"[^"]*' | cut -d'"' -f4)
  wget "$DOWNLOAD_LINK"
done
```

---

## 🐛 Troubleshooting

### API not starting
```
Error: Address already in use port 8000

Solution: Kill existing process or change port
lsof -i :8000
kill -9 <PID>
```

### Connection refused
```
Error: Connection refused on localhost:8000

Solution: Make sure API is running
python terabox_direct_api.py
```

### Module not found
```
Error: ModuleNotFoundError: No module named 'fastapi'

Solution: Install dependencies
pip install -r requirements.txt
```

### Docker build failed
```
Solution: Build without cache
docker build --no-cache -t terabox-api .
```

### Links not extracted
```
Possible reasons:
1. Link expired
2. Link requires authentication
3. Service structure changed

Solution: Test with browser first to verify link works
```

---

## 📈 Performance & Features

### Features
- ✅ Direct link extraction
- ✅ Multi-service support (terabox, 1024terabox, terasharefile, etc.)
- ✅ Automatic redirect following
- ✅ Result caching (1 hour)
- ✅ Password-protected link support
- ✅ Fast response (2-5 seconds)

### Performance
- Single request: ~2-5 seconds
- Cached request: <100ms
- Timeout: 15 seconds
- Concurrent requests: Unlimited

---

## 🔒 Security & Best Practices

### Security
- ✅ No login required (stateless)
- ✅ No file storage
- ✅ No data collection
- ✅ Direct link passthrough
- ✅ HTTPS ready

### Best Practices
1. Use behind reverse proxy (nginx/Apache) for production
2. Add API key authentication for private use
3. Implement rate limiting
4. Enable HTTPS/TLS
5. Monitor API logs regularly
6. Keep dependencies updated

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Swagger UI**: http://localhost:8000/swagger
- **ReDoc**: http://localhost:8000/redoc

---

## 🚀 Deployment Options

### Local
```bash
python terabox_direct_api.py
```
Best for: Development, testing

### Docker
```bash
docker-compose up -d
```
Best for: Self-hosted servers

### Vercel
Connect GitHub repo to Vercel
Best for: Free cloud hosting

### AWS/GCP/Azure
Deploy Docker image to cloud
Best for: Scalable production

---

## 📞 Support

### Check API Status
```bash
curl http://localhost:8000/info
```

### View Logs
```bash
tail -f api.log
```

### Debug Mode
Edit code and add:
```python
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎉 Quick Checklist

- [ ] Python installed (3.7+)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] API running (`python terabox_direct_api.py`)
- [ ] Browser accessible (http://localhost:8000/docs)
- [ ] Tested with terabox link
- [ ] Got download + stream links

**All done!** You're ready to use the API! 🚀

---

**Need help?** Check the logs or README.md!

**Happy linking! 🎬**
