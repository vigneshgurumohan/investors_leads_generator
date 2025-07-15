import requests
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from fake_useragent import UserAgent
from config import SCRAPING_CONFIG
from bs4 import BeautifulSoup

class ContentScraper:
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def process_articles(self, search_results: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Process content from multiple URLs
        """
        processed_articles = []
        
        # Skip problematic domains
        skip_domains = [
            'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'google.com', 'bing.com', 'yahoo.com', 'reddit.com',
            'amazon.com', 'podcasts.apple.com', 'x.com'
        ]
        
        for i, result in enumerate(search_results):
            try:
                url = result['url']
                domain = urlparse(url).netloc.lower()
                
                # Skip problematic domains
                if any(skip_domain in domain for skip_domain in skip_domains):
                    print(f"Skipping {url} (problematic domain)")
                    continue
                
                print(f"Processing source {i + 1}/{len(search_results)}: {url}")
                
                article_data = self.process_single_article(url)
                if article_data:
                    # Merge with search result data
                    article_data.update({
                        'search_title': result['title'],
                        'search_snippet': result['snippet'],
                        'search_query': result['search_query']
                    })
                    processed_articles.append(article_data)
                
                # Random delay between requests
                time.sleep(random.uniform(1, 2))
                
                # Rotate user agent periodically
                if i % 5 == 0:
                    self.session.headers['User-Agent'] = self.ua.random
                
            except Exception as e:
                print(f"Error processing {result['url']}: {e}")
                continue
        
        return processed_articles
    
    def process_single_article(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Process content from a single URL using BeautifulSoup (bypassing newspaper3k)
        """
        try:
            print(f"📄 Processing: {url}")
            
            # Skip problematic file types and large files
            if self._should_skip_url(url):
                print(f"⏭️ Skipping {url} (file type or size issue)")
                return None
                
            return self._fallback_processing(url)
                
        except Exception as e:
            print(f"Failed to process {url}: {e}")
            return None
    
    def _fallback_processing(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Primary processing method using requests and BeautifulSoup
        """
        try:
            # Make request with proper headers
            headers = {
                'User-Agent': self.ua.random,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(url, timeout=15, headers=headers)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title = ""
            title_selectors = [
                'h1', 'title', 
                'meta[property="og:title"]',
                'meta[name="twitter:title"]',
                '.page-title', '.post-title', '.article-title'
            ]
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    title = element.get_text(strip=True) if element.name != 'meta' else element.get('content', '')
                    if title and len(title) > 5:
                        break
            
            # Extract text content
            text = ""
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'menu', 'iframe']):
                element.decompose()
            
            # Try to find main content with multiple selectors
            main_selectors = [
                'main', 'article', 
                '.content', '.post-content', '.entry-content', '#content',
                '.main-content', '.article-content', '.post-body',
                '.page-content', '.story-content', '.text-content'
            ]
            main_content = None
            
            for selector in main_selectors:
                main_content = soup.select_one(selector)
                if main_content:
                    break
            
            if main_content:
                text = main_content.get_text(strip=True)
            else:
                # Fallback to body text, but exclude navigation and other noise
                body = soup.find('body')
                if body:
                    # Remove navigation and other noise
                    for noise in body.find_all(['nav', 'header', 'footer', 'aside', 'menu']):
                        noise.decompose()
                    text = body.get_text(strip=True)
                else:
                    text = soup.get_text(strip=True)
            
            # Clean up text
            text = ' '.join(text.split())
            
            # Check content size to avoid memory issues
            if len(text) > 50000:  # Skip very large content (50KB+)
                print(f"❌ Content too large ({len(text)} chars): {url}")
                return None
            
            # Check if we have enough content
            if len(text) < 200:
                print(f"❌ Too little content ({len(text)} chars): {url}")
                return None
            
            # Check if content is relevant (contains executive-related keywords)
            text_lower = text.lower()
            executive_keywords = ['ceo', 'cfo', 'cmo', 'cto', 'coo', 'cio', 'chief', 'executive', 'president', 'director']
            if not any(keyword in text_lower for keyword in executive_keywords):
                print(f"❌ Content not relevant to executives: {url}")
                return None
            
            article_data = {
                'url': url,
                'title': title,
                'text': text,
                'summary': text[:500] if text else '',
                'keywords': [],
                'publish_date': None,
                'authors': [],
                'domain': urlparse(url).netloc,
                'word_count': len(text.split())
            }
            
            print(f"✅ Successfully processed ({len(text)} chars): {url}")
            return article_data
            
        except Exception as e:
            print(f"❌ Processing failed for {url}: {e}")
            return None
    
    def _is_valid_article(self, article_data: Dict[str, Any]) -> bool:
        """
        Check if article is valid for executive information extraction
        """
        # Check minimum word count
        if article_data['word_count'] < 100:
            return False
        
        # Check for executive-related keywords in title or text
        executive_keywords = [
            'executive', 'ceo', 'cfo', 'cmo', 'cto', 'coo', 'cio',
            'chief', 'president', 'director', 'manager', 'officer',
            'leadership', 'management', 'board', 'appointed', 'named',
            'joins', 'leaves', 'retires', 'promoted'
        ]
        
        text_to_check = f"{article_data['title']} {article_data['text']}".lower()
        
        return any(keyword in text_to_check for keyword in executive_keywords)
    
    def get_article_text(self, url: str) -> Optional[str]:
        """
        Simple method to get just the text content from a URL
        """
        article_data = self.process_single_article(url)
        return article_data['text'] if article_data else None
    
    def batch_process(self, urls: List[str], max_concurrent: int = 3) -> List[Dict[str, Any]]:
        """
        Process multiple URLs with controlled concurrency
        """
        results = []
        
        for i in range(0, len(urls), max_concurrent):
            batch = urls[i:i + max_concurrent]
            batch_results = []
            
            for url in batch:
                try:
                    article_data = self.process_single_article(url)
                    if article_data:
                        batch_results.append(article_data)
                except Exception as e:
                    print(f"Error in batch processing {url}: {e}")
            
            results.extend(batch_results)
            
            # Delay between batches
            if i + max_concurrent < len(urls):
                time.sleep(random.uniform(2, 5))
        
        return results 

    def _should_skip_url(self, url: str) -> bool:
        """
        Check if URL should be skipped based on file type or other criteria
        """
        url_lower = url.lower()
        
        # Skip file types that are typically large or problematic
        skip_extensions = [
            '.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx',
            '.zip', '.rar', '.tar', '.gz', '.7z',
            '.mp4', '.avi', '.mov', '.wmv', '.flv',
            '.mp3', '.wav', '.flac',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff',
            '.exe', '.dmg', '.deb', '.rpm'
        ]
        
        # Skip URLs with problematic extensions
        if any(ext in url_lower for ext in skip_extensions):
            return True
        
        # Skip URLs that are likely to be large files
        large_file_indicators = [
            '/download/', '/files/', '/assets/', '/documents/',
            '/reports/', '/annual-reports/', '/financial-reports/',
            '/SiteAssets/', '/uploads/', '/media/'
        ]
        
        if any(indicator in url_lower for indicator in large_file_indicators):
            return True
        
        return False 