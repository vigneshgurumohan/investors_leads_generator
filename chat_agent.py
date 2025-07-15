#!/usr/bin/env python3
"""
Professional Investor Leads Generator - Chat Agent
OpenAI-powered agent that understands user queries and generates JSON for batch processing
"""

import json
import re
from typing import Dict, Any, List, Optional, Tuple
import openai
from config import OPENAI_API_KEY

class ProfessionalInvestorAgent:
    def __init__(self):
        if not OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in config.py")
        
        self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        # System prompt for the agent
        self.system_prompt = """You are a Professional Investor Leads Generator specializing in finding CXO-level executives from companies. 

Your role is to:
1. Understand user queries about companies they want to research
2. Research and find relevant companies based on the query
3. Pay attention to quantity requests in user queries (e.g., "top 5", "10 companies", "first 3")
4. Generate structured JSON data for executive extraction
5. Communicate clearly with users about next steps

You can handle:
- Specific company names: "Find CXOs of Emirates NBD"
- Quantity-specific queries: "Top 5 technology companies in UAE", "Get 10 banking companies", "First 3 companies from Dubai"
- Vague industry queries: "Technology companies in UAE" (default to reasonable number)
- Regional queries: "Listed companies in Dubai"
- Mixed queries: "Find executives from top 7 banks and tech companies in UAE"

For quantity requests, look for patterns like:
- "top X", "first X", "X companies", "get X", "list X"
- If no quantity specified, use reasonable defaults (5-10 companies)

For vague queries, use your knowledge to find relevant companies. Focus on:
- UAE companies (primary market)
- Listed/public companies
- Major private companies
- Companies with significant CXO presence

Always respond in a helpful, professional tone and guide users through the process."""

    def process_user_query(self, user_query: str) -> Dict[str, Any]:
        """
        Process user query and return structured response with JSON data
        
        Args:
            user_query (str): User's natural language query
            
        Returns:
            Dict[str, Any]: Response with JSON data and communication
        """
        try:
            print(f"🤖 Processing query: {user_query}")
            
            # Step 1: Analyze the query and find companies
            analysis = self._analyze_query_and_find_companies(user_query)
            
            if not analysis.get('companies'):
                return {
                    'success': False,
                    'message': "I couldn't find any companies matching your query. Please try being more specific or provide company names directly.",
                    'json_data': None,
                    'companies_found': 0
                }
            
            # Step 2: Generate JSON for batch processor
            json_data = self._generate_json_for_batch(analysis['companies'])
            
            # Step 3: Generate user communication
            communication = self._generate_user_communication(user_query, analysis)
            
            return {
                'success': True,
                'message': communication,
                'json_data': json_data,
                'companies_found': len(analysis['companies']),
                'analysis': analysis
            }
            
        except Exception as e:
            print(f"❌ Error processing query: {e}")
            return {
                'success': False,
                'message': f"I encountered an error while processing your query: {str(e)}. Please try again.",
                'json_data': None,
                'companies_found': 0
            }

    def _analyze_query_and_find_companies(self, user_query: str) -> Dict[str, Any]:
        """
        Use OpenAI to analyze query and find relevant companies
        """
        prompt = f"""
        Analyze this user query and find relevant companies for executive research:
        
        User Query: "{user_query}"
        
        Your task:
        1. Understand what type of companies the user wants
        2. Pay attention to quantity requests (e.g., "top 5", "10 companies", "first 3")
        3. Research and find relevant companies
        4. Provide company details in a structured format
        
        For each company, provide:
        - name: Full company name
        - city: Company's city/location
        - country: Company's country (usually UAE)
        - industry: Company's industry/sector
        
        Focus on:
        - UAE companies (primary focus)
        - Listed/public companies
        - Major private companies
        - Companies likely to have CXO information available
        
        Quantity handling:
        - Look for patterns like "top X", "first X", "X companies", "get X", "list X"
        - If quantity specified, return exactly that many companies
        - If no quantity specified, return 5-10 companies (reasonable default)
        
        Return a JSON object with:
        {{
            "query_type": "specific|vague|industry|regional",
            "companies": [
                {{
                    "name": "Company Name",
                    "city": "City",
                    "country": "Country",
                    "industry": "Industry/Sector"
                }}
            ],
            "reasoning": "Brief explanation of why these companies were selected",
            "quantity_requested": "Number of companies requested (if specified)"
        }}
        
        If the query is about specific companies, focus on those. If vague, suggest relevant companies based on the context.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Parse the response
            if content.startswith('```json'):
                content = content[7:]
            if content.endswith('```'):
                content = content[:-3]
            
            analysis = json.loads(content)
            
            # Validate the structure
            if 'companies' not in analysis or not isinstance(analysis['companies'], list):
                raise ValueError("Invalid response structure: missing companies array")
            
            # Validate each company
            validated_companies = []
            for company in analysis['companies']:
                if self._validate_company_data(company):
                    validated_companies.append(company)
            
            analysis['companies'] = validated_companies
            
            print(f"✅ Found {len(validated_companies)} companies")
            return analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            # Fallback: try to extract companies from response
            return self._fallback_company_extraction(content, user_query)
        except Exception as e:
            print(f"❌ OpenAI API error: {e}")
            return self._fallback_company_extraction("", user_query)

    def _validate_company_data(self, company: Dict[str, Any]) -> bool:
        """
        Validate company data structure
        """
        required_fields = ['name', 'city', 'country', 'industry']
        
        for field in required_fields:
            if field not in company or not company[field] or not str(company[field]).strip():
                return False
        
        # Basic validation
        if len(str(company['name']).strip()) < 2:
            return False
        
        return True

    def _fallback_company_extraction(self, content: str, user_query: str) -> Dict[str, Any]:
        """
        Fallback method when OpenAI response parsing fails
        """
        print("🔄 Using fallback company extraction")
        
        # Try to extract company names from the response
        companies = []
        
        # Look for company patterns in the response
        if content:
            # Simple pattern matching for company names
            lines = content.split('\n')
            for line in lines:
                if '"name"' in line and '"city"' in line:
                    try:
                        # Try to extract JSON-like structure
                        match = re.search(r'"name":\s*"([^"]+)"', line)
                        if match:
                            name = match.group(1)
                            # Try to find other fields
                            city_match = re.search(r'"city":\s*"([^"]+)"', line)
                            country_match = re.search(r'"country":\s*"([^"]+)"', line)
                            industry_match = re.search(r'"industry":\s*"([^"]+)"', line)
                            
                            companies.append({
                                'name': name,
                                'city': city_match.group(1) if city_match else 'Unknown',
                                'country': country_match.group(1) if country_match else 'UAE',
                                'industry': industry_match.group(1) if industry_match else 'Unknown'
                            })
                    except:
                        continue
        
        # If still no companies, try to extract from user query
        if not companies:
            companies = self._extract_companies_from_query(user_query)
        
        return {
            'query_type': 'fallback',
            'companies': companies,
            'reasoning': 'Used fallback extraction due to parsing issues'
        }

    def _extract_companies_from_query(self, user_query: str) -> List[Dict[str, Any]]:
        """
        Extract company names from user query as last resort
        """
        companies = []
        
        # Look for common UAE company patterns
        uae_companies = [
            'Emirates NBD', 'First Abu Dhabi Bank', 'Abu Dhabi Islamic Bank',
            'Dubai Islamic Bank', 'Mashreq Bank', 'Commercial Bank of Dubai',
            'Abu Dhabi Commercial Bank', 'Union National Bank', 'ADNOC',
            'Emirates Airlines', 'Etisalat', 'du', 'Emaar', 'Nakheel'
        ]
        
        query_lower = user_query.lower()
        for company in uae_companies:
            if company.lower() in query_lower:
                companies.append({
                    'name': company,
                    'city': 'Dubai' if 'dubai' in company.lower() else 'Abu Dhabi',
                    'country': 'UAE',
                    'industry': 'Banking' if 'bank' in company.lower() else 'Energy' if 'adnoc' in company.lower() else 'Technology'
                })
        
        return companies

    def _generate_json_for_batch(self, companies: List[Dict[str, Any]]) -> str:
        """
        Generate JSON string for batch processor
        """
        json_data = {
            'companies': companies
        }
        
        return json.dumps(json_data, indent=2)

    def _generate_user_communication(self, user_query: str, analysis: Dict[str, Any]) -> str:
        """
        Generate user-friendly communication about next steps
        """
        companies = analysis['companies']
        query_type = analysis.get('query_type', 'unknown')
        reasoning = analysis.get('reasoning', '')
        
        if query_type == 'specific':
            message = f"Perfect! I found {len(companies)} companies matching your specific request. "
        elif query_type == 'vague':
            message = f"Great! I've researched and found {len(companies)} relevant companies based on your query. "
        else:
            message = f"Excellent! I've identified {len(companies)} companies for your research. "
        
        message += f"I'm now preparing to extract executive information for these companies.\n\n"
        
        # List the companies
        message += "**Companies to be processed:**\n"
        for i, company in enumerate(companies[:10], 1):  # Show first 10
            message += f"{i}. {company['name']} ({company['city']}, {company['industry']})\n"
        
        if len(companies) > 10:
            message += f"... and {len(companies) - 10} more companies\n"
        
        message += f"\n**Next Steps:**\n"
        message += "1. ✅ Company research completed\n"
        message += "2. 🔄 Starting executive extraction process\n"
        message += "3. 📊 Will extract CXO information (CEO, CFO, CTO, etc.)\n"
        message += "4. 📁 Results will be saved to CSV files\n"
        message += "5. 📧 Will attempt to find LinkedIn profiles and email addresses\n\n"
        
        message += "The process will take a few minutes. You'll receive real-time updates on the progress!"
        
        return message

    def get_agent_info(self) -> Dict[str, Any]:
        """
        Get information about the agent's capabilities
        """
        return {
            'name': 'Professional Investor Leads Generator',
            'version': '1.0.0',
            'capabilities': [
                'Process specific company queries',
                'Research companies for vague queries',
                'Generate structured JSON for batch processing',
                'Focus on UAE companies and CXO information',
                'Provide real-time progress updates'
            ],
            'example_queries': [
                'Find CXOs of Emirates NBD',
                'Top 10 technology companies in UAE',
                'Listed companies in Dubai',
                'Banking executives in Abu Dhabi',
                'Energy sector companies in UAE'
            ]
        } 