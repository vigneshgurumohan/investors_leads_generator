#!/usr/bin/env python3
"""
CXO Executive Scraper Web UI
FastAPI-based web interface for the executive scraper
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

import pandas as pd
from fastapi import FastAPI, Request, Form, UploadFile, File, WebSocket, WebSocketDisconnect, Body
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from main import ProfessionalInvestorLeadsGenerator
from batch_extractor import BatchExtractor
from chat_agent import ProfessionalInvestorAgent
from config import BATCH_CONFIG
from data_exporter import DataExporter

# Initialize FastAPI app
app = FastAPI(title="CXO Executive Scraper", version="1.0.0")

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Global variables for real-time updates
active_connections: List[WebSocket] = []
scraper_instance = None
batch_instance = None
chat_agent_instance = None

class SearchRequest(BaseModel):
    query: str

class ChatAgentRequest(BaseModel):
    query: str

class BatchRequest(BaseModel):
    source: str = "csv"  # "csv" or "json"
    json_data: Optional[str] = None  # JSON string for chat agent input

class ConfigUpdate(BaseModel):
    target_executives_per_company: int
    max_results_per_query: int
    delay_between_queries: int
    delay_between_companies: int
    enable_early_termination: bool
    enable_duplicate_prevention: bool

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page with upload/chat options"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/records", response_class=HTMLResponse)
async def records_page(request: Request):
    """Records page showing all extracted executives"""
    return templates.TemplateResponse("records.html", {"request": request})

@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/api/records")
async def get_records(
    company: Optional[str] = None,
    position: Optional[str] = None,
    has_email: Optional[bool] = None,
    has_linkedin: Optional[bool] = None,
    limit: int = 100
):
    """Get executives records with filters"""
    try:
        if not os.path.exists("executives.csv"):
            return {"records": [], "total": 0}
        
        # Read CSV with error handling
        try:
            df = pd.read_csv("executives.csv", encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv("executives.csv", encoding='latin-1')
        except Exception as e:
            print(f"Error reading CSV: {e}")
            return {"error": f"Error reading CSV file: {str(e)}", "records": [], "total": 0}
        
        # Clean the dataframe to handle JSON serialization issues
        df = df.replace([float('inf'), float('-inf')], None)
        df = df.fillna('')
        
        # Apply filters with error handling
        if company:
            try:
                df = df[df['Company'].str.contains(company, case=False, na=False)]
            except:
                pass  # Skip filter if column doesn't exist or has issues
        if position:
            try:
                df = df[df['Title'].str.contains(position, case=False, na=False)]
            except:
                pass  # Skip filter if column doesn't exist or has issues
        if has_email is not None:
            try:
                if has_email:
                    df = df[df['Email'].notna() & (df['Email'] != '')]
                else:
                    df = df[df['Email'].isna() | (df['Email'] == '')]
            except:
                pass  # Skip filter if column doesn't exist or has issues
        if has_linkedin is not None:
            try:
                if has_linkedin:
                    df = df[df['LinkedIn'].notna() & (df['LinkedIn'] != '')]
                else:
                    df = df[df['LinkedIn'].isna() | (df['LinkedIn'] == '')]
            except:
                pass  # Skip filter if column doesn't exist or has issues
        
        # Limit results
        df = df.head(limit)
        
        # Convert to records with proper JSON serialization
        records = []
        for _, row in df.iterrows():
            record = {}
            for col in df.columns:
                value = row[col]
                # Handle NaN and infinite values
                if pd.isna(value) or (isinstance(value, float) and (value == float('inf') or value == float('-inf'))):
                    record[col] = None
                else:
                    record[col] = value
            records.append(record)
        
        return {"records": records, "total": len(records)}
        
    except Exception as e:
        return {"error": str(e), "records": [], "total": 0}

@app.get("/api/config")
async def get_config():
    """Get current configuration"""
    return {
        "target_executives_per_company": BATCH_CONFIG.get('target_executives_per_company', 5),
        "max_results_per_query": BATCH_CONFIG.get('max_results_per_query', 5),
        "delay_between_queries": BATCH_CONFIG.get('delay_between_queries', 2),
        "delay_between_companies": BATCH_CONFIG.get('delay_between_companies', 3),
        "enable_early_termination": BATCH_CONFIG.get('enable_early_termination', True),
        "enable_duplicate_prevention": BATCH_CONFIG.get('enable_duplicate_prevention', True),
        "llm_query_generation": BATCH_CONFIG.get('llm_query_generation', True),
        "quality_threshold": BATCH_CONFIG.get('quality_threshold', 0.7)
    }

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    """Update configuration"""
    try:
        # Update BATCH_CONFIG
        BATCH_CONFIG['target_executives_per_company'] = config.target_executives_per_company
        BATCH_CONFIG['max_results_per_query'] = config.max_results_per_query
        BATCH_CONFIG['delay_between_queries'] = config.delay_between_queries
        BATCH_CONFIG['delay_between_companies'] = config.delay_between_companies
        BATCH_CONFIG['enable_early_termination'] = config.enable_early_termination
        BATCH_CONFIG['enable_duplicate_prevention'] = config.enable_duplicate_prevention
        
        # Save to config file
        save_config_to_file()
        
        return {"success": True, "message": "Configuration updated successfully"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/search")
async def start_search(request: SearchRequest):
    """Start a search operation using chat agent"""
    global scraper_instance
    
    try:
        scraper_instance = ProfessionalInvestorLeadsGenerator()
        
        # Start search in background
        asyncio.create_task(run_search(request.query))
        
        return {"success": True, "message": "Search started", "task_id": "search_1"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/chat-agent")
async def start_chat_agent(request: ChatAgentRequest):
    """Start a chat agent operation"""
    global chat_agent_instance
    
    try:
        chat_agent_instance = ProfessionalInvestorAgent()
        
        # Start chat agent processing in background
        asyncio.create_task(run_chat_agent_processing(request.query))
        
        return {"success": True, "message": "Chat agent started", "task_id": "chat_1"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/batch")
async def start_batch(request: BatchRequest):
    """Start a batch processing operation"""
    global batch_instance
    
    try:
        batch_instance = BatchExtractor()
        
        # Start batch processing in background
        asyncio.create_task(run_batch_processing_json(request.source, request.json_data))
        
        return {"success": True, "message": "Batch processing started", "task_id": "batch_1"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload CSV file for batch processing"""
    try:
        # Save uploaded file
        file_path = f"uploads/{file.filename}"
        os.makedirs("uploads", exist_ok=True)
        
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Start batch processing with CSV source
        asyncio.create_task(run_batch_processing_csv(file_path))
        
        return {"success": True, "message": f"File uploaded and batch processing started: {file.filename}"}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    print(f"[WebSocket Debug] New connection added. Total connections: {len(active_connections)}")
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print(f"[WebSocket Debug] Connection removed. Total connections: {len(active_connections)}")

