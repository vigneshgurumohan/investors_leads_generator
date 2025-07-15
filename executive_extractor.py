import re
import openai
import spacy
from typing import List, Dict, Any, Optional
from email_validator import validate_email, EmailNotValidError
from config import OPENAI_API_KEY, CXO_POSITIONS

class ExecutiveExtractor:
    def __init__(self):
        if OPENAI_API_KEY:
            try:
                self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                print(f"Warning: Could not initialize OpenAI client: {e}")
                self.client = None
        else:
            self.client = None
        
        # Load spaCy model for NER
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("spaCy model not found. Installing...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def extract_executives_from_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract executive information from multiple articles with target limit
        """
        executives = []
        
        # Import config to get target count
        from config import BATCH_CONFIG
        target_executive_count = BATCH_CONFIG.get('target_executives_per_company', 5)
        
        print(f"🎯 Target: Extract up to {target_executive_count} unique executives")
        
        for i, article in enumerate(articles):
            try:
                print(f"Extracting executives from article {i + 1}/{len(articles)}")
                
                article_executives = self.extract_from_single_article(article)
                executives.extend(article_executives)
                
                # Check if we've reached the target after deduplication
                unique_executives = self._deduplicate_executives(executives)
                if len(unique_executives) >= target_executive_count:
                    print(f"✅ Reached target executive count ({len(unique_executives)}), stopping extraction")
                    executives = unique_executives[:target_executive_count]  # Limit to target
                    break
                
            except Exception as e:
                print(f"Error extracting from article {i + 1}: {e}")
                continue
        
        # Remove duplicates and merge information (final deduplication)
        unique_executives = self._deduplicate_executives(executives)
        
        # Limit to target count
        if len(unique_executives) > target_executive_count:
            print(f"📊 Limiting results to target count: {target_executive_count}")
            unique_executives = unique_executives[:target_executive_count]
        
        # Enrich executives with LinkedIn and email information
        enriched_executives = self._enrich_executives(unique_executives)
        
        return enriched_executives
    
    def extract_executives_basic_from_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract only basic executive info (name, title, company/bank, source) from articles, without enrichment.
        """
        executives = []
        from config import BATCH_CONFIG
        target_executive_count = BATCH_CONFIG.get('target_executives_per_company', 5)
        print(f"🎯 [Basic] Target: Extract up to {target_executive_count} unique executives (basic info only)")
        
        for i, article in enumerate(articles):
            try:
                print(f"[Basic] Extracting executives from article {i + 1}/{len(articles)}")
                article_executives = self.extract_from_single_article(article)
                executives.extend(article_executives)
                
                # Check if we've reached the target after deduplication
                unique_executives = self._deduplicate_executives(executives)
                if len(unique_executives) >= target_executive_count:
                    print(f"✅ [Basic] Reached target executive count ({len(unique_executives)}), stopping extraction")
                    # Limit to target count and return immediately
                    limited_executives = unique_executives[:target_executive_count]
                    # Only keep basic fields
                    basic_executives = []
                    for ex in limited_executives:
                        basic_executives.append({
                            'name': ex.get('name'),
                            'title': ex.get('title'),
                            'company': ex.get('company') or ex.get('bank'),
                            'source_url': ex.get('source_url'),
                            'source_title': ex.get('source_title'),
                        })
                    return basic_executives
                    
            except Exception as e:
                print(f"Error extracting from article {i + 1}: {e}")
                continue
        
        # If we get here, we didn't reach the target, so return what we have
        unique_executives = self._deduplicate_executives(executives)
        if len(unique_executives) > target_executive_count:
            unique_executives = unique_executives[:target_executive_count]
        
        # Only keep basic fields
        basic_executives = []
        for ex in unique_executives:
            basic_executives.append({
                'name': ex.get('name'),
                'title': ex.get('title'),
                'company': ex.get('company') or ex.get('bank'),
                'source_url': ex.get('source_url'),
                'source_title': ex.get('source_title'),
            })
        return basic_executives
    
    def extract_from_single_article(self, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract executive information from a single article
        """
        executives = []
        
        # Combine title and text for analysis
        full_text = f"{article['title']}\n\n{article['text']}"
        
        # Use OpenAI for extraction if available
        if OPENAI_API_KEY:
            ai_executives = self._extract_with_openai(full_text, article)
            executives.extend(ai_executives)
        
        # Use spaCy as backup or additional extraction
        spacy_executives = self._extract_with_spacy(full_text, article)
        executives.extend(spacy_executives)
        
        # Extract emails and LinkedIn profiles
        emails = self._extract_emails(full_text)
        linkedin_profiles = self._extract_linkedin_profiles(full_text)
        
        # Merge email and LinkedIn information with executives
        for executive in executives:
            if not executive.get('email') and emails:
                executive['email'] = emails[0]  # Assign first email found
            if not executive.get('linkedin') and linkedin_profiles:
                executive['linkedin'] = linkedin_profiles[0]  # Assign first LinkedIn found
        
        return executives
    
    def _extract_with_openai(self, text: str, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use OpenAI to extract executive information
        """
        if not self.client:
            print("OpenAI client not available")
            return []
            
        try:
            prompt = f"""
            Extract executive information from this article. Look for:
            - Executive names
            - Their titles/positions
            - The company/organization they work for
            - Any email addresses
            - LinkedIn profile URLs
            
            Article text:
            {text[:4000]}  # Limit text length
            
            Return a JSON array of executives found, with this structure:
            [
                {{
                    "name": "Full Name",
                    "title": "Position Title",
                    "company": "Company Name",
                    "email": "email@domain.com" (if found),
                    "linkedin": "linkedin.com/in/profile" (if found),
                    "confidence": 0.9
                }}
            ]
            
            Only include executives from companies/organizations. If no executives found, return empty array [].
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.1
            )
            
            import json
            content = response.choices[0].message.content.strip()
            
            # Clean up the response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            executives = json.loads(content)
            
            # Add source information and normalize company field
            for executive in executives:
                executive.update({
                    'source_url': article['url'],
                    'source_title': article['title'],
                    'extraction_method': 'openai'
                })
                # Normalize company field (for backward compatibility)
                if 'company' in executive and 'bank' not in executive:
                    executive['bank'] = executive['company']
            
            return executives
            
        except Exception as e:
            print(f"OpenAI extraction failed: {e}")
            return []
    
    def _extract_with_spacy(self, text: str, article: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Use spaCy NER to extract executive information
        """
        executives = []
        
        try:
            doc = self.nlp(text)
            
            # Find person names
            persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
            
            # Find organizations (banks)
            organizations = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
            
            # Look for executive titles near person names
            for person in persons[:10]:  # Limit to first 10 persons
                # Find context around the person name
                person_context = self._find_person_context(text, person)
                
                if person_context:
                    title = self._extract_title_from_context(person_context)
                    company = self._identify_company_from_context(person_context, organizations)
                    
                    if title and company:
                        executives.append({
                            'name': person,
                            'title': title,
                            'bank': company,  # Keep 'bank' field for backward compatibility
                            'email': None,
                            'linkedin': None,
                            'confidence': 0.7,
                            'source_url': article['url'],
                            'source_title': article['title'],
                            'extraction_method': 'spacy'
                        })
        
        except Exception as e:
            print(f"spaCy extraction failed: {e}")
        
        return executives
    
    def _find_person_context(self, text: str, person: str) -> Optional[str]:
        """
        Find context around a person's name
        """
        try:
            # Find the position of the person's name
            pos = text.find(person)
            if pos == -1:
                return None
            
            # Extract context (100 characters before and after)
            start = max(0, pos - 100)
            end = min(len(text), pos + len(person) + 100)
            
            return text[start:end]
        except:
            return None
    
    def _extract_title_from_context(self, context: str) -> Optional[str]:
        """
        Extract executive title from context
        """
        context_lower = context.lower()
        
        for position in CXO_POSITIONS:
            if position.lower() in context_lower:
                return position
        
        return None
    
    def _identify_company_from_context(self, context: str, organizations: List[str]) -> Optional[str]:
        """
        Identify which company from the context
        """
        context_lower = context.lower()
        
        # First check UAE banks (for backward compatibility) - simplified since UAE_BANKS was removed
        # This section can be enhanced with a custom bank list if needed
        pass
        
        # Check organizations list for any company
        for org in organizations:
            # Skip generic terms
            if org.lower() in ['company', 'corporation', 'inc', 'ltd', 'llc']:
                continue
            return org
        
        return None
    
    def _extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text
        """
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        # Validate emails
        valid_emails = []
        for email in emails:
            try:
                validate_email(email)
                valid_emails.append(email)
            except EmailNotValidError:
                continue
        
        return valid_emails
    
    def _extract_linkedin_profiles(self, text: str) -> List[str]:
        """
        Extract LinkedIn profile URLs from text
        """
        linkedin_pattern = r'https?://(?:www\.)?linkedin\.com/in/[A-Za-z0-9_-]+'
        profiles = re.findall(linkedin_pattern, text)
        return profiles
    
    def _deduplicate_executives(self, executives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate executives and merge information
        """
        unique_executives = {}
        
        for executive in executives:
            # Create a key based on name and bank
            key = f"{executive['name'].lower()}_{executive['bank'].lower()}"
            
            if key in unique_executives:
                # Merge information
                existing = unique_executives[key]
                
                # Keep the higher confidence extraction
                if executive.get('confidence', 0) > existing.get('confidence', 0):
                    unique_executives[key] = executive
                
                # Merge additional information
                if not existing.get('email') and executive.get('email'):
                    existing['email'] = executive['email']
                if not existing.get('linkedin') and executive.get('linkedin'):
                    existing['linkedin'] = executive['linkedin']
                if not existing.get('title') and executive.get('title'):
                    existing['title'] = executive['title']
            else:
                unique_executives[key] = executive
        
        return list(unique_executives.values())
    
    def _enrich_executives(self, executives: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrich executives with LinkedIn profiles and email addresses
        """
        if not executives:
            return executives
        
        # Import config to get target count
        from config import BATCH_CONFIG
        target_executive_count = BATCH_CONFIG.get('target_executives_per_company', 5)
        
        # Limit executives to target count for enrichment
        executives_to_enrich = executives[:target_executive_count]
        
        print(f"\n🔍 Enriching {len(executives_to_enrich)} executives with contact information...")
        
        # Import serpapi_searcher for web searches
        from serpapi_searcher import SerpAPISearcher
        searcher = SerpAPISearcher()
        
        for i, executive in enumerate(executives_to_enrich):
            try:
                print(f"Enriching executive {i + 1}/{len(executives_to_enrich)}: {executive.get('name', 'Unknown')}")
                
                # Generate enrichment queries
                enrichment_queries = self._generate_enrichment_queries(executive)
                
                # Try to find LinkedIn profile first
                linkedin_found = False
                for query in enrichment_queries[:2]:  # Try first 2 queries for LinkedIn
                    linkedin = self._search_linkedin_profile(query, executive, searcher)
                    if linkedin:
                        executive['linkedin'] = linkedin
                        linkedin_found = True
                        print(f"✅ Found LinkedIn: {linkedin}")
                        break
                
                # If LinkedIn not found, try to find email
                if not linkedin_found:
                    for query in enrichment_queries[1:]:  # Try remaining queries for email
                        email = self._search_email_address(query, executive, searcher)
                        if email:
                            executive['email'] = email
                            print(f"✅ Found email: {email}")
                            break
                
                # Add delay between executives to respect rate limits
                if i < len(executives_to_enrich) - 1:
                    import time
                    time.sleep(2)  # 2 second delay between executives
                
            except Exception as e:
                print(f"⚠️ Error enriching executive {executive.get('name', 'Unknown')}: {e}")
                continue
        
        return executives_to_enrich
    
    def _generate_enrichment_queries(self, executive: Dict[str, Any]) -> List[str]:
        """
        Generate enrichment queries for finding LinkedIn and email
        """
        name = executive.get('name', '')
        company = executive.get('bank', '') or executive.get('company', '')
        title = executive.get('title', '')
        
        if not name or not company:
            return []
        
        # Clean up name and company
        name = name.strip()
        company = company.strip()
        
        queries = [
            f'"{name}" "{company}" LinkedIn profile',
            f'"{name}" "{company}" email contact',
            f'"{name}" "{company}" {title} contact information',
            f'"{name}" "{company}" executive contact'
        ]
        
        return queries
    
    def _search_linkedin_profile(self, query: str, executive: Dict[str, Any], searcher) -> str:
        """
        Search for LinkedIn profile URL using web search
        """
        try:
            # Perform web search
            search_results = searcher.search_google(query, max_results=3)
            
            if not search_results:
                return None
            
            # Extract LinkedIn URLs from search results
            for result in search_results:
                url = result.get('url', '').lower()
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                
                # Look for LinkedIn URLs
                if 'linkedin.com/in/' in url:
                    return url
                elif 'linkedin.com/in/' in snippet:
                    # Extract LinkedIn URL from snippet
                    import re
                    linkedin_match = re.search(r'linkedin\.com/in/[a-zA-Z0-9\-_]+', snippet)
                    if linkedin_match:
                        return f"https://www.{linkedin_match.group()}"
                
                # Use OpenAI to extract LinkedIn from content if needed
                if hasattr(self, 'client') and self.client:
                    prompt = f"""
                    Extract LinkedIn profile URL from this search result.
                    
                    Title: {result.get('title', '')}
                    URL: {result.get('url', '')}
                    Snippet: {result.get('snippet', '')}
                    
                    Executive: {executive.get('name', '')} at {executive.get('bank', '') or executive.get('company', '')}
                    
                    Return only the LinkedIn profile URL if found, or "NOT_FOUND" if not found.
                    Format: linkedin.com/in/username or NOT_FOUND
                    """
                    
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=50,
                        temperature=0.1
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    if result_text.startswith('linkedin.com/') and result_text != 'NOT_FOUND':
                        return result_text
                
        except Exception as e:
            print(f"LinkedIn search failed: {e}")
        
        return None
    
    def _search_email_address(self, query: str, executive: Dict[str, Any], searcher) -> str:
        """
        Search for email address using web search
        """
        try:
            # Perform web search
            search_results = searcher.search_google(query, max_results=3)
            
            if not search_results:
                return None
            
            # Extract email addresses from search results
            for result in search_results:
                url = result.get('url', '')
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                
                # Look for email patterns
                import re
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                
                # Check snippet for emails
                emails = re.findall(email_pattern, snippet)
                for email in emails:
                    # Validate email format
                    try:
                        from email_validator import validate_email
                        validate_email(email)
                        return email
                    except:
                        continue
                
                # Use OpenAI to extract email from content if needed
                if hasattr(self, 'client') and self.client:
                    prompt = f"""
                    Extract email address from this search result.
                    
                    Title: {title}
                    URL: {url}
                    Snippet: {snippet}
                    
                    Executive: {executive.get('name', '')} at {executive.get('bank', '') or executive.get('company', '')}
                    
                    Return only the email address if found, or "NOT_FOUND" if not found.
                    Format: email@domain.com or NOT_FOUND
                    """
                    
                    response = self.client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        max_tokens=50,
                        temperature=0.1
                    )
                    
                    result_text = response.choices[0].message.content.strip()
                    
                    if '@' in result_text and result_text != 'NOT_FOUND':
                        # Validate email format
                        try:
                            from email_validator import validate_email
                            validate_email(result_text)
                            return result_text
                        except:
                            pass
                
        except Exception as e:
            print(f"Email search failed: {e}")
        
        return None
    
    def generate_email_guesses(self, name: str, company: str) -> List[str]:
        """
        Generate possible email addresses for an executive
        """
        # For companies, try to extract domain from company name
        # This is a simplified approach - in practice, you'd need a domain database
        company_lower = company.lower().replace(' ', '').replace('.', '')
        domain = f"{company_lower}.com"  # Default guess
        
        name_parts = name.split()
        
        if len(name_parts) < 2:
            return []
        
        first_name = name_parts[0].lower()
        last_name = name_parts[-1].lower()
        first_initial = first_name[0]
        
        email_patterns = [
            f"{first_name}.{last_name}@{domain}",
            f"{first_initial}.{last_name}@{domain}",
            f"{first_name}{last_name}@{domain}",
            f"{first_initial}{last_name}@{domain}",
            f"{first_name}_{last_name}@{domain}",
            f"{first_initial}_{last_name}@{domain}"
        ]
        
        return email_patterns 