#!/usr/bin/env python3
"""
Professional Investor Leads Generator
A comprehensive tool to extract CXO-level executives using AI-powered chat agent and batch processing.
"""

import sys
import time
import json
from typing import List, Dict, Any
from serpapi_searcher import SerpAPISearcher
from content_scraper import ContentScraper
from executive_extractor import ExecutiveExtractor
from data_exporter import DataExporter
from chat_agent import ProfessionalInvestorAgent
from batch_extractor import BatchExtractor
from config import BATCH_CONFIG

class ProfessionalInvestorLeadsGenerator:
    def __init__(self):
        self.serpapi_searcher = SerpAPISearcher()
        self.content_scraper = ContentScraper()
        self.executive_extractor = ExecutiveExtractor()
        self.data_exporter = DataExporter()
        self.chat_agent = ProfessionalInvestorAgent()
        self.batch_extractor = BatchExtractor()
    
    def run(self, user_query: str = None):
        """
        Main execution flow with AI chat agent
        """
        print("🚀 Professional Investor Leads Generator")
        print("="*60)
        
        # Get user query if not provided
        if not user_query:
            user_query = self._get_user_input()
        
        print(f"\n🤖 Processing your request: {user_query}")
        
        try:
            # Step 1: Use chat agent to analyze query and find companies
            print("\n🔍 Step 1: AI Agent analyzing your query and researching companies...")
            agent_response = self.chat_agent.process_user_query(user_query)
            
            if not agent_response['success']:
                print(f"❌ {agent_response['message']}")
                return
            
            # Display agent's response
            print(f"\n{agent_response['message']}")
            
            # Step 2: Show identified companies in logs
            print(f"\n📋 Step 2: Companies identified by AI Agent:")
            print("="*60)
            
            # Parse and display companies
            companies_data = json.loads(agent_response['json_data'])
            companies = companies_data.get('companies', [])
            
            for i, company in enumerate(companies, 1):
                print(f"{i:2d}. {company['name']} - {company['city']}, {company['country']} ({company['industry']})")
            
            print("="*60)
            print(f"Total companies found: {len(companies)}")
            
            # Save companies to CSV file
            print(f"\n💾 Saving companies to companies_in_uae.csv...")
            self._save_companies_to_csv(companies)
            
            # Step 3: Process companies with batch extractor
            print(f"\n🔄 Step 3: Starting executive extraction for {agent_response['companies_found']} companies...")
            
            # Use the JSON data from chat agent
            json_data = agent_response['json_data']
            
            # Process with batch extractor
            self.batch_extractor.run(source='json', json_data=json_data)
            
            print(f"\n🎉 Processing completed successfully!")
            print(f"📁 Check executives.csv and executives_detailed.csv for results")
            
        except KeyboardInterrupt:
            print("\n\n⏹️  Process interrupted by user")
        except Exception as e:
            print(f"\n❌ Error during processing: {e}")
            import traceback
            traceback.print_exc()
    
    def _save_companies_to_csv(self, companies: List[Dict[str, Any]]) -> None:
        """
        Save identified companies to companies_in_uae.csv file
        """
        try:
            import csv
            import os
            from datetime import datetime
            
            filename = "companies_in_uae.csv"
            
            # Check if file exists to determine if we need headers
            file_exists = os.path.exists(filename)
            
            with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['name', 'city', 'country', 'industry', 'source', 'date_added']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write headers if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Add companies with metadata
                for company in companies:
                    company_data = {
                        'name': company.get('name', ''),
                        'city': company.get('city', ''),
                        'country': company.get('country', ''),
                        'industry': company.get('industry', ''),
                        'source': 'chat_agent',
                        'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    writer.writerow(company_data)
            
            print(f"✅ Successfully saved {len(companies)} companies to {filename}")
            
        except Exception as e:
            print(f"❌ Error saving companies to CSV: {e}")

    def _get_user_input(self) -> str:
        """
        Get natural language query from user
        """
        print("\n🤖 Welcome to Professional Investor Leads Generator!")
        print("I can help you find CXO-level executives from companies.")
        print("\n💬 Enter your request in natural language:")
        print("Examples:")
        print("  - 'Find CXOs of Emirates NBD'")
        print("  - 'Top 10 technology companies in UAE'")
        print("  - 'Listed companies in Dubai'")
        print("  - 'Banking executives in Abu Dhabi'")
        print("  - 'Energy sector companies in UAE'")
        print("  - 'Find executives from Apple and Microsoft'")
        print()
        
        while True:
            try:
                user_input = input("Your request: ").strip()
                if user_input:
                    print(f"\n🤖 You asked: {user_input}")
                    return user_input
                else:
                    print("Please enter a valid request.")
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                sys.exit(0)
    
    def run_demo(self):
        """
        Run with a demo query
        """
        demo_query = "Find CXOs of Apple and Microsoft"
        print(f"🎯 Running demo with query: {demo_query}")
        self.run(demo_query)

def main():
    """
    Main entry point
    """
    scraper = ProfessionalInvestorLeadsGenerator()
    
    # Check command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == '--demo':
            scraper.run_demo()
        else:
            print("Usage:")
            print("  python main.py        # Interactive mode")
            print("  python main.py --demo # Demo mode")
    else:
        # Run in interactive mode
        scraper.run()

if __name__ == "__main__":
    main() 