@app.get("/api/test-websocket")
async def test_websocket():
    """Test endpoint to verify WebSocket functionality"""
    await broadcast_log("🧪 WebSocket test message", "info")
    return {"success": True, "message": "WebSocket test sent", "connections": len(active_connections)}

async def broadcast_log(message: str, log_type: str = "info"):
    """Broadcast log message to all connected WebSocket clients"""
    print(f"[WebSocket Debug] Broadcasting: {message} (type: {log_type})")
    print(f"[WebSocket Debug] Active connections: {len(active_connections)}")
    
    if active_connections:
        message_data = {
            "type": "log",
            "log_type": log_type,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(message_data))
                print(f"[WebSocket Debug] Message sent successfully")
            except Exception as e:
                print(f"[WebSocket Debug] Failed to send message: {e}")
                continue
    else:
        print(f"[WebSocket Debug] No active connections to broadcast to")

async def run_search(query: str):
    """Run search using chat agent with real-time logging"""
    global scraper_instance
    
    try:
        await broadcast_log("🚀 Starting Professional Investor Leads Generator...", "info")
        await broadcast_log(f"📝 Processing query: {query}", "info")
        
        # Use chat agent
        await broadcast_log("🤖 Using AI Chat Agent...", "info")
        
        # Initialize chat agent
        chat_agent = ProfessionalInvestorAgent()
        agent_response = chat_agent.process_user_query(query)
        
        if not agent_response['success']:
            await broadcast_log(f"❌ {agent_response['message']}", "error")
            return
        
        # Display agent's response
        await broadcast_log(agent_response['message'], "success")
        
        # Show identified companies in logs
        await broadcast_log("📋 Companies identified by AI Agent:", "info")
        
        # Parse and display companies
        companies_data = json.loads(agent_response['json_data'])
        companies = companies_data.get('companies', [])
        
        for i, company in enumerate(companies, 1):
            company_info = f"{i:2d}. {company['name']} - {company['city']}, {company['country']} ({company['industry']})"
            await broadcast_log(company_info, "info")
        
        await broadcast_log(f"Total companies found: {len(companies)}", "success")
        
        # Save companies to CSV file
        await broadcast_log("💾 Saving companies to companies_in_uae.csv...", "info")
        await save_companies_to_csv(companies)
        
        # Process with batch extractor
        await broadcast_log(f"🔄 Starting executive extraction for {agent_response['companies_found']} companies...", "info")
        
        # Use the JSON data from chat agent
        json_data = agent_response['json_data']
        
        # Initialize batch extractor and process
        batch_instance = BatchExtractor()
        batch_instance.run(source='json', json_data=json_data)
        
        await broadcast_log("🎉 Processing completed!", "success")
        await broadcast_log("📁 Check executives.csv and executives_detailed.csv for results", "info")
        
    except Exception as e:
        await broadcast_log(f"❌ Error during processing: {str(e)}", "error")



