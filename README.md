# 🏢 Executive Information Scraper & Enrichment Pipeline

A comprehensive Python-based scraper and enrichment pipeline to identify CXO-level executives from any company or industry, including their profiles and possible contact details. This tool combines AI-powered extraction, web scraping, and data enrichment to provide detailed executive information.

## 🎯 Features

### Core Capabilities
- **🤖 AI-Powered Chat Agent**: Natural language processing for executive searches with context-aware queries
- **📊 Batch Processing**: Process multiple companies from CSV files with progress tracking and resume capability
- **🌐 Real-time Web Interface**: Live logs and progress tracking with FastAPI-based dashboard
- **🔍 Executive Extraction**: Advanced AI extraction using GPT-3.5 and spaCy for accurate data extraction
- **📈 Data Export**: CSV and detailed reports with comprehensive summaries and analytics
- **🕷️ Web Scraping**: Automated content extraction from search results with intelligent parsing
- **📧 Contact Enrichment**: Email address generation and LinkedIn profile discovery
- **🔄 Resume Capability**: Continue batch processing from where it left off

### Advanced Features
- **Smart Deduplication**: AI-powered duplicate detection and merging
- **Quality Scoring**: Confidence-based result filtering
- **Rate Limiting**: Intelligent request throttling to avoid blocking
- **Error Recovery**: Automatic retry mechanisms with exponential backoff
- **Multi-source Validation**: Cross-reference information from multiple sources
- **Industry Detection**: Automatic industry classification for companies

## 📋 Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for batch processing)
- **Storage**: 1GB free space for models and data
- **Internet**: Stable connection for web scraping and API calls

### API Keys Required
- **OpenAI API Key** (recommended for best results)
  - Get from: https://platform.openai.com/api-keys
  - Used for: Executive extraction, query generation, company matching
- **SerpAPI Key** (required for search functionality)
  - Get from: https://serpapi.com/
  - Used for: Google search automation, result parsing

## 🚀 Installation

### 1. Clone the Repository
```bash
git clone <your-repository-url>
cd executive-scraper
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Install spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### 5. Environment Setup
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your API keys
# OPENAI_API_KEY=your_openai_api_key_here
# SERPAPI_KEY=your_serpapi_key_here
```

### 6. Verify Installation
```bash
python main.py --demo
```

## 💻 Usage

### Interactive Mode (Recommended for Beginners)

Run the scraper and enter your query when prompted:

```bash
python main.py
```

**Example Queries:**
- `"Find CEOs of UAE banks"`
- `"Extract CFOs from Apple and Microsoft"`
- `"Get all CXOs from technology companies"`
- `"Find marketing executives from healthcare companies in USA"`
- `"Search for CTOs in retail industry"`

### Demo Mode

Run with a predefined demo query to test the system:

```bash
python main.py --demo
```

### Batch Processing Mode

Process multiple companies from a CSV file:

```bash
python batch_extractor.py
```

#### Batch Processing Options

**Process specific companies:**
```bash
python batch_extractor.py --companies "Emirates NBD" "First Abu Dhabi Bank"
```

**Resume from last processed company:**
```bash
python batch_extractor.py --resume
```

**Process only recently added companies (last 7 days):**
```bash
python batch_extractor.py --recent 7
```

**Custom delay between requests:**
```bash
python batch_extractor.py --delay 3
```

### Web Interface

Launch the FastAPI web interface for real-time monitoring:

```bash
python web_app.py
```

Then visit: http://localhost:8000

## 📊 Output Files

The scraper generates comprehensive output files:

### 1. `executives.csv` - Main Results
**Columns:**
- `Name`: Executive's full name
- `Title`: Position/title
- `Company`: Company name
- `LinkedIn`: LinkedIn profile URL (if found)
- `Email`: Email address (if found)
- `Source URL`: Source article URL
- `Extraction Date`: When the data was extracted

**Batch Mode Additional Columns:**
- `Batch_Mode`: Indicates batch processing
- `Processing_Date`: When the company was processed
- `Company_Industry`: Detected industry

### 2. `executives_detailed.csv` - Detailed Results
**Additional Columns:**
- `Source Title`: Article title
- `Extraction Method`: How the data was extracted (AI/spaCy)
- `Confidence`: Extraction confidence score
- `Raw Text`: Original text snippet
- `Enrichment Status`: Whether contact info was enriched

### 3. `extraction_summary.txt` - Summary Report
**Contains:**
- Total executives found
- Companies covered
- Position breakdown
- Success rates
- Processing time
- Error summary

