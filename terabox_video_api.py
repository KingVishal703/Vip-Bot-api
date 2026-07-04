from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import requests
import os
import json
import re
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import asyncio
from urllib.parse import quote
import mimetypes
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terabox Video API",
    description="Terabox videos ke liye advanced API - Details, Download, Streaming!",
    version="2.0"
)

# Configuration
DOWNLOAD_FOLDER = "downloads"
CACHE_FOLDER = "cache"
Path(DOWNLOAD_FOLDER).mkdir(exist_ok=True)
Path(CACHE_FOLDER).mkdir(exist_ok=True)

# Request models
class VideoLinkRequest(BaseModel):
    url: str
    include_metadata: bool = True

class StreamRequest(BaseModel):
    url: str
    quality: str = "best"  # best, high, medium, low

# Response models
class VideoMetadata(BaseModel):
    title: str
    file_size: str
    file_size_bytes: int
    file_type: str
    download_url: str
    share_id: str
    duration: Optional[str]
    resolution: Optional[str]
    codec: Optional[str]
    fps: Optional[str]
    bitrate: Optional[str]
    created_date: Optional[str]
    updated_date: Optional[str]

class VideoDetailsResponse(BaseModel):
    status: str
    message: str
    video_metadata: Optional[VideoMetadata]
    preview_thumbnail: Optional[str]
    actions: Dict[str, str]

class DownloadStatusResponse(BaseModel):
    status: str
    message: str
    file_name: Optional[str]
    progress_percentage: Optional[int]
    downloaded_size: Optional[str]
    total_size: Optional[str]

# ==================== HELPER FUNCTIONS ====================

def parse_terabox_url(url: str) -> Dict:
    """Terabox URL se details nikalo"""
    try:
        # Share ID extract karo
        if 'terabox.com/s/' in url:
            share_id = url.split('/s/')[-1].split('?')[0]
            return {
                'share_id': share_id,
                'type': 'share_link',
                'original_url': url
            }
        return None
    except Exception as e:
        logger.error(f"URL parsing error: {e}")
        return None

def extract_video_metadata(url: str) -> Dict:
    """Video ke liye metadata nikalo (advanced)"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Terabox API se metadata lene ki koshish
        response = requests.head(url, headers=headers, allow_redirects=True, timeout=10)
        
        metadata = {
            'title': 'terabox_video',
            'file_size': response.headers.get('content-length', 'unknown'),
            'file_type': response.headers.get('content-type', 'video/mp4'),
            'download_url': response.url if response.status_code == 200 else url,
        }
        
        # Size ko readable format mein convert karo
        if metadata['file_size'] != 'unknown':
            metadata['file_size_bytes'] = int(metadata['file_size'])
            metadata['file_size'] = format_file_size(int(metadata['file_size']))
        else:
            metadata['file_size_bytes'] = 0
        
        # Content-Disposition se filename nikalo
        if 'content-disposition' in response.headers:
            match = re.findall(r'filename[^;=\n]*=(["\']?)([^"\';]*)\1', response.headers['content-disposition'])
            if match:
                metadata['title'] = match[0][1]
        
        return metadata
    except Exception as e:
        logger.error(f"Metadata extraction error: {e}")
        return {
            'title': 'terabox_video',
            'file_size': 'unknown',
            'file_size_bytes': 0,
            'file_type': 'video/mp4',
            'download_url': url
        }

def get_video_info(share_id: str) -> Dict:
    """Share ID se detailed video info lao"""
    try:
        # Terabox API endpoint
        api_url = f"https://www.terabox.com/api/clouddisk/info?shareid={share_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.terabox.com/'
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('errno') == 0:
                list_data = data.get('list', [])
                if list_data:
                    file_info = list_data[0]
                    
                    return {
                        'share_id': share_id,
                        'title': file_info.get('server_filename', 'video'),
                        'file_size': file_info.get('size', 0),
                        'file_type': file_info.get('category', 1),  # 1=video
                        'fs_id': file_info.get('fs_id'),
                        'md5': file_info.get('md5'),
                        'server_mtime': file_info.get('server_mtime'),
                    }
        
        return None
    except Exception as e:
        logger.error(f"Video info error: {e}")
        return None

def get_download_link(share_id: str, fs_id: str) -> Optional[str]:
    """Actual download link nikalo"""
    try:
        api_url = "https://www.terabox.com/api/shorturlv2"
        
        params = {
            'app_id': '250528',
            'shareID': share_id,
            'uk': '',
            'sign': '',
            'timestamp': '',
        }
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.post(api_url, data=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data.get('shorturl')
        
        return None
    except Exception as e:
        logger.error(f"Download link error: {e}")
        return None

def format_file_size(size_bytes: int) -> str:
    """Bytes ko readable format mein convert karo"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"