async def run_batch_processing_json(source: str, json_data: str = None):
    """Run batch processing for JSON input (chat agent) or CSV"""
    global batch_instance
    
    try:
        await broadcast_log("🚀 Starting enhanced batch processing...", "info")
        
        # Initialize batch extractor
        batch_instance = BatchExtractor()
        
        # Load companies from specified source
        if source == 'json' and json_data:
            companies = batch_instance.load_companies_from_json(json_data)
            await broadcast_log(f"📊 Loaded {len(companies)} companies from JSON (chat agent)", "info")
        else:
            companies = batch_instance.load_companies_from_csv()
            await broadcast_log(f"📊 Loaded {len(companies)} companies from CSV", "info")
        
        if not companies:
            await broadcast_log("❌ No companies found", "error")
            return
        
        # Process companies
        all_executives = []
        processed_count = 0
        
        for i, company in enumerate(companies):
            try:
                await broadcast_log(f"Processing company {i+1}/{len(companies)}: {company['name']}", "info")
                
                # Process company
                company_executives = batch_instance.process_single_company(company)
                all_executives.extend(company_executives)
                
                processed_count += 1
                await broadcast_log(f"✅ Processed {company['name']}: {len(company_executives)} executives found", "success")
                
                # Delay between companies
                if i < len(companies) - 1:
                    await asyncio.sleep(BATCH_CONFIG['delay_between_companies'])
                
            except Exception as e:
                await broadcast_log(f"❌ Error processing {company['name']}: {e}", "error")
                continue
        
        # Export results
        if all_executives:
            await broadcast_log(f"💾 Exporting {len(all_executives)} executives...", "info")
            
            # Export to CSV
            csv_file = batch_instance.data_exporter.export_to_csv(all_executives, append_mode=True, batch_mode=True)
            detailed_csv = batch_instance.data_exporter.export_detailed_csv(all_executives, append_mode=True, batch_mode=True)
            
            # Generate summary
            summary = batch_instance.data_exporter.generate_summary_report(all_executives)
            
            await broadcast_log(f"🎉 Enhanced batch processing completed!", "success")
            await broadcast_log(f"📁 Files created: {csv_file}, {detailed_csv}", "info")
            
            # Broadcast results
            await broadcast_results(all_executives)
        else:
            await broadcast_log("❌ No executives found during batch processing", "warning")
            
    except Exception as e:
        await broadcast_log(f"❌ Enhanced batch processing error: {e}", "error")