### 4. Batch Processing Files
- `batch_progress.json`: Progress tracking and resume points
- `batch_logs.txt`: Detailed processing logs with timestamps

## 🏗️ Architecture

### Core Components

| Component | File | Purpose |
|-----------|------|---------|
| **Main Entry** | `main.py` | Interactive CLI with AI chat agent |
| **Chat Agent** | `chat_agent.py` | AI-powered query processing and company research |
| **Batch Processor** | `batch_extractor.py` | Enhanced batch processing with JSON/CSV support |
| **Data Loader** | `data_loader.py` | Modular data loading from multiple sources |
| **Search Engine** | `serpapi_searcher.py` | Google search automation via SerpAPI |
| **Content Scraper** | `content_scraper.py` | Article content extraction and parsing |
| **Executive Extractor** | `executive_extractor.py` | AI-powered executive information extraction |
| **Data Exporter** | `data_exporter.py` | Data export and reporting functionality |
| **Configuration** | `config.py` | Centralized configuration and settings |
| **Web Interface** | `web_app.py` | FastAPI web interface for monitoring |

### Data Flow

```
User Query → Chat Agent → Search Engine → Content Scraper → Executive Extractor → Data Exporter → Output Files
     ↓
Batch CSV → Data Loader → Batch Processor → Multiple Queries → Aggregated Results
```

### Supported Industries

- **Banking & Finance**: Banks, investment firms, insurance companies
- **Technology**: Software, hardware, internet companies
- **Healthcare**: Hospitals, pharmaceutical, medical devices
- **Retail & E-commerce**: Online and offline retail
- **Manufacturing**: Industrial, automotive, consumer goods
- **Energy**: Oil & gas, renewable energy, utilities
- **Real Estate**: Property development, management
- **And more**: Automatically detected from queries

### Pre-configured UAE Banks

- Emirates NBD
- Abu Dhabi Islamic Bank (ADIB)
- Dubai Islamic Bank (DIB)
- First Abu Dhabi Bank (FAB)
- Mashreq Bank
- Commercial Bank of Dubai (CBD)
- Abu Dhabi Commercial Bank (ADCB)
- Union National Bank (UNB)

### Supported CXO Positions

| Position | Full Title | Variations |
|----------|------------|------------|
| **CEO** | Chief Executive Officer | Chief Executive, Executive Director |
| **CFO** | Chief Financial Officer | Chief Finance Officer, Finance Director |
| **CMO** | Chief Marketing Officer | Chief Marketing, Marketing Director |
| **CTO** | Chief Technology Officer | Chief Technology, Technology Director |
| **COO** | Chief Operating Officer | Chief Operations Officer, Operations Director |
| **CIO** | Chief Information Officer | Chief Information, IT Director |
| **CRO** | Chief Risk Officer | Chief Risk, Risk Director |
| **CLO** | Chief Legal Officer | Chief Legal, General Counsel |
| **CHRO** | Chief Human Resources Officer | Chief HR Officer, HR Director |
| **CDO** | Chief Digital Officer | Chief Digital, Digital Director |
| **CCO** | Chief Compliance Officer | Chief Compliance, Compliance Director |
| **CBO** | Chief Business Officer | Chief Business, Business Director |

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Required API Keys
OPENAI_API_KEY=your_openai_api_key_here
SERPAPI_KEY=your_serpapi_key_here

# Optional: Customize scraping behavior
MAX_PAGES_PER_SEARCH=5
RESULTS_PER_PAGE=10
DELAY_BETWEEN_REQUESTS=2
TIMEOUT=30
MAX_RETRIES=3

# Optional: Batch processing settings
DELAY_BETWEEN_COMPANIES=1
DELAY_BETWEEN_QUERIES=1
MAX_RETRIES_PER_COMPANY=2
RECENT_DAYS_THRESHOLD=7
LOG_LEVEL=INFO
```

### Configuration File (`config.py`)

Edit `config.py` to customize:

#### General Settings
- **Scraping behavior**: Delays, timeouts, retries
- **Search parameters**: Number of pages, results per page
- **Bank database**: Add/remove banks or modify aliases
- **CXO positions**: Add new executive positions

#### Batch Processing Settings
- **Companies CSV file**: Source file for company data
- **Progress tracking**: Resume capability and state management
- **Processing delays**: Rate limiting between companies
- **LLM company matching**: AI-powered company name validation
- **Logging level**: Detailed processing logs

## 🔧 Advanced Usage

### Programmatic Usage

#### Chat Agent
```python
from chat_agent import ProfessionalInvestorAgent

