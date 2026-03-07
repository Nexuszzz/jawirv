#!/usr/bin/env python
"""Test Computer Use dengan gemini-3-pro-preview - Journal Search & Download to Local"""
import os
import sys

# Load API keys from environment (JANGAN hardcode di sini!)
# Set GOOGLE_API_KEYS di .env dengan format: GOOGLE_API_KEYS=key1,key2,key3
_raw_keys = os.environ.get("GOOGLE_API_KEYS", os.environ.get("GOOGLE_API_KEY", ""))
API_KEYS = [k.strip() for k in _raw_keys.split(",") if k.strip()]

if not API_KEYS:
    raise ValueError("GOOGLE_API_KEY atau GOOGLE_API_KEYS harus di-set di environment/.env")

# Set API key (coba yang pertama)
os.environ["GOOGLE_API_KEY"] = API_KEYS[0]

from computer_use import PlaywrightComputer, BrowserAgent

# Folder untuk menyimpan jurnal
DOWNLOAD_FOLDER = "D:\\jawirv2\\jawirv2\\downloads\\journals"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

print("=" * 60)
print("🚀 Testing JAWIR Computer Use - Journal Search & DOWNLOAD")
print("=" * 60)
print(f"📌 Model: gemini-3-pro-preview")
print(f"📌 API Key: {os.environ.get('GOOGLE_API_KEY', 'NOT SET')[:25]}...")
print(f"📁 Download Folder: {DOWNLOAD_FOLDER}")
print()