async def run_batch_processing_csv(file_path: str):
    """Run batch processing for uploaded CSV file"""
    global batch_instance
    
    try:
        await broadcast_log("🚀 Starting CSV batch processing...", "info")
        await broadcast_log(f"📁 Processing file: {file_path}", "info")
        
        # Initialize batch extractor
        batch_instance = BatchExtractor()
        
        # Load companies from the uploaded CSV file using data loader
        data_loader = batch_instance.data_loader
        try:
            data = data_loader.load_from_csv(file_path)
            companies = data['companies']
            await broadcast_log(f"📊 Loaded {len(companies)} companies from uploaded CSV", "info")
        except Exception as e:
            await broadcast_log(f"❌ Error loading CSV file: {e}", "error")
            return
        
        if not companies:
            await broadcast_log("❌ No companies found in CSV file", "error")
            return
        
        # Process companies
        all_executives = []
        processed_count = 0
        
        for i, company in enumerate(companies):
            try:
                await broadcast_log(f"Processing company {i+1}/{len(companies)}: {company['name']}", "info")
                
                # Process company
                company_executives = batch_instance.process_single_company(company)
                all_executives.extend(company_executives)
                
                processed_count += 1
                await broadcast_log(f"✅ Processed {company['name']}: {len(company_executives)} executives found", "success")
                
                # Delay between companies
                if i < len(companies) - 1:
                    await asyncio.sleep(BATCH_CONFIG['delay_between_companies'])
                
            except Exception as e:
                await broadcast_log(f"❌ Error processing {company['name']}: {e}", "error")
                continue
        
        # Export results
        if all_executives:
            await broadcast_log(f"💾 Exporting {len(all_executives)} executives...", "info")
            
            # Export to CSV
            csv_file = batch_instance.data_exporter.export_to_csv(all_executives, append_mode=True, batch_mode=True)
            detailed_csv = batch_instance.data_exporter.export_detailed_csv(all_executives, append_mode=True, batch_mode=True)
            
            # Generate summary
            summary = batch_instance.data_exporter.generate_summary_report(all_executives)
            
            await broadcast_log(f"🎉 CSV batch processing completed!", "success")
            await broadcast_log(f"📁 Files created: {csv_file}, {detailed_csv}", "info")
            
            # Broadcast results
            await broadcast_results(all_executives)
        else:
            await broadcast_log("❌ No executives found during CSV batch processing", "warning")
            
    except Exception as e:
        await broadcast_log(f"❌ CSV batch processing error: {e}", "error")

async def run_chat_agent_processing(user_query: str):
    """Run chat agent processing with real-time updates"""
    global chat_agent_instance, batch_instance
    
    try:
        await broadcast_log("🤖 Starting Professional Investor Leads Generator...", "info")
        await broadcast_log(f"📝 Processing your request: {user_query}", "info")
        
        # Initialize chat agent
        chat_agent_instance = ProfessionalInvestorAgent()
        
        # Step 1: Analyze query and find companies
        await broadcast_log("🔍 Step 1: AI Agent analyzing your query and researching companies...", "info")
        agent_response = chat_agent_instance.process_user_query(user_query)
        
        if not agent_response['success']:
            await broadcast_log(f"❌ {agent_response['message']}", "error")
            return
        
        # Display agent's response
        await broadcast_log(agent_response['message'], "success")
        
        # Step 2: Process companies with batch extractor
        await broadcast_log(f"🔄 Step 2: Starting executive extraction for {agent_response['companies_found']} companies...", "info")
        
        # Use the JSON data from chat agent
        json_data = agent_response['json_data']
        
        # Initialize batch extractor and process
        batch_instance = BatchExtractor()
        batch_instance.run(source='json', json_data=json_data)
        
        await broadcast_log("🎉 Chat agent processing completed successfully!", "success")
        await broadcast_log("📁 Check executives.csv and executives_detailed.csv for results", "info")
        
    except Exception as e:
        await broadcast_log(f"❌ Chat agent processing error: {e}", "error")

async def save_companies_to_csv(companies: List[Dict[str, Any]]) -> None:
    """Save identified companies to companies_in_uae.csv file"""
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
        
        # Save silently without logging
        
    except Exception as e:
        await broadcast_log(f"❌ Error saving companies to CSV: {e}", "error")

async def broadcast_results(executives: List[Dict[str, Any]]):
    """Broadcast search results to WebSocket clients"""
    if active_connections:
        results_data = {
            "type": "results",
            "executives": executives,
            "count": len(executives),
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(results_data))
            except:
                continue

async def broadcast_companies(companies: List[Dict[str, Any]]):
    """Broadcast companies to WebSocket clients"""
    if active_connections:
        companies_data = {
            "type": "companies",
            "companies": companies,
            "count": len(companies),
            "timestamp": datetime.now().isoformat()
        }
        
        for connection in active_connections:
            try:
                await connection.send_text(json.dumps(companies_data))
            except:
                continue

