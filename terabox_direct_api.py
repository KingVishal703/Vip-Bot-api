from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import re
import json
from typing import Optional, Dict
import logging
from urllib.parse import quote, unquote
import time
import hashlib

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terabox Direct Download API",
    description="Extract actual downloadable file links from terabox shares",
    version="3.0"
)

class TeraboxRealExtractor:
    """Extract REAL downloadable links from terabox"""
    
    def __init__(self):
        self.cache = {}
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.terabox.com/',
        })
    
    def parse_share_url(self, url: str) -> Dict:
        """Extract share ID and service from URL"""
        try:
            # Extract service domain
            service_match = re.search(r'https?://([a-zA-Z0-9.-]+terabox[a-zA-Z0-9.-]*\.com)', url)
            # Extract share ID
            share_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            
            if not service_match or not share_match:
                raise ValueError("Invalid terabox URL")
            
            service = service_match.group(1)
            share_id = share_match.group(1)
            
            return {
                'service': service,
                'share_id': share_id,
                'url': url,
            }
        except Exception as e:
            raise ValueError(f"URL parsing failed: {e}")
    
    def get_share_page(self, url: str) -> Optional[str]:
        """Get terabox share page content"""
        try:
            response = self.session.get(url, timeout=15, verify=False)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Error fetching share page: {e}")
            return None
    
    def extract_file_info_from_page(self, html_content: str) -> Optional[Dict]:
        """Extract file info from HTML page"""
        try:
            # Look for file list data in page
            patterns = [
                r'"list":\s*(\[.*?\])',
                r'"filename":"([^"]+)".*?"size":(\d+)',
                r'var\s+fileinfo\s*=\s*(\{.*?\})',
                r'"server_filename":"([^"]+)"',
            ]
            
            file_info = {}
            
            for pattern in patterns:
                match = re.search(pattern, html_content)
                if match:
                    if 'list' in pattern:
                        try:
                            list_data = json.loads(match.group(1))
                            if isinstance(list_data, list) and len(list_data) > 0:
                                file_info = list_data[0]
                                break
                        except:
                            pass
            
            return file_info if file_info else None
        except Exception as e:
            logger.error(f"Error extracting file info: {e}")
            return None
    
    def get_dlink_from_api(self, service: str, share_id: str) -> Optional[str]:
        """Get dlink (actual file link) from terabox API"""
        try:
            # Try multiple terabox API endpoints
            endpoints = [
                f"https://{service}/api/shorturlv2?app_id=250528&weiyun=1&share_id={share_id}",
                f"https://{service}/api/shorturlv2?app_id=250528&share_id={share_id}",
                f"https://{service}/api/download?share_id={share_id}",
            ]
            
            for api_url in endpoints:
                try:
                    response = self.session.get(api_url, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"API Response: {data}")
                        
                        # Look for download link in response
                        if 'dlink' in data:
                            return data['dlink']
                        elif 'shorturl' in data:
                            return data['shorturl']
                        elif 'download_link' in data:
                            return data['download_link']
                        elif 'list' in data and len(data['list']) > 0:
                            file_info = data['list'][0]
                            if 'dlink' in file_info:
                                return file_info['dlink']
                except Exception as e:
                    logger.warning(f"API endpoint failed: {api_url} - {e}")
                    continue
            
            return None
        except Exception as e:
            logger.error(f"Error getting dlink: {e}")
            return None
    
    def follow_redirect(self, url: str) -> Optional[str]:
        """Follow redirects to get actual download link"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=15, verify=False)
            
            if response.status_code == 200:
                return response.url
            
            return url
        except Exception as e:
            logger.error(f"Error following redirect: {e}")
            return url
    
    def format_file_size(self, size_bytes: int) -> str:
        """Convert bytes to human readable"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    def extract_real_links(self, url: str) -> Dict:
        """Extract REAL downloadable links from terabox"""
        try:
            # Parse URL
            parsed = self.parse_share_url(url)
            service = parsed['service']
            share_id = parsed['share_id']
            
            logger.info(f"Extracting from: {service} - {share_id}")
            
            # Method 1: Try API first
            dlink = self.get_dlink_from_api(service, share_id)
            
            # Method 2: If API fails, try page content
            if not dlink:
                page_content = self.get_share_page(url)
                if page_content:
                    file_info = self.extract_file_info_from_page(page_content)
                    if file_info and 'dlink' in file_info:
                        dlink = file_info['dlink']
            
            # Method 3: Try to follow share link directly
            if not dlink:
                dlink = self.follow_redirect(url)
            
            if not dlink or dlink == url:
                raise ValueError("Could not extract actual download link")
            
            # Verify it's a real download link (should contain /file/)
            if '/file/' not in dlink and 'data.' not in dlink:
                raise ValueError("Extracted link doesn't look like actual file link")
            
            # Extract filename
            filename_match = re.search(r'[?&]fn=([^&]+)', dlink)
            filename = unquote(filename_match.group(1)) if filename_match else 'file'
            
            # Get file size
            try:
                size_response = self.session.head(dlink, timeout=10, verify=False)
                size_bytes = int(size_response.headers.get('content-length', 0))
            except:
                size_bytes = 0
            
            return {
                'status': '✅ Successfully',
                'file_name': filename,
                'file_size': self.format_file_size(size_bytes),
                'size_bytes': size_bytes,
                'download_link': dlink,
                'streaming_url': dlink,  # Same as download for direct playback
                'thumbnail': None,
                'proxy_url': dlink,
                'service': service,
                'share_id': share_id,
                'original_url': url,
                'developer': 'Terabox Real Download API'
            }
        
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {
                'status': '❌ Failed',
                'error': str(e),
                'file_name': None,
                'file_size': None,
                'size_bytes': 0,
                'download_link': None,
                'streaming_url': None,
                'thumbnail': None,
                'proxy_url': None,
                'developer': 'Terabox Real Download API'
            }