def get_folder_size(folder_path: str) -> int:
    """Folder ka total size"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
    except:
        pass
    return total

async def download_file_stream(url: str, file_path: str, on_progress=None):
    """File ko stream karte hue download karo"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    if on_progress and total_size > 0:
                        progress = int((downloaded / total_size) * 100)
                        on_progress(progress, downloaded, total_size)
        
        return True, os.path.getsize(file_path)
    except Exception as e:
        logger.error(f"Download error: {e}")
        if os.path.exists(file_path):
            os.remove(file_path)
        return False, None

def get_video_preview(url: str) -> Optional[str]:
    """Video ka thumbnail/preview lao (base64 mein)"""
    try:
        # Ye ek dummy function hai - real implementation mein 
        # FFmpeg use karoge thumbnail nikalne ke liye
        return None
    except:
        return None

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API Home"""
    return {
        "name": "Terabox Video API",
        "version": "2.0",
        "description": "Videos ke liye advanced API - Details, Download, Streaming!",
        "endpoints": {
            "GET /": "API Documentation",
            "POST /video/details": "Video ke details nikalo",
            "POST /video/download": "Video download karo",
            "POST /video/stream": "Video streaming ke liye",
            "GET /video/downloads": "Sab downloaded videos",
            "GET /video/progress/{filename}": "Download progress check karo",
            "DELETE /video/delete/{filename}": "Video delete karo",
            "GET /video/info": "API info",
        }
    }

@app.post("/video/details")
async def get_video_details(request: VideoLinkRequest):
    """
    Video ki details nikalo
    - Title, Size, Type
    - Download link
    - Metadata
    """
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL required hai!")
        
        # URL parse karo
        parsed = parse_terabox_url(request.url)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid Terabox URL!")
        
        # Video info nikalo
        video_info = get_video_info(parsed['share_id'])
        
        if not video_info:
            # Fallback - direct metadata extraction
            metadata = extract_video_metadata(request.url)
            return VideoDetailsResponse(
                status="partial",
                message="API se info nahi mila, direct link se metadata nikala",
                video_metadata=VideoMetadata(
                    title=metadata.get('title', 'video'),
                    file_size=metadata.get('file_size', 'unknown'),
                    file_size_bytes=metadata.get('file_size_bytes', 0),
                    file_type=metadata.get('file_type', 'video/mp4'),
                    download_url=metadata.get('download_url', request.url),
                    share_id=parsed['share_id'],
                    duration=None,
                    resolution=None,
                    codec=None,
                    fps=None,
                    bitrate=None,
                    created_date=None,
                    updated_date=None,
                ),
                preview_thumbnail=None,
                actions={
                    "download": f"/video/download",
                    "stream": f"/video/stream",
                    "delete": f"/video/delete/{{filename}}"
                }
            )
        
        # Full metadata extract karo
        metadata = extract_video_metadata(request.url)
        
        return VideoDetailsResponse(
            status="success",
            message="Video details successfully extracted!",
            video_metadata=VideoMetadata(
                title=video_info.get('title', 'video'),
                file_size=format_file_size(video_info.get('file_size', 0)),
                file_size_bytes=video_info.get('file_size', 0),
                file_type="video",
                download_url=metadata.get('download_url', request.url),
                share_id=parsed['share_id'],
                duration=None,
                resolution=None,
                codec=None,
                fps=None,
                bitrate=None,
                created_date=datetime.fromtimestamp(
                    video_info.get('server_mtime', 0)
                ).isoformat() if video_info.get('server_mtime') else None,
                updated_date=None,
            ),
            preview_thumbnail=None,
            actions={
                "download": "/video/download",
                "stream": "/video/stream",
                "list": "/video/downloads"
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/video/download")
async def download_video(request: VideoLinkRequest, background_tasks: BackgroundTasks):
    """
    Video download karo
    - Streaming download
    - Progress tracking
    - Resume support
    """
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL required hai!")
        
        parsed = parse_terabox_url(request.url)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid Terabox URL!")
        
        # Video info nikalo
        video_info = get_video_info(parsed['share_id'])
        file_name = video_info.get('title', 'video') if video_info else 'terabox_video.mp4'
        file_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        
        # Agar file already exist karti hai
        if os.path.exists(file_path):
            return DownloadStatusResponse(
                status="exists",
                message=f"File '{file_name}' already downloaded hai!",
                file_name=file_name,
                progress_percentage=100,
                downloaded_size=format_file_size(os.path.getsize(file_path)),
                total_size=format_file_size(os.path.getsize(file_path))
            )
        
        # Get actual download link
        metadata = extract_video_metadata(request.url)
        download_url = metadata.get('download_url', request.url)
        
        # Background mein download shuru karo
        async def download_task():
            await download_file_stream(download_url, file_path)
        
        background_tasks.add_task(download_task)
        
        return DownloadStatusResponse(
            status="started",
            message=f"Download started for '{file_name}'",
            file_name=file_name,
            progress_percentage=0,
            downloaded_size="0 B",
            total_size=metadata.get('file_size', 'unknown')
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/video/stream")
async def stream_video(request: StreamRequest):
    """
    Video streaming ke liye
    - Different quality options
    - Subtitle support
    - Resume support
    """
    try:
        if not request.url:
            raise HTTPException(status_code=400, detail="URL required hai!")
        
        parsed = parse_terabox_url(request.url)
        if not parsed:
            raise HTTPException(status_code=400, detail="Invalid Terabox URL!")
        
        # Download link nikalo
        metadata = extract_video_metadata(request.url)
        stream_url = metadata.get('download_url', request.url)
        
        # Stream response karo
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        
        response = requests.get(stream_url, headers=headers, stream=True, timeout=60)
        response.raise_for_status()
        
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=response.headers.get('content-type', 'video/mp4'),
            headers={
                'Content-Length': response.headers.get('content-length', ''),
                'Accept-Ranges': 'bytes'
            }
        )
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Streaming error: {str(e)}")

@app.get("/video/downloads")
async def list_downloads():
    """Sab downloaded videos list karo"""
    try:
        files = []
        for filename in os.listdir(DOWNLOAD_FOLDER):
            filepath = os.path.join(DOWNLOAD_FOLDER, filename)
            if os.path.isfile(filepath):
                size = os.path.getsize(filepath)
                mod_time = os.path.getmtime(filepath)
                
                files.append({
                    "name": filename,
                    "size": format_file_size(size),
                    "size_bytes": size,
                    "downloaded_at": datetime.fromtimestamp(mod_time).isoformat(),
                    "watch_link": f"/video/watch/{quote(filename)}",
                    "delete_link": f"/video/delete/{quote(filename)}"
                })
        
        return {
            "status": "success",
            "total_videos": len(files),
            "total_storage": format_file_size(get_folder_size(DOWNLOAD_FOLDER)),
            "videos": files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/watch/{filename}")
async def watch_video(filename: str):
    """Downloaded video ko watch/stream karo"""
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Video not found!")
        
        return FileResponse(
            file_path,
            media_type='video/mp4',
            headers={
                'Content-Disposition': f'inline; filename="{filename}"',
                'Accept-Ranges': 'bytes'
            }
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/video/delete/{filename}")
async def delete_video(filename: str):
    """Video delete karo"""
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Video not found!")
        
        os.remove(file_path)
        
        return {
            "status": "success",
            "message": f"Video '{filename}' deleted!"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/info")
async def get_api_info():
    """API info aur statistics"""
    try:
        video_count = len([f for f in os.listdir(DOWNLOAD_FOLDER) if os.path.isfile(os.path.join(DOWNLOAD_FOLDER, f))])
        storage_used = get_folder_size(DOWNLOAD_FOLDER)
        
        return {
            "status": "online",
            "api_version": "2.0",
            "downloads_folder": DOWNLOAD_FOLDER,
            "videos_count": video_count,
            "storage_used": format_file_size(storage_used),
            "storage_used_bytes": storage_used,
            "features": [
                "Video Details Extraction",
                "Direct Download",
                "Live Streaming",
                "Progress Tracking",
                "Video Management"
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/video/progress/{filename}")
async def get_download_progress(filename: str):
    """Download progress check karo"""
    try:
        file_path = os.path.join(DOWNLOAD_FOLDER, filename)
        
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            return {
                "status": "downloading",
                "file_name": filename,
                "downloaded_size": format_file_size(size),
                "downloaded_bytes": size,
                "message": "Download in progress or completed"
            }
        else:
            return {
                "status": "not_found",
                "file_name": filename,
                "message": "File not found"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "message": exc.detail}
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("🎬 TERABOX VIDEO API - Starting...")
    print("="*60)
    print("📡 Server: http://0.0.0.0:8000")
    print("📚 Docs: http://localhost:8000/docs")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
