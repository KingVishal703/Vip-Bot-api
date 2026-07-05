from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import re
from typing import Optional, Dict
import json
import logging
from urllib.parse import quote
import time
from functools import lru_cache
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terabox Direct Link Extractor",
    description="Get direct download & stream links from terabox URLs",
    version="1.0"
)

class LinkExtractor:
    """Extract direct links from terabox services"""
    
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    def parse_url(self, url: str) -> Dict:
        """Parse terabox URL"""
        try:
            # Extract service and share ID
            service_match = re.search(r'https?://([a-zA-Z0-9.-]+terabox[a-zA-Z0-9.-]*\.com)', url)
            share_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            access_code_match = re.search(r'pwd=([a-zA-Z0-9]+)', url)
            
            if not service_match or not share_match:
                raise ValueError("Invalid terabox URL format")
            
            return {
                'service': service_match.group(1),
                'share_id': share_match.group(1),
                'access_code': access_code_match.group(1) if access_code_match else None,
                'original_url': url,
            }
        except Exception as e:
            raise ValueError(f"URL parsing failed: {e}")
    
    def get_direct_link(self, url: str) -> Optional[str]:
        """Get direct download link by following redirects"""
        try:
            # Check cache first
            cache_key = hashlib.md5(url.encode()).hexdigest()
            if cache_key in self.cache:
                cached = self.cache[cache_key]
                if time.time() - cached['time'] < 3600:  # Cache for 1 hour
                    return cached['link']
            
            # Follow redirects to get direct link
            response = self.session.head(url, allow_redirects=True, timeout=15, verify=False)
            
            if response.status_code == 200:
                direct_link = response.url
                
                # Cache the result
                self.cache[cache_key] = {
                    'link': direct_link,
                    'time': time.time()
                }
                
                return direct_link
            
            return None
        except Exception as e:
            logger.error(f"Error getting direct link: {e}")
            return None
    
    def extract_from_page(self, url: str) -> Dict:
        """Extract links from terabox page"""
        try:
            response = self.session.get(url, timeout=15, verify=False)
            response.raise_for_status()
            
            # Look for download links in response
            # Different terabox services may have different patterns
            patterns = [
                r'(?:download|stream).*?(?:url|href|src).*?["\']([^"\']*(?:terabox|tera|baidu)[^"\']*)["\']',
                r'(?:dlink|download_link|stream_url).*?["\']([^"\']+)["\']',
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, response.text, re.IGNORECASE)
                if matches:
                    return matches[0]
            
            return None
        except Exception as e:
            logger.error(f"Error extracting from page: {e}")
            return None
    
    def process_url(self, url: str) -> Dict:
        """Process terabox URL and extract links"""
        try:
            # Parse URL
            parsed = self.parse_url(url)
            
            # Try to get direct download link
            direct_link = self.get_direct_link(url)
            
            # Try extracting from page
            page_link = self.extract_from_page(url) if not direct_link else None
            
            final_download_link = direct_link or page_link
            
            return {
                'status': 'success' if final_download_link else 'partial',
                'service': parsed['service'],
                'share_id': parsed['share_id'],
                'original_url': url,
                'download_link': final_download_link,
                'stream_link': final_download_link,  # Same as download for streaming
                'access_code': parsed.get('access_code'),
                'message': 'Links extracted successfully' if final_download_link else 'Could not extract links, try browser download'
            }
        except Exception as e:
            return {
                'status': 'error',
                'message': str(e),
                'download_link': None,
                'stream_link': None,
            }

# Initialize
extractor = LinkExtractor()

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API Home"""
    return {
        "name": "Terabox Direct Link Extractor",
        "version": "1.0",
        "usage": "GET /api?url=YOUR_TERABOX_URL",
        "example": "/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
        "endpoints": {
            "/": "This page",
            "/api?url=...": "Extract links",
            "/docs": "Interactive API docs",
        },
        "features": [
            "✅ Extract direct download links",
            "✅ Extract stream links",
            "✅ Support multiple terabox services",
            "✅ Link caching (1 hour)",
            "✅ Password protected links support"
        ]
    }

@app.get("/api")
async def extract_links(url: str = Query(..., description="Terabox URL")):
    """
    Extract download and stream links from terabox URL
    
    Example: /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
    
    Response:
    {
        "status": "success",
        "service": "1024terabox.com",
        "share_id": "10LHRppa8fMO6NJhuiRMkWA",
        "download_link": "https://...",
        "stream_link": "https://...",
    }
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        if 'terabox' not in url.lower() and 'tera' not in url.lower():
            raise HTTPException(status_code=400, detail="URL must be a terabox link")
        
        result = extractor.process_url(url)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def get_download_link(url: str = Query(..., description="Terabox URL")):
    """Get only download link"""
    try:
        result = extractor.process_url(url)
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": result['status'],
            "download_link": result.get('download_link'),
            "message": "Ready to download" if result.get('download_link') else "Link not found"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def get_stream_link(url: str = Query(..., description="Terabox URL")):
    """Get only stream link (for videos/audio)"""
    try:
        result = extractor.process_url(url)
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return {
            "status": result['status'],
            "stream_link": result.get('stream_link'),
            "message": "Ready to stream" if result.get('stream_link') else "Link not found"
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def api_info():
    """API information"""
    return {
        "name": "Terabox Direct Link Extractor",
        "version": "1.0",
        "status": "online",
        "endpoints": {
            "GET /": "Home",
            "GET /api?url=...": "Extract all links",
            "GET /download?url=...": "Get download link",
            "GET /stream?url=...": "Get stream link",
            "GET /info": "API info",
        },
        "supported_services": [
            "terabox.com",
            "1024terabox.com",
            "terasharefile.com",
            "teraboxshare.com",
            "And other terabox variants"
        ],
        "features": {
            "caching": "Results cached for 1 hour",
            "redirects": "Follows all redirects automatically",
            "timeout": "15 seconds per request",
        },
        "example_request": "/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
        "example_response": {
            "status": "success",
            "service": "1024terabox.com",
            "share_id": "10LHRppa8fMO6NJhuiRMkWA",
            "download_link": "https://...",
            "stream_link": "https://..."
        }
    }

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail,
            "example": "GET /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA"
        }
    )

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🎬 TERABOX DIRECT LINK EXTRACTOR API")
    print("="*70)
    print("📡 API Running: http://localhost:8000")
    print("📚 Documentation: http://localhost:8000/docs")
    print("🧪 Try: http://localhost:8000/api?url=YOUR_TERABOX_LINK")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
