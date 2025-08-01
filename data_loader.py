#!/usr/bin/env python3
"""
Data Loader Module
Handles loading company data from different sources (JSON, CSV)
"""

import json
from typing import Dict, Any, List
from pathlib import Path

class DataLoader:
    def __init__(self):
        pass
    
    def load_from_json(self, json_data: str) -> Dict[str, Any]:
        """
        Load company data from JSON string (generated by chat agent)
        
        Args:
            json_data (str): JSON string with companies data
            
        Returns:
            Dict[str, Any]: Standardized company data structure
            
        Raises:
            ValueError: If JSON is invalid or missing required fields
        """
        try:
            # Parse JSON
            data = json.loads(json_data)
            
            # Validate structure
            if not isinstance(data, dict):
                raise ValueError("JSON must be an object")
            
            if 'companies' not in data:
                raise ValueError("JSON must contain 'companies' array")
            
            if not isinstance(data['companies'], list):
                raise ValueError("'companies' must be an array")
            
            # Validate each company
            validated_companies = []
            for i, company in enumerate(data['companies']):
                if not isinstance(company, dict):
                    raise ValueError(f"Company at index {i} must be an object")
                
                # Check required fields
                required_fields = ['name', 'city', 'country', 'industry']
                missing_fields = [field for field in required_fields if field not in company]
                
                if missing_fields:
                    raise ValueError(f"Company at index {i} missing required fields: {missing_fields}")
                
                # Validate field types
                for field in required_fields:
                    if not isinstance(company[field], str) or not company[field].strip():
                        raise ValueError(f"Company at index {i} field '{field}' must be a non-empty string")
                
                # Add validated company
                validated_companies.append({
                    'name': company['name'].strip(),
                    'city': company['city'].strip(),
                    'country': company['country'].strip(),
                    'industry': company['industry'].strip()
                })
            
            return {
                'companies': validated_companies,
                'source': 'json',
                'total_companies': len(validated_companies)
            }
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Error processing JSON: {e}")
    
    def load_from_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Load company data from CSV file (uploaded by user)
        
        Args:
            file_path (str): Path to CSV file
            
        Returns:
            Dict[str, Any]: Standardized company data structure
            
        Raises:
            ValueError: If CSV is invalid or missing required columns
        """
        try:
            # Check if file exists
            if not Path(file_path).exists():
                raise ValueError(f"CSV file not found: {file_path}")
            
            # Read CSV with manual parsing to handle mixed row lengths
            companies = []
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='latin-1') as f:
                    lines = f.readlines()
            
            # Skip header line
            if lines:
                header = lines[0].strip().split(',')
                lines = lines[1:]
            
            # Process each line manually
            for line_num, line in enumerate(lines, 2):  # Start from line 2 (after header)
                line = line.strip()
                if not line:
                    continue
                
                # Split by comma, but handle quoted fields
                fields = []
                current_field = ""
                in_quotes = False
                
                for char in line:
                    if char == '"':
                        in_quotes = not in_quotes
                    elif char == ',' and not in_quotes:
                        fields.append(current_field.strip())
                        current_field = ""
                    else:
                        current_field += char
                
                # Add the last field
                fields.append(current_field.strip())
                
                # Handle different row formats
                if len(fields) >= 4:
                    # Extract the first 4 fields (name, city, country, industry)
                    name = fields[0].strip('"')
                    city = fields[1].strip('"')
                    country = fields[2].strip('"')
                    industry = fields[3].strip('"')
                    
                    # Skip if any required field is empty
                    if not name or not city or not country or not industry:
                        continue
                    
                    companies.append({
                        'name': name,
                        'city': city,
                        'country': country,
                        'industry': industry
                    })
                else:
                    print(f"⚠️ Skipping line {line_num}: insufficient fields ({len(fields)})")
            
            if not companies:
                raise ValueError("No valid companies found in CSV file")
            
            return {
                'companies': companies,
                'source': 'csv',
                'total_companies': len(companies)
            }
            

            
        except Exception as e:
            raise ValueError(f"Error processing CSV: {e}")
    
    def validate_company_data(self, companies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Validate and clean company data
        
        Args:
            companies (List[Dict[str, Any]]): List of company dictionaries
            
        Returns:
            List[Dict[str, Any]]: Validated and cleaned companies
        """
        validated = []
        
        for i, company in enumerate(companies):
            try:
                # Check required fields
                required_fields = ['name', 'city', 'country', 'industry']
                for field in required_fields:
                    if field not in company or not company[field] or not str(company[field]).strip():
                        print(f"⚠️ Skipping company {i+1}: missing or empty '{field}'")
                        continue
                
                # Clean and validate
                validated_company = {
                    'name': str(company['name']).strip(),
                    'city': str(company['city']).strip(),
                    'country': str(company['country']).strip(),
                    'industry': str(company['industry']).strip()
                }
                
                # Basic validation
                if len(validated_company['name']) < 2:
                    print(f"⚠️ Skipping company {i+1}: name too short")
                    continue
                
                validated.append(validated_company)
                
            except Exception as e:
                print(f"⚠️ Skipping company {i+1}: validation error - {e}")
                continue
        
        return validated 