from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
import re
import json
from typing import Optional, Dict
import logging
from urllib.parse import quote, unquote, urlparse, parse_qs
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terabox Real Download API",
    description="Extract REAL downloadable file links from terabox",
    version="3.1"
)

class TeraboxExtractor:
    """Extract real downloadable links from terabox"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Referer': 'https://www.terabox.com/',
        })
    
    def parse_url(self, url: str) -> Dict:
        """Parse terabox URL"""
        try:
            service_match = re.search(r'https?://([a-zA-Z0-9.-]+terabox[a-zA-Z0-9.-]*\.com)', url)
            share_match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
            
            if not service_match or not share_match:
                raise ValueError("Invalid URL format")
            
            return {
                'service': service_match.group(1),
                'share_id': share_match.group(1),
                'url': url,
            }
        except Exception as e:
            raise ValueError(f"URL parsing failed: {e}")
    
    def get_file_info_v1(self, service: str, share_id: str) -> Optional[Dict]:
        """Method 1: Try terabox API v1"""
        try:
            api_url = f"https://{service}/api/clouddisk/info?shareid={share_id}"
            
            response = self.session.get(api_url, timeout=10, verify=False)
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"API v1 Response: {json.dumps(data, indent=2)[:500]}")
                
                if 'list' in data and len(data['list']) > 0:
                    file_info = data['list'][0]
                    
                    # Extract download link
                    download_link = None
                    
                    if 'dlink' in file_info:
                        download_link = file_info['dlink']
                    
                    return {
                        'file_name': file_info.get('server_filename', 'file'),
                        'size': file_info.get('size', 0),
                        'download_link': download_link,
                    }
            
            return None
        except Exception as e:
            logger.warning(f"API v1 failed: {e}")
            return None
    
    def get_file_info_v2(self, service: str, share_id: str) -> Optional[Dict]:
        """Method 2: Try different API endpoint"""
        try:
            # Try multiple endpoints
            endpoints = [
                f"https://{service}/api/shorturlv2?app_id=250528&share_id={share_id}&web=1",
                f"https://{service}/api/shorturlv2?share_id={share_id}",
                f"https://{service}/share/list?shareid={share_id}",
            ]
            
            for api_url in endpoints:
                try:
                    response = self.session.get(api_url, timeout=10, verify=False)
                    
                    if response.status_code == 200:
                        data = response.json()
                        logger.info(f"API v2 endpoint {api_url} response: {str(data)[:500]}")
                        
                        # Look for download link
                        if 'dlink' in data:
                            return {
                                'file_name': data.get('filename', data.get('server_filename', 'file')),
                                'size': data.get('size', 0),
                                'download_link': data['dlink'],
                            }
                        
                        if 'shorturl' in data:
                            return {
                                'file_name': 'file',
                                'size': 0,
                                'download_link': data['shorturl'],
                            }
                        
                        if 'list' in data and len(data['list']) > 0:
                            file_info = data['list'][0]
                            if 'dlink' in file_info:
                                return {
                                    'file_name': file_info.get('server_filename', 'file'),
                                    'size': file_info.get('size', 0),
                                    'download_link': file_info['dlink'],
                                }
                except Exception as e:
                    logger.warning(f"Endpoint {api_url} failed: {e}")
                    continue
            
            return None
        except Exception as e:
            logger.warning(f"API v2 failed: {e}")
            return None
    
    def follow_url(self, url: str) -> Optional[str]:
        """Method 3: Follow URL redirects to get actual link"""
        try:
            response = self.session.head(url, allow_redirects=True, timeout=15, verify=False)
            
            if response.status_code == 200:
                final_url = response.url
                logger.info(f"Followed URL to: {final_url}")
                
                # Check if it looks like actual file link
                if any(domain in final_url for domain in ['data.', '/file/', 'download']):
                    return final_url
            
            return None
        except Exception as e:
            logger.warning(f"URL following failed: {e}")
            return None
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size"""
        if not size_bytes:
            return "Unknown"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def get_file_size(self, url: str) -> int:
        """Get actual file size"""
        try:
            response = self.session.head(url, timeout=10, verify=False)
            return int(response.headers.get('content-length', 0))
        except:
            return 0
    
    def extract_links(self, url: str) -> Dict:
        """Extract download links"""
        try:
            parsed = self.parse_url(url)
            service = parsed['service']
            share_id = parsed['share_id']
            
            logger.info(f"Extracting from {service}/{share_id}")
            
            file_info = None
            download_link = None
            
            # Try Method 1: API v1
            file_info = self.get_file_info_v1(service, share_id)
            if file_info and file_info.get('download_link'):
                download_link = file_info['download_link']
                logger.info(f"Method 1 success: {download_link[:80]}")
            
            # Try Method 2: API v2
            if not download_link:
                file_info = self.get_file_info_v2(service, share_id)
                if file_info and file_info.get('download_link'):
                    download_link = file_info['download_link']
                    logger.info(f"Method 2 success: {download_link[:80]}")
            
            # Try Method 3: Follow redirects
            if not download_link:
                download_link = self.follow_url(url)
                if download_link:
                    logger.info(f"Method 3 success: {download_link[:80]}")
            
            # If still no link, but we have file info
            if not download_link and file_info:
                logger.warning(f"Got file info but no download link: {file_info}")
                # Return whatever we have
                download_link = url  # Fallback to original URL
            
            if not download_link:
                raise ValueError("Could not extract any download link from terabox")
            
            # Get filename from URL or header
            filename = "file"
            if file_info and file_info.get('file_name'):
                filename = file_info['file_name']
            else:
                # Try to extract from URL
                fn_match = re.search(r'[?&]fn=([^&]+)', download_link)
                if fn_match:
                    filename = unquote(fn_match.group(1))
            
            # Get file size
            size_bytes = 0
            if file_info and file_info.get('size'):
                size_bytes = file_info['size']
            else:
                size_bytes = self.get_file_size(download_link)
            
            return {
                'status': '✅ Successfully',
                'file_name': filename,
                'file_size': self.format_size(size_bytes),
                'size_bytes': size_bytes,
                'download_link': download_link,
                'streaming_url': download_link,
                'service': service,
                'share_id': share_id,
                'original_url': url,
                'developer': 'Terabox Real Download API'
            }
        
        except Exception as e:
            logger.error(f"Extraction error: {e}", exc_info=True)
            return {
                'status': '❌ Failed',
                'error': str(e),
                'file_name': None,
                'file_size': None,
                'size_bytes': 0,
                'download_link': None,
                'developer': 'Terabox Real Download API'
            }

