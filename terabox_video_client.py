#!/usr/bin/env python3
"""
Terabox Video API - Advanced Client
Video details, download, streaming sab kuch!
"""

import requests
import sys
import json
import time
from datetime import datetime
from tabulate import tabulate
from urllib.parse import quote

BASE_URL = "http://localhost:8000"

class TeraboxVideoClient:
    def __init__(self, base_url=BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
    
    def check_api(self):
        """API online hai ya nahi check karo"""
        try:
            response = self.session.get(f"{self.base_url}/video/info", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def get_video_details(self, url: str):
        """Video ki saari details nikalo"""
        print(f"\n{'='*60}")
        print(f"🔍 Fetching video details...")
        print(f"{'='*60}\n")
        
        try:
            response = self.session.post(
                f"{self.base_url}/video/details",
                json={"url": url, "include_metadata": True},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                metadata = data.get('video_metadata', {})
                
                print("✅ VIDEO DETAILS FOUND!\n")
                print(f"{'='*60}")
                print(f"📹 TITLE: {metadata.get('title', 'N/A')}")
                print(f"{'='*60}")
                print(f"📊 FILE SIZE: {metadata.get('file_size', 'N/A')}")
                print(f"📝 FILE TYPE: {metadata.get('file_type', 'N/A')}")
                print(f"🎬 DURATION: {metadata.get('duration', 'Not available')}")
                print(f"📐 RESOLUTION: {metadata.get('resolution', 'Not available')}")
                print(f"🎥 CODEC: {metadata.get('codec', 'Not available')}")
                print(f"⏱️  FPS: {metadata.get('fps', 'Not available')}")
                print(f"📈 BITRATE: {metadata.get('bitrate', 'Not available')}")
                print(f"📅 CREATED: {metadata.get('created_date', 'N/A')}")
                print(f"{'='*60}\n")
                
                print("🎯 AVAILABLE ACTIONS:")
                print("   1. ⬇️  Download")
                print("   2. ▶️  Stream/Watch")
                print("   3. 📋 List Downloads")
                print("   4. 🗑️  Delete")
                print(f"{'='*60}\n")
                
                return metadata
            else:
                error = response.json()
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"❌ Connection error: {str(e)}")
            return None
    
    def download_video(self, url: str, wait_for_completion=False):
        """Video download karo"""
        print(f"\n{'='*60}")
        print(f"⬇️  Starting video download...")
        print(f"{'='*60}\n")
        
        try:
            response = self.session.post(
                f"{self.base_url}/video/download",
                json={"url": url},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                file_name = data.get('file_name', 'video')
                
                print(f"✅ Download started!")
                print(f"📁 File: {file_name}")
                print(f"📊 Size: {data.get('total_size', 'N/A')}")
                print(f"{'='*60}\n")
                
                if wait_for_completion:
                    print("⏳ Waiting for download to complete...")
                    while True:
                        progress_response = self.session.get(
                            f"{self.base_url}/video/progress/{quote(file_name)}",
                            timeout=10
                        )
                        
                        if progress_response.status_code == 200:
                            progress_data = progress_response.json()
                            size = progress_data.get('downloaded_size', '0 B')
                            print(f"   Downloaded: {size}", end='\r')
                            
                            if "completed" in progress_data.get('message', '').lower():
                                print(f"\n✅ Download completed! Size: {size}\n")
                                break
                        
                        time.sleep(2)
                
                return True
            else:
                error = response.json()
                print(f"❌ Error: {error.get('message', 'Unknown error')}")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def stream_video(self, url: str, quality: str = "best"):
        """Video stream karo (watch online)"""
        print(f"\n{'='*60}")
        print(f"▶️  Setting up stream...")
        print(f"{'='*60}\n")
        
        try:
            print(f"🎬 Streaming at quality: {quality}")
            print(f"URL: {self.base_url}/video/stream")
            print(f"\n💡 Video stream is ready!")
            print(f"📝 Request Body:")
            print(f'{{\n  "url": "{url}",')
            print(f'  "quality": "{quality}"\n}}')
            print(f"{'='*60}\n")
            
            response = self.session.post(
                f"{self.base_url}/video/stream",
                json={"url": url, "quality": quality},
                stream=True,
                timeout=60
            )
            
            if response.status_code == 200:
                print(f"✅ Stream active!")
                print(f"📊 Content-Type: {response.headers.get('content-type', 'video/mp4')}")
                print(f"📏 Content-Length: {response.headers.get('content-length', 'unknown')}")
                print(f"\n💻 Stream connection established!")
                return True
            else:
                print(f"❌ Streaming failed")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False
    
    def list_downloads(self):
        """Sab downloaded videos list karo"""
        print(f"\n{'='*60}")
        print(f"📋 DOWNLOADED VIDEOS")
        print(f"{'='*60}\n")
        
        try:
            response = self.session.get(f"{self.base_url}/video/downloads", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                videos = data.get('videos', [])
                
                print(f"Total Videos: {data.get('total_videos', 0)}")
                print(f"Total Storage: {data.get('total_storage', '0 B')}")
                print(f"\n{'='*60}\n")
                
                if videos:
                    table_data = []
                    for i, video in enumerate(videos, 1):
                        table_data.append([
                            i,
                            video['name'][:40] + '...' if len(video['name']) > 40 else video['name'],
                            video['size'],
                            video['downloaded_at'][:10]  # Date only
                        ])
                    
                    headers = ["#", "📁 Name", "📊 Size", "📅 Date"]
                    print(tabulate(table_data, headers=headers, tablefmt="grid"))
                    
                    print(f"\n{'='*60}")
                    print(f"\n💡 TIP: Use '/video/watch/filename' to watch online")
                    print(f"{'='*60}\n")
                else:
                    print("❌ No videos downloaded yet!\n")
                
                return videos
            else:
                print(f"❌ Error fetching downloads")
                return []
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return []
    
    def delete_video(self, filename: str):
        """Video delete karo"""
        print(f"\n⚠️  Deleting: {filename}")
        
        try:
            response = self.session.delete(
                f"{self.base_url}/video/delete/{quote(filename)}",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {data['message']}\n")
                return True
            else:
                error = response.json()
                print(f"❌ Error: {error.get('message', 'Unknown error')}\n")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}\n")
            return False
    
    def get_api_info(self):
        """API info aur features"""
        print(f"\n{'='*60}")
        print(f"ℹ️  API INFORMATION")
        print(f"{'='*60}\n")
        
        try:
            response = self.session.get(f"{self.base_url}/video/info", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                print(f"✅ Status: {data['status'].upper()}")
                print(f"📦 Version: {data['api_version']}")
                print(f"📁 Folder: {data['downloads_folder']}")
                print(f"🎬 Videos: {data['videos_count']}")
                print(f"💾 Storage: {data['storage_used']}")
                print(f"\n🎯 Features:")
                
                for feature in data.get('features', []):
                    print(f"   ✨ {feature}")
                
                print(f"\n{'='*60}\n")
                return True
            else:
                print(f"❌ Cannot get API info")
                return False
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return False


def print_banner():
    """Banner print karo"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║         🎬 TERABOX VIDEO API - ADVANCED CLIENT 🎬         ║
║                                                           ║
║     Video Details • Download • Streaming • Management     ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

def print_menu():
    """Main menu"""
    print(f"\n{'='*60}")
    print("📺 MAIN MENU")
    print(f"{'='*60}")
    print("1️⃣  Get Video Details (Title, Size, etc.)")
    print("2️⃣  Download Video")
    print("3️⃣  Stream Video (Watch Online)")
    print("4️⃣  List Downloaded Videos")
    print("5️⃣  Delete Video")
    print("6️⃣  API Information")
    print("7️⃣  Exit")
    print(f"{'='*60}\n")


def main():
    """Main function"""
    print_banner()
    
    client = TeraboxVideoClient()
    
    # API check karo
    print("🔍 Checking API connection...")
    if not client.check_api():
        print("❌ API is not running!")
        print("Please start: python terabox_video_api.py")
        sys.exit(1)
    
    print("✅ API is online!\n")
    time.sleep(1)
    
    while True:
        print_menu()
        choice = input("👉 Choose option (1-7): ").strip()
        
        if choice == "1":
            url = input("\n🔗 Enter Terabox video link: ").strip()
            if url:
                metadata = client.get_video_details(url)
            
        elif choice == "2":
            url = input("\n🔗 Enter Terabox video link: ").strip()
            if url:
                wait = input("⏳ Wait for completion? (y/n): ").lower() == 'y'
                client.download_video(url, wait_for_completion=wait)
        
        elif choice == "3":
            url = input("\n🔗 Enter Terabox video link: ").strip()
            if url:
                quality = input("🎬 Quality (best/high/medium/low) [default: best]: ").strip() or "best"
                client.stream_video(url, quality)
        
        elif choice == "4":
            client.list_downloads()
        
        elif choice == "5":
            videos = client.list_downloads()
            if videos:
                filename = input("\n📁 Enter filename to delete: ").strip()
                if filename:
                    confirm = input(f"⚠️  Delete '{filename}'? (y/n): ").lower()
                    if confirm == 'y':
                        client.delete_video(filename)
        
        elif choice == "6":
            client.get_api_info()
        
        elif choice == "7":
            print("\n👋 Goodbye! Happy watching! 🎬\n")
            sys.exit(0)
        
        else:
            print("❌ Invalid choice! Try again.")
        
        input("\n⏎ Press Enter to continue...")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...\n")
        sys.exit(0)
              