@app.post("/api/extract-basic")
async def extract_basic_contacts(request: SearchRequest):
    """Extract companies and basic executive info (no enrichment)"""
    try:
        await broadcast_log("🚀 Starting search...", "info")
        chat_agent = ProfessionalInvestorAgent()
        agent_response = chat_agent.process_user_query(request.query)
        if not agent_response['success']:
            await broadcast_log(f"❌ {agent_response['message']}", "error")
            return {"success": False, "error": agent_response['message']}
        
        companies_data = json.loads(agent_response['json_data'])
        companies = companies_data.get('companies', [])
        
        # Broadcast companies to WebSocket clients
        await broadcast_companies(companies)
        
        # Show company identification first
        for company in companies:
            company_name = company.get('name', '')
            await broadcast_log(f"🏢 Company identified: {company_name}", "info")
        
        # Save companies to CSV (silently, no log message)
        await save_companies_to_csv(companies)
        
        # Extract basic executives for each company (no enrichment)
        import config
        from executive_extractor import ExecutiveExtractor
        from serpapi_searcher import SerpAPISearcher
        from content_scraper import ContentScraper
        from batch_extractor import BatchExtractor
        
        searcher = SerpAPISearcher()
        scraper = ContentScraper()
        extractor = ExecutiveExtractor()
        batch_extractor = BatchExtractor()  # Use BatchExtractor for query generation
        
        all_executives = []
        
        for company in companies:
            company_name = company.get('name', '')
            await broadcast_log(f"🔍 Searching for executives from {company_name}...", "info")
            
            # Generate search queries for this company using BatchExtractor
            await broadcast_log(f"🔍 Generating search queries for {company_name}...", "info")
            queries = batch_extractor.generate_company_queries(company)
            
            company_executives = []
            max_retries = config.BATCH_CONFIG.get('max_retry_attempts', 3)
            retry_delay = config.BATCH_CONFIG.get('retry_delay_seconds', 2)
            
            # Try each query with retry logic
            for query_index, query in enumerate(queries[:max_retries]):
                if company_executives:  # If we found executives, no need to continue
                    break
                    
                await broadcast_log(f"🎯 Attempt {query_index + 1}/{max_retries}: {query[:60]}...", "info")
                
                # Search for articles with limited results
                search_results = searcher.search_google(query, max_results=5)  # Increased to 5 for better coverage
                
                # Broadcast found results to show progress
                for result in search_results:
                    title = result.get('title', '')[:50]
                    await broadcast_log(f"✅ Found: {title}...", "info")
                
                if not search_results:
                    await broadcast_log(f"⚠️ No search results for attempt {query_index + 1}, trying next query...", "warning")
                    continue
                
                # Extract content from search results with size filtering
                await broadcast_log(f"📄 Analyzing content from {len(search_results)} sources...", "info")
                articles = []
                for i, result in enumerate(search_results):
                    try:
                        await broadcast_log(f"📄 Processing source {i+1}/{len(search_results)}...", "info")
                        article = scraper.process_single_article(result['url'])
                        if article and len(article.get('text', '')) < 50000:  # Skip very large content
                            articles.append(article)
                            await broadcast_log(f"✅ Source {i+1} processed successfully", "success")
                            if len(articles) >= 3:  # Increased to 3 articles for better coverage
                                break
                    except Exception as e:
                        await broadcast_log(f"❌ Unable to process source {i+1}: {str(e)[:50]}...", "error")
                        continue
                
                if not articles:
                    await broadcast_log(f"⚠️ No articles processed for attempt {query_index + 1}, trying next query...", "warning")
                    continue
                
                # Extract basic executives from articles with reduced target
                await broadcast_log(f"🤖 Analyzing executive information from {len(articles)} sources...", "info")
                # Temporarily override target for basic extraction
                original_target = config.BATCH_CONFIG.get('target_executives_per_company', 5)
                config.BATCH_CONFIG['target_executives_per_company'] = 3  # Reduce target for speed
                
                executives = extractor.extract_executives_basic_from_articles(articles)
                
                # Restore original target
                config.BATCH_CONFIG['target_executives_per_company'] = original_target
                
                if executives:
                    company_executives.extend(executives)
                    await broadcast_log(f"✅ Executives found: {len(executives)} from {company_name} (attempt {query_index + 1})", "success")
                    break
                else:
                    await broadcast_log(f"⚠️ No executives found in attempt {query_index + 1}, retrying...", "warning")
                    if query_index < max_retries - 1:  # Don't delay on the last attempt
                        await asyncio.sleep(retry_delay)
            
            if not company_executives:
                await broadcast_log(f"❌ No executives found for {company_name} after {max_retries} attempts", "error")
            else:
                all_executives.extend(company_executives)
                await broadcast_log(f"🎉 Successfully extracted {len(company_executives)} executives from {company_name}", "success")
        
        await broadcast_log(f"🎉 Total executives extracted: {len(all_executives)}", "success")
        await broadcast_results(all_executives)
        return {"success": True, "executives": all_executives, "companies": companies}
        
    except Exception as e:
        await broadcast_log(f"❌ Error in basic extraction: {e}", "error")
        return {"success": False, "error": str(e)}