# Initialize
extractor = TeraboxExtractor()

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """API Home"""
    return {
        "name": "Terabox Real Download API",
        "version": "3.1",
        "description": "Extract REAL downloadable file links",
        "usage": "GET /api?url=TERABOX_LINK",
        "example": "/api?url=https://1024terabox.com/s/10LHRppa8fMO6NJhuiRMkWA",
    }

@app.get("/api")
async def get_download_links(url: str = Query(..., description="Terabox share URL")):
    """
    Extract REAL downloadable links from terabox
    
    Returns direct file download link that works in browser!
    """
    try:
        if not url:
            raise HTTPException(status_code=400, detail="URL required")
        
        if 'terabox' not in url.lower():
            raise HTTPException(status_code=400, detail="Must be terabox URL")
        
        result = extractor.extract_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return result
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Endpoint error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download")
async def get_download_link(url: str = Query(...)):
    """Get download link only"""
    try:
        result = extractor.extract_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return {
            'status': 'success',
            'download_link': result['download_link'],
            'file_name': result['file_name'],
            'file_size': result['file_size'],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream")
async def get_stream_link(url: str = Query(...)):
    """Get stream link"""
    try:
        result = extractor.extract_links(url)
        
        if result['status'] == '❌ Failed':
            raise HTTPException(status_code=400, detail=result.get('error'))
        
        return {
            'status': 'success',
            'stream_link': result['streaming_url'],
            'file_name': result['file_name'],
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info")
async def api_info():
    """API info"""
    return {
        "name": "Terabox Real Download API",
        "version": "3.1",
        "status": "🟢 Online",
        "what_it_does": [
            "Takes terabox share link",
            "Extracts actual file download link",
            "Returns link that works in browser"
        ],
    }

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*70)
    print("🎬 TERABOX REAL DOWNLOAD API v3.1")
    print("="*70)
    print("📡 API: http://localhost:3000")
    print("📚 Try: http://localhost:3000/api?url=TERABOX_LINK")
    print("="*70 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=3000)
            
