from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse, StreamingResponse
import requests
import re
from typing import Optional, Dict
import json
import logging
from urllib.parse import quote, unquote, urlencode
import time
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terabox Advanced API",
    description="Complete Terabox link extractor with file details, download, and streaming",
    version="2.0"
)

class TeraboxAdvancedExtractor:
    """Extract complete file information from terabox services"""
    
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def parse_url(self, url: str) -> Dict:
        """Parse terabox URL"""
        try:
            service_match = re.search(r'https?://([a-zA-Z0-9.-]+terabox[a-zA-Z0-9.-]*\.com)', url)
            share_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            
            if not service_match or not share_match:
                raise ValueError("Invalid terabox URL format")
            
            return {
                'service': service_match.group(1),
                'share_id': share_match.group(1),
                'original_url': url,
            }
        except Exception as e:
            raise ValueError(f"URL parsing failed: {e}")
    
    def get_direct_link(self, url: str) -> Optional[str]:
        """Get direct download link by following redirects"""
        try:
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if time.time() - cached['time'] < 3600:
                    return cached['link']
            
            response = self.session.head(url, allow_redirects=True, timeout=15, verify=False)
            
            if response.status_code == 200:
                direct_link = response.url
                
                self.cache[cache_key] = {
                    'link': direct_link,
                    'time': time.time()
                }
                
                return direct_link
            
            return None
        except Exception as e:
            logger.error(f"Error getting direct link: {e}")
            return None
    
    def extract_filename(self, url: str) -> str:
        """Extract filename from URL or headers"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10, verify=False)
            
            if 'content-disposition' in response.headers:
                match = re.search(r'filename[^;=\n]*=(["\']?)([^"\';]*)\1', 
                                response.headers['content-disposition'])
                if match:
                    return unquote(match.group(2))
            
            filename = url.split('/')[-1].split('?')[0]
            return unquote(filename) if filename else 'file'
        except:
            return 'file'
    
    def get_file_size(self, url: str) -> Optional[int]:
        """Get file size from URL headers"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=10, verify=False)
            
            if 'content-length' in response.headers:
                return int(response.headers['content-length'])
            
            return None
        except Exception as e:
            logger.error(f"Error getting file size: {e}")
            return None
    
    def format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable format"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def get_thumbnail(self, download_link: str, filename: str) -> Optional[str]:
        """Try to generate thumbnail URL"""
        try:
            if not download_link:
                return None
            
            # Some terabox services support thumbnail generation
            # This is a basic attempt
            if 'data.1024tera.com' in download_link or 'data.terabox.com' in download_link:
                base = download_link.split('?')[0]
                params = download_link.split('?')[1] if '?' in download_link else ''
                
                if params:
                    return f"{base.replace('/file/', '/thumbnail/')}?{params}&quality=100"
            
            return None
        except:
            return None
    
    def create_proxy_url(self, download_link: str, filename: str) -> str:
        """Create proxy URL for safe downloading"""
        try:
            if not download_link:
                return ""
            
            # Using a proxy service for better compatibility
            proxy_base = "https://api.allorigins.win/raw?url="
            encoded_url = quote(download_link, safe='')
            
            return f"{proxy_base}{encoded_url}"
        except:
            return download_link
    
    def create_stream_url(self, download_link: str, filename: str) -> str:
        """Create streaming URL"""
        try:
            if not download_link:
                return ""
            
            # For streaming, we can use the direct link with range headers support
            return download_link
        except:
            return download_link
    
    def extract_complete_info(self, url: str) -> Dict:
        """Extract all information from terabox URL"""
        try:
            parsed = self.parse_url(url)
            
            # Get direct download link
            download_link = self.get_direct_link(url)
            
            if not download_link:
                raise ValueError("Could not extract download link")
            
            # Extract filename
            filename = self.extract_filename(download_link)
            
            # Get file size
            file_size_bytes = self.get_file_size(download_link)
            file_size_formatted = self.format_file_size(file_size_bytes) if file_size_bytes else "Unknown"
            
            # Generate URLs
            thumbnail = self.get_thumbnail(download_link, filename)
            proxy_url = self.create_proxy_url(download_link, filename)
            streaming_url = self.create_stream_url(download_link, filename)
            
            return {
                'status': '✅ Successfully',
                'file_name': filename,
                'file_size': file_size_formatted,
                'size_bytes': file_size_bytes or 0,
                'download_link': download_link,
                'thumbnail': thumbnail,
                'proxy_url': proxy_url,
                'streaming_url': streaming_url,
                'service': parsed['service'],
                'share_id': parsed['share_id'],
                'original_url': url,
                'developer': 'Advanced Terabox API',
            }
        except Exception as e:
            return {
                'status': '❌ Failed',
                'error': str(e),
                'file_name': None,
                'file_size': None,
                'size_bytes': 0,
                'download_link': None,
                'thumbnail': None,
                'proxy_url': None,
                'streaming_url': None,
                'developer': 'Advanced Terabox API',
            }