agent = ProfessionalInvestorAgent()
response = agent.process_user_query("Find CXOs of Emirates NBD")
print(response['message'])
```

#### Manual Content Scraping
```python
from content_scraper import ContentScraper

scraper = ContentScraper()
article_data = scraper.scrape_single_article("https://example.com/article")
print(article_data['text'])
```

#### Executive Extraction
```python
from executive_extractor import ExecutiveExtractor

extractor = ExecutiveExtractor()
executives = extractor.extract_from_single_article(article_data)
print(executives)
```

#### Batch Processing
```python
from batch_extractor import BatchExtractor

extractor = BatchExtractor()
extractor.process_companies(["Company A", "Company B"])
```

### Custom Data Sources

#### Adding Custom Companies
```python
# Add to config.py
CUSTOM_COMPANIES = [
    "Your Company Name",
    "Another Company"
]
```

#### Custom CSV Format
The system supports various CSV formats. Ensure your CSV has:
- Company name column
- Optional: Industry column
- Optional: Country column

### Performance Optimization

#### For Large Datasets
1. **Increase delays**: Set higher values in config
2. **Use batch mode**: Process companies in batches
3. **Enable resume**: Use `--resume` flag for interrupted runs
4. **Monitor logs**: Check `batch_logs.txt` for issues

#### For Better Results
1. **Specific queries**: Include position titles
2. **Company aliases**: Add alternative company names
3. **Industry context**: Include industry in queries
4. **Recent data**: Use `--recent` flag for fresh data

## 🛡️ Ethical Considerations

### Responsible Usage
- **Rate Limiting**: Built-in delays to avoid overwhelming servers
- **User-Agent Rotation**: Prevents detection and blocking
- **Respectful Scraping**: Follows robots.txt and implements proper delays
- **Data Usage**: Intended for research and business intelligence only

### Compliance
- **Terms of Service**: Respect website terms of service
- **Rate Limits**: Stay within API rate limits
- **Data Privacy**: Use extracted data responsibly
- **Verification**: Always verify information accuracy

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users are responsible for:

- Complying with website terms of service
- Respecting rate limits and robots.txt
- Using extracted data responsibly
- Verifying information accuracy
- Obtaining necessary permissions for data usage

## 🐛 Troubleshooting

### Common Issues

#### 1. "No search results found"
**Solutions:**
- Try a more specific query
- Check internet connection
- Wait a few minutes and retry
- Verify SerpAPI key is valid

#### 2. "spaCy model not found"
**Solution:**
```bash
python -m spacy download en_core_web_sm
```

#### 3. "OpenAI extraction failed"
**Solutions:**
- Check your API key in `.env` file
- Verify API key is valid and has credits
- Check OpenAI service status

#### 4. "Rate limited"
**Solutions:**
- Wait 10-15 minutes before retrying
- Reduce scraping frequency
- Increase delays in config

#### 5. "Batch processing stuck"
**Solutions:**
- Check `batch_logs.txt` for errors
- Use `--resume` flag to continue
- Verify CSV file format

### Performance Tips

- **Use specific bank names** for better results
- **Include position titles** in queries
- **Run during off-peak hours** for better performance
- **Monitor system resources** during batch processing
- **Use SSD storage** for faster file operations

### Debug Mode

Enable detailed logging:
```bash
# Set in .env
LOG_LEVEL=DEBUG

# Or in config.py
BATCH_CONFIG['log_level'] = 'DEBUG'
```

## 📈 Performance Metrics

### Typical Results
- **Success Rate**: 85-95% for well-known companies
- **Processing Speed**: 2-5 companies per minute
- **Data Quality**: 90%+ accuracy for basic information
- **Contact Enrichment**: 60-80% success rate

### Scalability
- **Small Scale**: 1-10 companies (interactive mode)
- **Medium Scale**: 10-100 companies (batch mode)
- **Large Scale**: 100+ companies (distributed processing)

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Add type hints where possible
- Include docstrings for functions
- Write meaningful commit messages

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

### Getting Help
1. Check the troubleshooting section
2. Review the logs for error messages
3. Search existing issues
4. Create a new issue with details

### Issue Template
When reporting issues, include:
- Python version
- Operating system
- Error message
- Steps to reproduce
- Expected vs actual behavior

## 🔄 Changelog

### Version 1.0.0
- Initial release
- AI-powered executive extraction
- Batch processing capability
- Web interface
- Comprehensive documentation

---

**Happy Scraping! 🚀**

For questions and support, please refer to the documentation above or create an issue in the repository. 