# Initialize
extractor = TeraboxRealExtractor()

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API Home"""
    return {
        "name": "Terabox Real Download API",
        "version": "3.0",
        "description": "Extract REAL downloadable file links from terabox shares",
        "usage": "GET /api?url=YOUR_TERABOX_SHARE_URL",
        "example": "/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
        "response_includes": [
            "file_name",
            "file_size",
            "download_link (REAL direct link)",
            "streaming_url",
            "status"
        ],
    }

@app.get("/api")
async def get_download_links(url: str = Query(..., description="Terabox share URL")):
    """
    Extract REAL downloadable file links from terabox
    
    Returns:
    - download_link: ACTUAL file download link (not terabox page link!)
    - streaming_url: Direct streaming link
    - file_name: Original filename
    - file_size: File size in human-readable format
    
    Example:
    /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL parameter required")
        
        if 'terabox' not in url.lower():
            raise HTTPException(status_code=400, detail="Must be a terabox URL")
        
        result = extractor.extract_real_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error', 'Failed to extract links'))
        
        return result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def download_redirect(url: str = Query(..., description="Terabox share URL")):
    """
    Get download link and redirect to it
    """
    try:
        result = extractor.extract_real_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        download_link = result.get('download_link')
        
        if not download_link:
            raise HTTPException(status_code=400, detail="Could not extract download link")
        
        return {
            'status': 'success',
            'download_link': download_link,
            'file_name': result.get('file_name'),
            'file_size': result.get('file_size'),
            'message': 'Use this link to download: ' + download_link
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def stream_redirect(url: str = Query(..., description="Terabox share URL")):
    """
    Get stream link for video/audio
    """
    try:
        result = extractor.extract_real_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        stream_link = result.get('streaming_url')
        
        if not stream_link:
            raise HTTPException(status_code=400, detail="Could not extract stream link")
        
        return {
            'status': 'success',
            'stream_link': stream_link,
            'file_name': result.get('file_name'),
            'message': 'Use this link to stream: ' + stream_link
        }
    
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def api_info():
    """Get API info"""
    return {
        "name": "Terabox Real Download API",
        "version": "3.0",
        "status": "🟢 Online",
        "description": "Extracts REAL downloadable links (not terabox share pages)",
        "what_it_does": [
            "Takes terabox share link as input",
            "Extracts ACTUAL file download URL",
            "Returns direct download/stream links",
            "Works in browser directly"
        ],
        "endpoints": {
            "GET /api?url=...": "Get all links",
            "GET /download?url=...": "Get download link",
            "GET /stream?url=...": "Get stream link",
            "GET /info": "This page"
        }
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🎬 TERABOX REAL DOWNLOAD API v3.0")
    print("="*70)
    print("📡 API: http://localhost:3000")
    print("📚 Docs: http://localhost:3000/docs")
    print("\n🎯 What it does:")
    print("  Input:  Terabox share link")
    print("  Output: ACTUAL downloadable file link")
    print("\n📝 Example:")
    print("  GET /api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA")
    print("  Returns: download_link (direct file URL)")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
                    