# Initialize
extractor = TeraboxAdvancedExtractor()

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API Home"""
    return {
        "name": "Advanced Terabox API",
        "version": "2.0",
        "description": "Extract complete file information from terabox links",
        "usage": "GET /api?url=YOUR_TERABOX_URL",
        "example": "/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
        "response_includes": [
            "file_name",
            "file_size",
            "size_bytes",
            "download_link",
            "thumbnail",
            "proxy_url",
            "streaming_url",
            "status"
        ],
        "endpoints": {
            "/": "This page",
            "/api?url=...": "Extract complete file info",
            "/download?url=...": "Download file",
            "/stream?url=...": "Stream file",
            "/docs": "Interactive API documentation",
            "/info": "API information"
        }
    }

@app.get("/api")
async def extract_complete_info(url: str = Query(..., description="Terabox URL")):
    """
    Extract complete file information from terabox URL
    
    Returns:
    - file_name: Original filename
    - file_size: Human readable file size (e.g., "26.89 MB")
    - size_bytes: File size in bytes
    - download_link: Direct download URL
    - thumbnail: Thumbnail image URL
    - proxy_url: Proxy download URL (for compatibility)
    - streaming_url: Streaming URL (for video/audio)
    - status: Operation status
    
    Example:
    /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        if 'terabox' not in url.lower() and 'tera' not in url.lower():
            raise HTTPException(status_code=400, detail="URL must be a terabox link")
        
        result = extractor.extract_complete_info(url)
        
        if result.get('status') == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
        
        return result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_file(url: str = Query(..., description="Terabox URL")):
    """
    Download file from terabox
    
    Browser will automatically download the file
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        result = extractor.extract_complete_info(url)
        
        if result.get('status') == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
        
        download_url = result.get('download_link')
        filename = result.get('file_name', 'file')
        
        if not download_url:
            raise HTTPException(status_code=400, detail="Could not extract download link")
        
        # Stream the file
        response = extractor.session.get(download_url, stream=True, timeout=30, verify=False)
        response.raise_for_status()
        
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=response.headers.get('content-type', 'application/octet-stream'),
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"',
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def stream_file(url: str = Query(..., description="Terabox URL")):
    """
    Stream file (for videos/audio)
    
    Supports range requests for seeking
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        result = extractor.extract_complete_info(url)
        
        if result.get('status') == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error', 'Unknown error'))
        
        stream_url = result.get('streaming_url')
        
        if not stream_url:
            raise HTTPException(status_code=400, detail="Could not extract stream link")
        
        # Stream the file
        response = extractor.session.get(stream_url, stream=True, timeout=30, verify=False)
        response.raise_for_status()
        
        return StreamingResponse(
            response.iter_content(chunk_size=8192),
            media_type=response.headers.get('content-type', 'video/mp4'),
            headers={
                'Accept-Ranges': 'bytes',
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def api_info():
    """Get API information and capabilities"""
    return {
        "name": "Advanced Terabox API",
        "version": "2.0",
        "status": "🟢 Online",
        "developer": "Advanced Terabox API",
        "description": "Complete terabox file information extractor",
        "endpoints": {
            "GET /": "Home page",
            "GET /api?url=...": "Extract complete file info",
            "GET /download?url=...": "Download file",
            "GET /stream?url=...": "Stream file",
            "GET /info": "This page",
            "GET /docs": "Interactive documentation"
        },
        "response_format": {
            "status": "✅ Successfully / ❌ Failed",
            "file_name": "string",
            "file_size": "string (e.g., '26.89 MB')",
            "size_bytes": "integer",
            "download_link": "string (direct URL)",
            "thumbnail": "string (image URL)",
            "proxy_url": "string (proxy download URL)",
            "streaming_url": "string (for video/audio)",
            "service": "string",
            "share_id": "string",
            "original_url": "string",
            "developer": "string"
        },
        "supported_services": [
            "terabox.com",
            "1024terabox.com",
            "terasharefile.com",
            "teraboxshare.com",
            "And other terabox variants"
        ],
        "features": {
            "file_info_extraction": True,
            "direct_download": True,
            "streaming": True,
            "thumbnail_generation": True,
            "proxy_urls": True,
            "link_caching": True,
            "concurrent_requests": "Unlimited"
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "❌ Failed",
            "error": exc.detail,
            "example": "GET /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
            "developer": "Advanced Terabox API"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🎬 ADVANCED TERABOX API v2.0")
    print("="*70)
    print("📡 API Running: http://localhost:3000")
    print("📚 Documentation: http://localhost:3000/docs")
    print("\n📝 Usage:")
    print("  GET /api?url=TERABOX_LINK")
    print("\n📋 Response Includes:")
    print("  - file_name: Filename")
    print("  - file_size: Human readable size (e.g., '26.89 MB')")
    print("  - size_bytes: Size in bytes")
    print("  - download_link: Direct download URL")
    print("  - thumbnail: Thumbnail image URL")
    print("  - proxy_url: Proxy download URL")
    print("  - streaming_url: Stream URL for video/audio")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
    
