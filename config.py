import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
SERPAPI_KEY = os.getenv('SERPAPI_KEY')


# CXO Positions
CXO_POSITIONS = [
    'CEO', 'Chief Executive Officer', 'Chief Executive',
    'CFO', 'Chief Financial Officer', 'Chief Finance Officer',
    'CMO', 'Chief Marketing Officer', 'Chief Marketing',
    'CTO', 'Chief Technology Officer', 'Chief Technology',
    'COO', 'Chief Operating Officer', 'Chief Operations Officer',
    'CIO', 'Chief Information Officer', 'Chief Information',
    'CRO', 'Chief Risk Officer', 'Chief Risk',
    'CLO', 'Chief Legal Officer', 'Chief Legal',
    'CHRO', 'Chief Human Resources Officer', 'Chief HR Officer',
    'CDO', 'Chief Digital Officer', 'Chief Digital',
    'CCO', 'Chief Compliance Officer', 'Chief Compliance',
    'CBO', 'Chief Business Officer', 'Chief Business'
]

# Scraping Configuration
SCRAPING_CONFIG = {
    'max_pages_per_search': 5,
    'results_per_page': 10,
    'delay_between_requests': 2,
    'timeout': 30,
    'max_retries': 3,
    'user_agents': [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
}

# Output Configuration
OUTPUT_CONFIG = {
    'csv_filename': 'executives.csv',
    'columns': ['Name', 'Title', 'Company', 'LinkedIn', 'Email', 'Source URL', 'Extraction Date']
}

# Batch Processing Configuration
BATCH_CONFIG = {
    'companies_csv_file': 'companies_in_uae.csv',
    'progress_file': 'batch_progress.json',
    'log_file': 'batch_logs.txt',
    'country_filter': 'UAE',
    'max_results_per_company': 5,
    'delay_between_companies': 1,
    'delay_between_queries': 1,
    'max_retries_per_company': 2,
    'recent_days_threshold': 7,
    'batch_mode_flag': 'Yes',
    'llm_company_matching': True,
    'llm_query_generation': True,
    'log_level': 'INFO',
    
    # Smart optimization settings
    'target_executives_per_company': 5,
    'max_results_per_query': 5,
    'enable_early_termination': True,
    'enable_duplicate_prevention': True,
    'quality_threshold': 0.7,
    
    # Retry settings for executive extraction
    'max_retry_attempts': 3,
    'retry_delay_seconds': 2,
    'enable_retry_on_zero_executives': True
}