def search_and_download_journal():
    """Search journal on arXiv and download PDF to local."""
    
    # Search query - use arXiv search URL directly for reliability
    search_query = "Machine Learning IoT"
    search_url = f"https://arxiv.org/search/?searchtype=all&query={search_query.replace(' ', '+')}&start=0"
    
    with PlaywrightComputer(
        initial_url=search_url, 
        headless=False,  # Show browser
        highlight_mouse=True,
        download_folder=DOWNLOAD_FOLDER,  # Set download folder
    ) as browser:
        
        browser._page.context.set_default_timeout(60000)  # 60 detik timeout
        
        # STEP 1: Click on first paper using Playwright selector
        print("\n📚 STEP 1: Finding papers on arXiv...")
        print(f"🔍 Search Query: {search_query}")
        print("-" * 50)
        
        # Wait for search results to load
        browser._page.wait_for_load_state("networkidle", timeout=15000)
        import time
        time.sleep(2)
        
        # Find first paper link using selector
        try:
            # arXiv search results have paper titles with class 'title'
            first_paper = browser._page.query_selector("li.arxiv-result p.title a")
            if not first_paper:
                first_paper = browser._page.query_selector("p.title a")
            if not first_paper:
                first_paper = browser._page.query_selector("a[href*='/abs/']")
            
            if first_paper:
                paper_title_text = first_paper.text_content().strip()
                print(f"📄 Found paper: {paper_title_text[:80]}...")
                first_paper.click()
                browser._page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(1)
                print("✅ Clicked on paper, navigating to abstract page...")
            else:
                print("⚠️ Using AI agent to find paper...")
                # Fallback to agent
                agent = BrowserAgent(
                    browser_computer=browser,
                    query="Click on the first paper title link to go to its abstract page",
                    model_name="gemini-3-pro-preview",
                    verbose=True,
                    max_iterations=5
                )
                agent.run()
        except Exception as e:
            print(f"⚠️ Selector method failed: {e}, using AI agent...")
            agent = BrowserAgent(
                browser_computer=browser,
                query="Click on any paper title link on this page",
                model_name="gemini-3-pro-preview",
                verbose=True,
                max_iterations=5
            )
            agent.run()
        
        # STEP 2: Get arXiv ID and title from abstract page
        current_url = browser._page.url
        print(f"\n🔗 Current URL: {current_url}")
        
        # Extract arXiv ID from URL
        arxiv_id = None
        if "arxiv.org/abs/" in current_url:
            arxiv_id = current_url.split("/abs/")[-1].split("?")[0].split("#")[0].split("v")[0]
        
        if not arxiv_id:
            # Try to find arXiv ID in page content
            page_text = browser._page.text_content("body") or ""
            import re
            match = re.search(r'arXiv:(\d{4}\.\d{4,5})', page_text)
            if match:
                arxiv_id = match.group(1)
        
        if arxiv_id:
            print(f"\n📄 Found arXiv ID: {arxiv_id}")
            
            # Get paper title from page
            paper_title = "Unknown"
            try:
                title_elem = browser._page.query_selector("h1.title")
                if title_elem:
                    paper_title = title_elem.text_content().replace("Title:", "").strip()
                else:
                    # Try meta tag
                    meta_title = browser._page.query_selector("meta[name='citation_title']")
                    if meta_title:
                        paper_title = meta_title.get_attribute("content")
            except:
                pass
            
            # Get authors
            authors = "Unknown"
            try:
                authors_elem = browser._page.query_selector("div.authors")
                if authors_elem:
                    authors = authors_elem.text_content().replace("Authors:", "").strip()[:100]
            except:
                pass
            
            print(f"📝 Title: {paper_title}")
            print(f"👥 Authors: {authors}")
            
            # Take screenshot of abstract page
            screenshot_path = os.path.join(DOWNLOAD_FOLDER, "journal_abstract.png")
            browser.screenshot_to_file(screenshot_path)
            print(f"📸 Abstract Screenshot: {screenshot_path}")
            
            # STEP 3: Download PDF directly using arXiv PDF URL pattern
            print("\n📥 STEP 2: Downloading PDF...")
            print("-" * 50)
            
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            print(f"📎 PDF URL: {pdf_url}")
            
            # Download PDF using urllib (more reliable)
            import urllib.request
            
            # Clean filename
            clean_title = "".join(c for c in paper_title if c.isalnum() or c in (' ', '-', '_')).strip()
            clean_title = clean_title[:60] if clean_title and clean_title != "Unknown" else "paper"
            filename = f"arxiv_{arxiv_id.replace('.', '_')}_{clean_title}.pdf"
            save_path = os.path.join(DOWNLOAD_FOLDER, filename)
            
            print(f"⏳ Downloading to: {save_path}")
            urllib.request.urlretrieve(pdf_url, save_path)
            
            # Verify download
            if os.path.exists(save_path):
                file_size = os.path.getsize(save_path)
                print(f"\n✅ SUCCESS! PDF Downloaded!")
                print(f"📄 Filename: {filename}")
                print(f"📁 Location: {save_path}")
                print(f"📊 File Size: {file_size / 1024:.1f} KB ({file_size / (1024*1024):.2f} MB)")
                
                return {
                    "success": True,
                    "arxiv_id": arxiv_id,
                    "title": paper_title,
                    "authors": authors,
                    "pdf_path": save_path,
                    "pdf_url": pdf_url,
                    "file_size_kb": file_size / 1024,
                }
            else:
                print("❌ Download failed - file not found")
                return {"success": False, "error": "Download failed"}
        else:
            print("❌ Could not find arXiv ID")
            return {"success": False, "error": "arXiv ID not found"}

try:
    result = search_and_download_journal()
    
    print()
    print("=" * 60)
    print("📝 FINAL RESULT:")
    print("=" * 60)
    
    if result.get("success"):
        print(f"✅ Paper downloaded successfully!")
        print(f"📄 arXiv ID: {result.get('arxiv_id')}")
        print(f"📝 Title: {result.get('title')}")
        print(f"📁 PDF saved at: {result.get('pdf_path')}")
        print(f"📊 File Size: {result.get('file_size_kb', 0):.1f} KB")
        print(f"🔗 PDF URL: {result.get('pdf_url')}")
    else:
        print(f"❌ Failed: {result.get('error')}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
