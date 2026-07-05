# 🎬 Terabox Direct Link Extractor API

**Simple API - Pass link → Get download + stream links!**

---

## ⚡ Quick Start (30 seconds)

### 1. Install
```bash
pip install fastapi uvicorn requests
```

### 2. Run
```bash
python terabox_direct_api.py
```

### 3. Use
```bash
# In browser or curl
http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
```

### 4. Get Response
```json
{
  "status": "success",
  "service": "1024terabox.com",
  "share_id": "10LHRppa8fMO6NJhuiRMkWA",
  "download_link": "https://...",
  "stream_link": "https://..."
}
```

✅ **Done!**

---

## 📡 API Endpoints

### 1. Extract All Links
```
GET /api?url=TERABOX_URL
```

**Response:**
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

---

### 2. Get Download Link Only
```
GET /download?url=TERABOX_URL
```

**Response:**
```json
{
  "status": "success",
  "download_link": "https://...",
  "message": "Ready to download"
}
```

---

### 3. Get Stream Link Only
```
GET /stream?url=TERABOX_URL
```

**Response:**
```json
{
  "status": "success",
  "stream_link": "https://...",
  "message": "Ready to stream"
}
```

---

### 4. API Info
```
GET /info
```

Returns API documentation and features.

---

## 🎯 Usage Examples

### Browser
```
http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
```

### cURL
```bash
curl "http://localhost:8000/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA"
```

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
const teraboxUrl = "https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA";

fetch(`http://localhost:8000/api?url=${encodeURIComponent(teraboxUrl)}`)
  .then(res => res.json())
  .then(data => {
    console.log("Download:", data.download_link);
    console.log("Stream:", data.stream_link);
  });
```

---

## 🌐 Supported Services

Ye sab terabox-like services support karti hai:
- ✅ terabox.com
- ✅ 1024terabox.com
- ✅ terasharefile.com
- ✅ teraboxshare.com
- ✅ And other terabox variants

---

## 📊 Features

- 🚀 **Fast** - Direct link extraction
- 💾 **Caching** - Results cached for 1 hour
- 🔄 **Redirect Following** - Auto-follows redirects
- 🔐 **Password Support** - Handles password-protected links
- ⏱️ **Timeout** - 15 seconds per request
- 📱 **Simple** - Easy to use API

---

## 📚 Interactive Docs

Browser mein kholo:
```
http://localhost:8000/docs
```

Sab endpoints test kar sakte ho directly!

---

## 🔧 Advanced Usage

### With Headers
```python
import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

response = requests.get(
    "http://localhost:8000/api",
    params={"url": "https://1024terabox.com/s/..."},
    headers=headers
)
```

### Error Handling
```python
try:
    response = requests.get("http://localhost:8000/api", 
                           params={"url": url})
    data = response.json()
    
    if data['status'] == 'success':
        print(f"Download: {data['download_link']}")
    else:
        print(f"Error: {data['message']}")
except Exception as e:
    print(f"API Error: {e}")
```

---

## 🎬 Download & Stream

### Download File
```bash
# Using the download link from API
wget "DOWNLOAD_LINK"

# Or with curl
curl -O "DOWNLOAD_LINK"
```

### Stream Video
```bash
# Play with VLC or any video player
vlc "STREAM_LINK"

# Or with ffmpeg
ffmpeg -i "STREAM_LINK" output.mp4
```

---

## 🚀 Deployment

### Local
```bash
python terabox_direct_api.py
```

### Docker
```bash
docker build -t terabox-api .
docker run -p 8000:8000 terabox-api
```

### Vercel
```bash
vercel deploy
```

### Heroku
```bash
heroku create terabox-api
git push heroku main
```

---

## ⚙️ Configuration

### Change Port
```bash
# Command line
python terabox_direct_api.py --port 9000

# Or modify code:
uvicorn.run(app, host="0.0.0.0", port=9000)
```

### Custom Headers
Edit `terabox_direct_api.py`:
```python
self.session.headers.update({
    'User-Agent': 'Your custom user agent'
})
```

### Timeout
Edit `terabox_direct_api.py`:
```python
# Default: 15 seconds
response = self.session.head(url, timeout=30)  # Increase to 30
```

---

## 🐛 Troubleshooting

### "Connection refused"
```bash
Make sure API is running:
python terabox_direct_api.py
```

### "Link not found"
```
Some links may not work if:
- Link is expired
- Link requires authentication
- Service changed their structure

Try with browser first to verify link works
```

### "Timeout error"
```
Link may be slow to load:
- Try again after few seconds
- Or increase timeout in code
```

---

## 📊 Performance

- ✅ Instant response for cached links
- ✅ 2-5 seconds for new links
- ✅ Handles multiple concurrent requests
- ✅ Auto-caches results for 1 hour

---

## 🔒 Security Notes

- ✅ No login required
- ✅ No file storage on server
- ✅ Links are temporary
- ✅ No data collection
- ✅ Direct link passthrough

---

## 📞 API Status

Check API status:
```bash
curl http://localhost:8000/info
```

Response:
```json
{
  "status": "online",
  "version": "1.0",
  "uptime": "..."
}
```

---

## 🎯 Use Cases

1. **Download Manager**
   ```
   Build UI → Pass link → Get download link
   ```

2. **Video Player**
   ```
   Get stream link → Play in VLC/HTML5 player
   ```

3. **Batch Download**
   ```
   Loop through links → Get all links → Download all
   ```

4. **Telegram Bot**
   ```
   User sends link → API extracts → Return links
   ```

5. **Web Scraper**
   ```
   Scrape terabox links → Extract → Download
   ```

---

## 🚀 Production Tips

1. **Enable HTTPS**
   ```
   Use nginx/Apache reverse proxy
   ```

2. **Add Authentication**
   ```python
   @app.get("/api")
   async def extract_links(url: str, api_key: str = Query(...)):
       if api_key != "your_secret_key":
           raise HTTPException(status_code=401)
   ```

3. **Rate Limiting**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @app.get("/api")
   @limiter.limit("10/minute")
   async def extract_links(...):
   ```

4. **Logging**
   ```python
   logger.info(f"Extracted link for: {url}")
   ```

5. **Monitoring**
   ```bash
   docker stats terabox-api
   ```

---

## 📦 Installation

### Requirements
```bash
pip install fastapi==0.104.1
pip install uvicorn==0.24.0
pip install requests==2.31.0
```

### Or use requirements.txt
```bash
pip install -r requirements.txt
```

---

## 📄 Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success ✅ |
| 400 | Bad request (invalid URL) ❌ |
| 500 | Server error ⚠️ |
| 429 | Rate limited ⏱️ |

---

## 🎉 You're Ready!

```
✅ API installed
✅ API running
✅ Links extracted
✅ Ready to use!
```

**Start using it now! 🚀**

---

## 📚 Related Files

- `terabox_direct_api.py` - Main API code
- `requirements.txt` - Dependencies
- `Dockerfile` - Docker setup
- `docker-compose.yml` - Docker Compose

---

**Happy linking! 🎬🔗**
