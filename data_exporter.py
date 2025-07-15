import pandas as pd
from datetime import datetime
from typing import List, Dict, Any
from config import OUTPUT_CONFIG, BATCH_CONFIG

class DataExporter:
    def __init__(self):
        self.columns = OUTPUT_CONFIG['columns']
        self.filename = OUTPUT_CONFIG['csv_filename']
        self.batch_mode_flag = BATCH_CONFIG['batch_mode_flag']
    
    def export_to_csv(self, executives: List[Dict[str, Any]], filename: str = None, append_mode: bool = False, batch_mode: bool = False) -> str:
        """
        Export executive data to CSV file
        """
        if filename is None:
            filename = self.filename
        
        # Prepare data for CSV
        csv_data = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for executive in executives:
            row = {
                'Name': executive.get('name', ''),
                'Title': executive.get('title', ''),
                'Company': executive.get('company', '') or executive.get('bank', ''),  # Handle both 'company' and 'bank' fields
                'LinkedIn': executive.get('linkedin', ''),
                'Email': executive.get('email', ''),
                'Source URL': executive.get('source_url', ''),
                'Extraction Date': current_date
            }
            
            # Add batch mode columns if in append mode
            if append_mode:
                row.update({
                    'Batch_Mode': self.batch_mode_flag if batch_mode else '',
                    'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Company_Industry': executive.get('company_industry', '')
                })
            
            csv_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(csv_data)
        
        if append_mode:
            # Append to existing file
            try:
                existing_df = pd.read_csv(filename)
                # Add batch columns if they don't exist
                if 'Batch_Mode' not in existing_df.columns:
                    existing_df['Batch_Mode'] = 'No'
                if 'Processing_Date' not in existing_df.columns:
                    existing_df['Processing_Date'] = ''
                if 'Company_Industry' not in existing_df.columns:
                    existing_df['Company_Industry'] = ''
                
                # Combine existing and new data
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✅ Appended {len(executives)} executives to {filename}")
            except FileNotFoundError:
                # File doesn't exist, create new
                df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✅ Created new file {filename} with {len(executives)} executives")
        else:
            # Overwrite existing file
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Exported {len(executives)} executives to {filename}")
        
        return filename
    
    def export_detailed_csv(self, executives: List[Dict[str, Any]], filename: str = None, append_mode: bool = False, batch_mode: bool = False) -> str:
        """
        Export detailed executive data with additional fields
        """
        if filename is None:
            filename = 'executives_detailed.csv'
        
        # Prepare detailed data
        detailed_data = []
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        for executive in executives:
            row = {
                'Name': executive.get('name', ''),
                'Title': executive.get('title', ''),
                'Company': executive.get('company', '') or executive.get('bank', ''),  # Handle both 'company' and 'bank' fields
                'LinkedIn': executive.get('linkedin', ''),
                'Email': executive.get('email', ''),
                'Source URL': executive.get('source_url', ''),
                'Source Title': executive.get('source_title', ''),
                'Extraction Method': executive.get('extraction_method', ''),
                'Confidence': executive.get('confidence', ''),
                'Extraction Date': current_date
            }
            
            # Add batch mode columns if in append mode
            if append_mode:
                row.update({
                    'Batch_Mode': self.batch_mode_flag if batch_mode else '',
                    'Processing_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Company_Industry': executive.get('company_industry', '')
                })
            
            detailed_data.append(row)
        
        # Create DataFrame
        df = pd.DataFrame(detailed_data)
        
        if append_mode:
            # Append to existing file
            try:
                existing_df = pd.read_csv(filename)
                # Add batch columns if they don't exist
                if 'Batch_Mode' not in existing_df.columns:
                    existing_df['Batch_Mode'] = ''
                if 'Processing_Date' not in existing_df.columns:
                    existing_df['Processing_Date'] = ''
                if 'Company_Industry' not in existing_df.columns:
                    existing_df['Company_Industry'] = ''
                
                # Combine existing and new data
                combined_df = pd.concat([existing_df, df], ignore_index=True)
                combined_df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✅ Appended detailed data for {len(executives)} executives to {filename}")
            except FileNotFoundError:
                # File doesn't exist, create new
                df.to_csv(filename, index=False, encoding='utf-8')
                print(f"✅ Created new detailed file {filename} with {len(executives)} executives")
        else:
            # Overwrite existing file
            df.to_csv(filename, index=False, encoding='utf-8')
            print(f"✅ Exported detailed data for {len(executives)} executives to {filename}")
        
        return filename
    
    def generate_summary_report(self, executives: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary report of the extraction results
        """
        if not executives:
            return {
                'total_executives': 0,
                'banks_covered': 0,
                'positions_found': 0,
                'emails_found': 0,
                'linkedin_profiles': 0
            }
        
        # Count statistics
        companies = set(exec.get('company', '') or exec.get('bank', '') for exec in executives if exec.get('company') or exec.get('bank'))
        positions = set(exec.get('title', '') for exec in executives if exec.get('title'))
        emails = sum(1 for exec in executives if exec.get('email'))
        linkedin = sum(1 for exec in executives if exec.get('linkedin'))
        
        # Company breakdown
        company_breakdown = {}
        for exec in executives:
            company = exec.get('company', '') or exec.get('bank', 'Unknown')
            if company in company_breakdown:
                company_breakdown[company] += 1
            else:
                company_breakdown[company] = 1
        
        # Position breakdown
        position_breakdown = {}
        for exec in executives:
            position = exec.get('title', 'Unknown')
            if position in position_breakdown:
                position_breakdown[position] += 1
            else:
                position_breakdown[position] = 1
        
        report = {
            'total_executives': len(executives),
            'companies_covered': len(companies),
            'positions_found': len(positions),
            'emails_found': emails,
            'linkedin_profiles': linkedin,
            'company_breakdown': company_breakdown,
            'position_breakdown': position_breakdown,
            'extraction_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return report
    
    def print_summary_report(self, report: Dict[str, Any]):
        """
        Print a formatted summary report
        """
        print("\n" + "="*50)
        print("📊 EXTRACTION SUMMARY REPORT")
        print("="*50)
        print(f"Total Executives Found: {report['total_executives']}")
        print(f"Companies Covered: {report['companies_covered']}")
        print(f"Positions Found: {report['positions_found']}")
        print(f"Emails Found: {report['emails_found']}")
        print(f"LinkedIn Profiles: {report['linkedin_profiles']}")
        print(f"Extraction Date: {report['extraction_date']}")
        
        if report['company_breakdown']:
            print("\n🏢 Company Breakdown:")
            for company, count in sorted(report['company_breakdown'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {company}: {count}")
        
        if report['position_breakdown']:
            print("\n👔 Position Breakdown:")
            for position, count in sorted(report['position_breakdown'].items(), key=lambda x: x[1], reverse=True):
                print(f"  {position}: {count}")
        
        print("="*50)
    
    def export_summary_to_txt(self, report: Dict[str, Any], filename: str = "extraction_summary.txt"):
        """
        Export summary report to text file
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("CXO EXTRACTION SUMMARY REPORT\n")
            f.write("="*50 + "\n")
            f.write(f"Total Executives Found: {report['total_executives']}\n")
            f.write(f"Companies Covered: {report['companies_covered']}\n")
            f.write(f"Positions Found: {report['positions_found']}\n")
            f.write(f"Emails Found: {report['emails_found']}\n")
            f.write(f"LinkedIn Profiles: {report['linkedin_profiles']}\n")
            f.write(f"Extraction Date: {report['extraction_date']}\n")
            
            if report['company_breakdown']:
                f.write("\nCompany Breakdown:\n")
                for company, count in sorted(report['company_breakdown'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {company}: {count}\n")
            
            if report['position_breakdown']:
                f.write("\nPosition Breakdown:\n")
                for position, count in sorted(report['position_breakdown'].items(), key=lambda x: x[1], reverse=True):
                    f.write(f"  {position}: {count}\n")
        
        print(f"✅ Summary report exported to {filename}")
        return filename 