@app.post("/api/enrich-contacts")
async def enrich_contacts(executives: list = Body(...)):
    """Enrich basic contacts with LinkedIn/email and save to CSV"""
    try:
        await broadcast_log("🔍 Starting enrichment of contacts...", "info")
        batch = BatchExtractor()
        enriched = batch.executive_extractor._enrich_executives(executives)
        # Save to CSV
        exporter = DataExporter()
        exporter.export_to_csv(enriched, append_mode=True, batch_mode=True)
        await broadcast_log(f"✅ Enriched and saved {len(enriched)} contacts.", "success")
        await broadcast_results(enriched)
        return {"success": True, "executives": enriched}
    except Exception as e:
        await broadcast_log(f"❌ Error in enrichment: {e}", "error")
        return {"success": False, "error": str(e)}

@app.post("/api/save-basic-contacts")
async def save_basic_contacts(executives: list = Body(...)):
    """Save basic contacts to CSV (no enrichment)"""
    try:
        exporter = DataExporter()
        exporter.export_to_csv(executives, append_mode=True, batch_mode=True)
        await broadcast_log(f"✅ Saved {len(executives)} basic contacts to CSV.", "success")
        return {"success": True}
    except Exception as e:
        await broadcast_log(f"❌ Error saving basic contacts: {e}", "error")
        return {"success": False, "error": str(e)}

def save_config_to_file():
    """Save configuration to config.py file"""
    # Import current config to preserve API keys
    import config
    
    config_content = f'''import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
OPENAI_API_KEY = "{config.OPENAI_API_KEY}"
SERPAPI_KEY = "{config.SERPAPI_KEY}"


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
SCRAPING_CONFIG = {{
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
}}

# Output Configuration
OUTPUT_CONFIG = {{
    'csv_filename': 'executives.csv',
    'columns': ['Name', 'Title', 'Company', 'LinkedIn', 'Email', 'Source URL', 'Extraction Date']
}}

# Batch Processing Configuration
BATCH_CONFIG = {{
    'companies_csv_file': 'companies_in_uae.csv',
    'progress_file': 'batch_progress.json',
    'log_file': 'batch_logs.txt',
    'country_filter': 'UAE',
    'max_results_per_company': 5,
    'delay_between_companies': {BATCH_CONFIG.get('delay_between_companies', 3)},
    'delay_between_queries': {BATCH_CONFIG.get('delay_between_queries', 2)},
    'max_retries_per_company': 2,
    'recent_days_threshold': 7,
    'batch_mode_flag': 'Yes',
    'llm_company_matching': True,
    'llm_query_generation': {BATCH_CONFIG.get('llm_query_generation', True)},
    'log_level': 'INFO',
    
    # Smart optimization settings
    'target_executives_per_company': {BATCH_CONFIG.get('target_executives_per_company', 5)},
    'max_results_per_query': {BATCH_CONFIG.get('max_results_per_query', 5)},
    'enable_early_termination': {BATCH_CONFIG.get('enable_early_termination', True)},
    'enable_duplicate_prevention': {BATCH_CONFIG.get('enable_duplicate_prevention', True)},
    'quality_threshold': {BATCH_CONFIG.get('quality_threshold', 0.7)}
}}
'''
    
    with open("config.py", "w") as f:
        f.write(config_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 