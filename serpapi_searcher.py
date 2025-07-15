import time
import random
from typing import List, Dict, Any
from serpapi import GoogleSearch
from config import SERPAPI_KEY, SCRAPING_CONFIG

class SerpAPISearcher:
    def __init__(self):
        if not SERPAPI_KEY:
            raise ValueError("SERPAPI_KEY not found in environment variables. Please add it to your .env file.")
        self.api_key = SERPAPI_KEY
    
    def search_google(self, query: str, max_pages: int = None, max_results: int = None) -> List[Dict[str, str]]:
        """
        Perform Google search using SerpAPI
        """
        if max_pages is None:
            max_pages = 1  # Reduced from SCRAPING_CONFIG['max_pages_per_search'] for speed
        if max_results is None:
            max_results = 5  # Reduced from 10 for speed
        
        all_results = []
        
        for page in range(max_pages):
            try:
                print(f"Searching page {page + 1} for: {query}")
                
                # Configure SerpAPI search
                search_params = {
                    "q": query,
                    "api_key": self.api_key,
                    "engine": "google",
                    "start": page * 10,  # SerpAPI uses start parameter
                    "num": 10,  # Results per page
                    "hl": "en",
                    "gl": "us"  # Country
                }
                
                # Perform search
                search = GoogleSearch(search_params)
                results = search.get_dict()
                
                # Extract organic results
                organic_results = results.get("organic_results", [])
                
                if not organic_results:
                    print(f"No results found on page {page + 1}")
                    break
                
                # Process results
                page_results = []
                for result in organic_results:
                    try:
                        # Extract data from SerpAPI result
                        title = result.get("title", "")
                        url = result.get("link", "")
                        snippet = result.get("snippet", "")
                        
                        if title and url and url.startswith('http'):
                            # Filter out non-relevant results
                            if self._is_relevant_result(title, snippet, url):
                                page_results.append({
                                    'title': title,
                                    'url': url,
                                    'snippet': snippet,
                                    'search_query': query
                                })
                                print(f"✅ Found: {title[:50]}...")
                    
                    except Exception as e:
                        print(f"Error processing result: {e}")
                        continue
                
                all_results.extend(page_results)
                
                # Check if we have enough results
                if len(all_results) >= max_results:
                    print(f"Reached maximum results limit ({max_results})")
                    break
                
                if len(organic_results) < 10:
                    print(f"Reached end of results on page {page + 1}")
                    break
                
                # Reduced delay for speed
                if page < max_pages - 1:
                    delay = random.uniform(0.5, 1.5)  # Reduced from 1-3 seconds
                    print(f"Waiting {delay:.1f} seconds...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"Error searching page {page + 1}: {e}")
                break
        
        # Limit results to max_results
        return all_results[:max_results]
    
    def _is_relevant_result(self, title: str, snippet: str, url: str) -> bool:
        """
        Check if search result is relevant to our executive search
        """
        text = f"{title} {snippet}".lower()
        
        # Skip certain types of pages
        skip_domains = [
            'youtube.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'linkedin.com', 'indeed.com', 'glassdoor.com', 'monster.com',
            'google.com', 'bing.com', 'yahoo.com'
        ]
        
        if any(domain in url.lower() for domain in skip_domains):
            return False
        
        # Look for executive-related keywords
        executive_keywords = [
            'executive', 'ceo', 'cfo', 'cmo', 'cto', 'coo', 'cio',
            'chief', 'president', 'director', 'manager', 'officer',
            'leadership', 'management', 'board'
        ]
        
        return any(keyword in text for keyword in executive_keywords)
    
    def search_multiple_queries(self, queries: List[str], max_results_per_query: int = None) -> List[Dict[str, str]]:
        """
        Search multiple queries and combine results
        """
        all_results = []
        
        for i, query in enumerate(queries):
            print(f"\nSearching query {i + 1}/{len(queries)}: {query}")
            results = self.search_google(query, max_results=max_results_per_query)
            all_results.extend(results)
            
            # Delay between different queries
            if i < len(queries) - 1:
                delay = random.uniform(2, 5)
                print(f"Waiting {delay:.1f} seconds between queries...")
                time.sleep(delay)
        
        # Remove duplicates based on URL
        unique_results = []
        seen_urls = set()
        
        for result in all_results:
            if result['url'] not in seen_urls:
                unique_results.append(result)
                seen_urls.add(result['url'])
        
        print(f"\n✅ Total unique results found: {len(unique_results)}")
        return unique_results
    
    def test_api(self):
        """
        Test the SerpAPI connection
        """
        try:
            print("🧪 Testing SerpAPI connection...")
            
            search_params = {
                "q": "CEO Apple",
                "api_key": self.api_key,
                "engine": "google",
                "num": 3
            }
            
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            if "organic_results" in results:
                print(f"✅ SerpAPI working! Found {len(results['organic_results'])} results")
                return True
            else:
                print(f"❌ SerpAPI error: {results}")
                return False
                
        except Exception as e:
            print(f"❌ SerpAPI test failed: {e}")
            return False 