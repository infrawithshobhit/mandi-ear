"""
Government Data Integration System
Handles MSP rate updates and government data sources
"""

import asyncio
import aiohttp
import structlog
from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import json
import re
from bs4 import BeautifulSoup
from io import StringIO
import csv

from models import (
    MSPRate, GovernmentDataSource, MSPSeason, MSPCommodityType,
    ProcurementCenter
)
from database import store_msp_rate, store_procurement_center, get_government_data_sources

logger = structlog.get_logger()

class GovernmentDataIntegrator:
    """Integrates with government data sources for MSP rates and procurement centers"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.data_sources: List[GovernmentDataSource] = []
        self.sync_tasks: List[asyncio.Task] = []
        self.is_running = False
    
    async def initialize(self):
        """Initialize the data integrator"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=60),
            headers={
                'User-Agent': 'MANDI-EAR-MSP-Service/1.0'
            }
        )
        await self._load_data_sources()
        logger.info("Government data integrator initialized")
    
    async def shutdown(self):
        """Shutdown the data integrator"""
        self.is_running = False
        
        # Cancel sync tasks
        for task in self.sync_tasks:
            task.cancel()
        
        if self.sync_tasks:
            await asyncio.gather(*self.sync_tasks, return_exceptions=True)
        
        if self.session:
            await self.session.close()
        
        logger.info("Government data integrator shutdown")
    
    async def _load_data_sources(self):
        """Load configured government data sources"""
        try:
            # Load from database if available
            self.data_sources = await get_government_data_sources()
        except:
            # Fallback to default sources
            self.data_sources = [
                GovernmentDataSource(
                    id="cacp_msp",
                    name="Commission for Agricultural Costs & Prices",
                    url="https://cacp.dacnet.nic.in/",
                    update_frequency=24,  # Check daily
                    reliability_score=0.95
                ),
                GovernmentDataSource(
                    id="fci_msp",
                    name="Food Corporation of India",
                    url="https://fci.gov.in/",
                    update_frequency=24,
                    reliability_score=0.9
                ),
                GovernmentDataSource(
                    id="agmarknet_msp",
                    name="AgMarkNet MSP Data",
                    url="https://agmarknet.gov.in/",
                    api_endpoint="https://api.data.gov.in/resource/35985678-0d79-46b4-9ed6-6f13308a1d24",
                    update_frequency=12,  # Check twice daily
                    reliability_score=0.85
                ),
                GovernmentDataSource(
                    id="dacfw_msp",
                    name="Department of Agriculture & Farmers Welfare",
                    url="https://agricoop.nic.in/",
                    update_frequency=24,
                    reliability_score=0.9
                )
            ]
        
        logger.info("Loaded government data sources", count=len(self.data_sources))
    
    async def start_sync_tasks(self):
        """Start background sync tasks for all data sources"""
        if self.is_running:
            return
        
        self.is_running = True
        
        for source in self.data_sources:
            if source.is_active:
                task = asyncio.create_task(self._sync_loop(source))
                self.sync_tasks.append(task)
        
        logger.info("Started government data sync tasks", count=len(self.sync_tasks))
    
    async def stop_sync_tasks(self):
        """Stop all sync tasks"""
        self.is_running = False
        
        for task in self.sync_tasks:
            task.cancel()
        
        self.sync_tasks.clear()
        logger.info("Stopped government data sync tasks")
    
    async def _sync_loop(self, source: GovernmentDataSource):
        """Sync loop for a specific data source"""
        while self.is_running:
            try:
                await self._sync_from_source(source)
                source.last_sync = datetime.utcnow()
                
                # Wait for next sync
                await asyncio.sleep(source.update_frequency * 3600)  # Convert hours to seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in sync loop", source_id=source.id, error=str(e))
                await asyncio.sleep(3600)  # Wait 1 hour before retry
    
    async def _sync_from_source(self, source: GovernmentDataSource):
        """Sync data from a specific government source"""
        logger.info("Starting sync from government source", source_id=source.id)
        
        try:
            if source.api_endpoint:
                data = await self._fetch_api_data(source)
            else:
                data = await self._scrape_web_data(source)
            
            if data:
                await self._process_government_data(data, source)
                logger.info("Successfully synced government data", source_id=source.id, records=len(data))
            else:
                logger.warning("No data received from government source", source_id=source.id)
                
        except Exception as e:
            logger.error("Failed to sync from government source", source_id=source.id, error=str(e))
    
    async def _fetch_api_data(self, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Fetch data from government API"""
        if not self.session or not source.api_endpoint:
            return []
        
        try:
            headers = {}
            if source.api_key:
                headers['Authorization'] = f'Bearer {source.api_key}'
            
            async with self.session.get(source.api_endpoint, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle different API response formats
                    if isinstance(data, dict):
                        if 'records' in data:
                            return data['records']
                        elif 'data' in data:
                            return data['data']
                        elif 'results' in data:
                            return data['results']
                    elif isinstance(data, list):
                        return data
                    
                    return [data] if data else []
                else:
                    logger.error("API request failed", source_id=source.id, status=response.status)
                    return []
                    
        except Exception as e:
            logger.error("Error fetching API data", source_id=source.id, error=str(e))
            return []
    
    async def _scrape_web_data(self, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Scrape data from government website"""
        if not self.session:
            return []
        
        try:
            # This is a simplified scraper - in production, each source would need
            # specific scraping logic based on their website structure
            async with self.session.get(source.url) as response:
                if response.status == 200:
                    html = await response.text()
                    return await self._parse_government_html(html, source)
                else:
                    logger.error("Web scraping failed", source_id=source.id, status=response.status)
                    return []
                    
        except Exception as e:
            logger.error("Error scraping web data", source_id=source.id, error=str(e))
            return []
    
    async def _parse_government_html(self, html: str, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Parse HTML content from government websites"""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for common patterns in government websites
            data = []
            
            # Look for tables with MSP data
            tables = soup.find_all('table')
            for table in tables:
                table_data = self._extract_table_data(table)
                if self._is_msp_table(table_data):
                    data.extend(self._convert_table_to_msp_records(table_data, source))
            
            # Look for downloadable files (PDF, Excel)
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if any(ext in href.lower() for ext in ['.pdf', '.xls', '.xlsx', '.csv']):
                    if any(keyword in link.text.lower() for keyword in ['msp', 'minimum support price', 'procurement']):
                        file_data = await self._process_downloadable_file(href, source)
                        if file_data:
                            data.extend(file_data)
            
            return data
            
        except Exception as e:
            logger.error("Error parsing government HTML", source_id=source.id, error=str(e))
            return []
    
    def _extract_table_data(self, table) -> List[List[str]]:
        """Extract data from HTML table"""
        rows = []
        for tr in table.find_all('tr'):
            row = []
            for td in tr.find_all(['td', 'th']):
                row.append(td.get_text(strip=True))
            if row:
                rows.append(row)
        return rows
    
    def _is_msp_table(self, table_data: List[List[str]]) -> bool:
        """Check if table contains MSP data"""
        if not table_data:
            return False
        
        # Check headers for MSP-related keywords
        header_text = ' '.join(table_data[0]).lower()
        msp_keywords = ['msp', 'minimum support price', 'procurement price', 'commodity', 'crop']
        
        return any(keyword in header_text for keyword in msp_keywords)
    
    def _convert_table_to_msp_records(self, table_data: List[List[str]], source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Convert table data to MSP records"""
        if len(table_data) < 2:
            return []
        
        headers = [h.lower().strip() for h in table_data[0]]
        records = []
        
        for row in table_data[1:]:
            if len(row) != len(headers):
                continue
            
            record = dict(zip(headers, row))
            
            # Try to extract MSP information
            msp_record = self._parse_msp_record(record, source)
            if msp_record:
                records.append(msp_record)
        
        return records
    
    def _parse_msp_record(self, record: Dict[str, str], source: GovernmentDataSource) -> Optional[Dict[str, Any]]:
        """Parse a single MSP record from table data"""
        try:
            # Common field mappings
            commodity_fields = ['commodity', 'crop', 'crop name', 'item']
            price_fields = ['msp', 'minimum support price', 'price', 'rate', 'rs/qtl', 'rs per quintal']
            season_fields = ['season', 'crop season', 'marketing season']
            year_fields = ['year', 'crop year', 'marketing year']
            
            # Extract commodity
            commodity = None
            for field in commodity_fields:
                if field in record and record[field].strip():
                    commodity = record[field].strip()
                    break
            
            if not commodity:
                return None
            
            # Extract price
            price = None
            for field in price_fields:
                if field in record and record[field].strip():
                    price_text = record[field].strip()
                    # Extract numeric value
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        price = float(price_match.group())
                        break
            
            if not price or price <= 0:
                return None
            
            # Extract season
            season = MSPSeason.KHARIF  # Default
            for field in season_fields:
                if field in record and record[field].strip():
                    season_text = record[field].strip().lower()
                    if 'rabi' in season_text:
                        season = MSPSeason.RABI
                    elif 'summer' in season_text:
                        season = MSPSeason.SUMMER
                    break
            
            # Extract year
            crop_year = None
            for field in year_fields:
                if field in record and record[field].strip():
                    year_text = record[field].strip()
                    year_match = re.search(r'20\d{2}', year_text)
                    if year_match:
                        year = int(year_match.group())
                        crop_year = f"{year}-{year+1:02d}"
                        break
            
            if not crop_year:
                # Use current year as fallback
                current_year = datetime.now().year
                crop_year = f"{current_year}-{current_year+1:02d}"
            
            # Determine commodity type
            commodity_type = self._classify_commodity_type(commodity)
            
            return {
                'commodity': commodity,
                'season': season,
                'crop_year': crop_year,
                'msp_price': price,
                'commodity_type': commodity_type,
                'source_id': source.id,
                'announcement_date': datetime.now().date(),
                'effective_date': datetime.now().date()
            }
            
        except Exception as e:
            logger.error("Error parsing MSP record", error=str(e))
            return None
    
    def _classify_commodity_type(self, commodity: str) -> MSPCommodityType:
        """Classify commodity type based on name"""
        commodity_lower = commodity.lower()
        
        cereals = ['wheat', 'rice', 'maize', 'bajra', 'jowar', 'barley', 'ragi']
        pulses = ['gram', 'tur', 'arhar', 'moong', 'urad', 'masoor', 'lentil']
        oilseeds = ['groundnut', 'mustard', 'rapeseed', 'sunflower', 'soybean', 'safflower', 'niger', 'sesame']
        commercial = ['cotton', 'sugarcane', 'jute']
        
        for cereal in cereals:
            if cereal in commodity_lower:
                return MSPCommodityType.CEREALS
        
        for pulse in pulses:
            if pulse in commodity_lower:
                return MSPCommodityType.PULSES
        
        for oilseed in oilseeds:
            if oilseed in commodity_lower:
                return MSPCommodityType.OILSEEDS
        
        for commercial in commercial:
            if commercial in commodity_lower:
                return MSPCommodityType.COMMERCIAL_CROPS
        
        return MSPCommodityType.CEREALS  # Default
    
    async def _process_downloadable_file(self, file_url: str, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Process downloadable files (PDF, Excel, CSV)"""
        try:
            if not self.session:
                return []
            
            # Make URL absolute if relative
            if not file_url.startswith('http'):
                file_url = f"{source.url.rstrip('/')}/{file_url.lstrip('/')}"
            
            async with self.session.get(file_url) as response:
                if response.status != 200:
                    return []
                
                content = await response.read()
                
                if file_url.lower().endswith('.csv'):
                    return await self._process_csv_data(content, source)
                elif file_url.lower().endswith(('.xls', '.xlsx')):
                    return await self._process_excel_data(content, source)
                elif file_url.lower().endswith('.pdf'):
                    return await self._process_pdf_data(content, source)
                
        except Exception as e:
            logger.error("Error processing downloadable file", file_url=file_url, error=str(e))
        
        return []
    
    async def _process_csv_data(self, content: bytes, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Process CSV data"""
        try:
            csv_text = content.decode('utf-8')
            csv_reader = csv.DictReader(StringIO(csv_text))
            
            records = []
            for row in csv_reader:
                record = self._parse_msp_record(row, source)
                if record:
                    records.append(record)
            
            return records
            
        except Exception as e:
            logger.error("Error processing CSV data", error=str(e))
            return []
    
    async def _process_excel_data(self, content: bytes, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Process Excel data"""
        try:
            # Excel processing would require openpyxl or xlrd
            # For now, return empty list
            logger.info("Excel processing not implemented yet", source_id=source.id)
            return []
            
        except Exception as e:
            logger.error("Error processing Excel data", error=str(e))
            return []
    
    async def _process_pdf_data(self, content: bytes, source: GovernmentDataSource) -> List[Dict[str, Any]]:
        """Process PDF data (simplified - would need proper PDF parsing)"""
        # PDF processing would require libraries like PyPDF2 or pdfplumber
        # For now, return empty list
        logger.info("PDF processing not implemented yet", source_id=source.id)
        return []
    
    async def _process_government_data(self, data: List[Dict[str, Any]], source: GovernmentDataSource):
        """Process and store government data"""
        for record in data:
            try:
                # Create MSP rate record
                msp_rate = MSPRate(
                    commodity=record['commodity'],
                    variety=record.get('variety'),
                    season=record['season'],
                    crop_year=record['crop_year'],
                    msp_price=record['msp_price'],
                    commodity_type=record['commodity_type'],
                    effective_date=record['effective_date'],
                    announcement_date=record['announcement_date'],
                    source_document=f"{source.name} - {source.id}"
                )
                
                # Store in database
                await store_msp_rate(msp_rate)
                
            except Exception as e:
                logger.error("Error processing government data record", error=str(e))
    
    async def manual_sync_all(self):
        """Manually trigger sync for all data sources"""
        tasks = []
        for source in self.data_sources:
            if source.is_active:
                task = asyncio.create_task(self._sync_from_source(source))
                tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            logger.info("Manual sync completed for all sources")
    
    async def sync_procurement_centers(self):
        """Sync government procurement centers"""
        logger.info("Starting procurement centers sync")
        
        # This would integrate with FCI, state agencies, and cooperative databases
        # Enhanced sample data covering more states and center types
        sample_centers = [
            # FCI Centers
            {
                'name': 'FCI Depot Delhi',
                'center_type': 'FCI',
                'address': 'Sector 12, Dwarka, New Delhi',
                'district': 'New Delhi',
                'state': 'Delhi',
                'pincode': '110075',
                'phone_number': '+91-11-25309876',
                'email': 'fci.delhi@fci.gov.in',
                'contact_person': 'Rajesh Kumar',
                'operating_hours': '9:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Maize', 'Bajra'],
                'storage_capacity': 50000.0,
                'current_stock': 25000.0
            },
            {
                'name': 'FCI Depot Ludhiana',
                'center_type': 'FCI',
                'address': 'Industrial Area, Ludhiana, Punjab',
                'district': 'Ludhiana',
                'state': 'Punjab',
                'pincode': '141003',
                'phone_number': '+91-161-2345678',
                'email': 'fci.ludhiana@fci.gov.in',
                'contact_person': 'Harpreet Singh',
                'operating_hours': '8:00 AM - 7:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Bajra', 'Maize'],
                'storage_capacity': 100000.0,
                'current_stock': 45000.0
            },
            {
                'name': 'FCI Depot Karnal',
                'center_type': 'FCI',
                'address': 'Grain Market, Karnal, Haryana',
                'district': 'Karnal',
                'state': 'Haryana',
                'pincode': '132001',
                'phone_number': '+91-184-2234567',
                'email': 'fci.karnal@fci.gov.in',
                'contact_person': 'Suresh Chand',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Mustard', 'Gram'],
                'storage_capacity': 75000.0,
                'current_stock': 30000.0
            },
            
            # State Agency Centers
            {
                'name': 'Punjab State Procurement Center',
                'center_type': 'State Agency',
                'address': 'Mandi Gobindgarh, Punjab',
                'district': 'Fatehgarh Sahib',
                'state': 'Punjab',
                'pincode': '147301',
                'phone_number': '+91-1763-240123',
                'email': 'procurement.punjab@gov.in',
                'contact_person': 'Jasbir Singh',
                'operating_hours': '7:00 AM - 8:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Bajra', 'Maize'],
                'storage_capacity': 75000.0,
                'current_stock': 35000.0
            },
            {
                'name': 'Haryana State Procurement Agency',
                'center_type': 'State Agency',
                'address': 'Sector 4, Panchkula, Haryana',
                'district': 'Panchkula',
                'state': 'Haryana',
                'pincode': '134109',
                'phone_number': '+91-172-2345678',
                'email': 'hspa.panchkula@gov.in',
                'contact_person': 'Ramesh Kumar',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Mustard', 'Gram', 'Bajra'],
                'storage_capacity': 60000.0,
                'current_stock': 28000.0
            },
            {
                'name': 'UP State Procurement Center Meerut',
                'center_type': 'State Agency',
                'address': 'Agricultural Market, Meerut, UP',
                'district': 'Meerut',
                'state': 'Uttar Pradesh',
                'pincode': '250001',
                'phone_number': '+91-121-2345678',
                'email': 'procurement.meerut@up.gov.in',
                'contact_person': 'Vijay Singh',
                'operating_hours': '8:00 AM - 7:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Gram', 'Mustard'],
                'storage_capacity': 80000.0,
                'current_stock': 40000.0
            },
            
            # Cooperative Centers
            {
                'name': 'Delhi Cooperative Marketing Society',
                'center_type': 'Cooperative',
                'address': 'Azadpur Mandi, Delhi',
                'district': 'North Delhi',
                'state': 'Delhi',
                'pincode': '110033',
                'phone_number': '+91-11-27675432',
                'email': 'dcms.azadpur@coop.delhi.gov.in',
                'contact_person': 'Ashok Sharma',
                'operating_hours': '6:00 AM - 8:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Gram', 'Mustard', 'Bajra'],
                'storage_capacity': 40000.0,
                'current_stock': 18000.0
            },
            {
                'name': 'Punjab Cooperative Society Amritsar',
                'center_type': 'Cooperative',
                'address': 'Grain Market, Amritsar, Punjab',
                'district': 'Amritsar',
                'state': 'Punjab',
                'pincode': '143001',
                'phone_number': '+91-183-2345678',
                'email': 'pcs.amritsar@coop.punjab.gov.in',
                'contact_person': 'Gurpreet Kaur',
                'operating_hours': '7:00 AM - 7:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Bajra'],
                'storage_capacity': 55000.0,
                'current_stock': 25000.0
            },
            {
                'name': 'Maharashtra Cooperative Procurement',
                'center_type': 'Cooperative',
                'address': 'APMC Market, Pune, Maharashtra',
                'district': 'Pune',
                'state': 'Maharashtra',
                'pincode': '411001',
                'phone_number': '+91-20-23456789',
                'email': 'mcp.pune@coop.maharashtra.gov.in',
                'contact_person': 'Sunil Patil',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Rice', 'Gram', 'Tur', 'Groundnut'],
                'storage_capacity': 65000.0,
                'current_stock': 32000.0
            },
            
            # Additional centers for better coverage
            {
                'name': 'Gujarat State Procurement Center',
                'center_type': 'State Agency',
                'address': 'Agricultural Market, Ahmedabad, Gujarat',
                'district': 'Ahmedabad',
                'state': 'Gujarat',
                'pincode': '380001',
                'phone_number': '+91-79-23456789',
                'email': 'gspc.ahmedabad@gujarat.gov.in',
                'contact_person': 'Kiran Patel',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Gram', 'Groundnut', 'Mustard', 'Cotton'],
                'storage_capacity': 70000.0,
                'current_stock': 35000.0
            },
            {
                'name': 'Rajasthan Cooperative Marketing',
                'center_type': 'Cooperative',
                'address': 'Mandi Samiti, Jaipur, Rajasthan',
                'district': 'Jaipur',
                'state': 'Rajasthan',
                'pincode': '302001',
                'phone_number': '+91-141-2345678',
                'email': 'rcm.jaipur@coop.rajasthan.gov.in',
                'contact_person': 'Mohan Lal',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Wheat', 'Gram', 'Mustard', 'Bajra', 'Groundnut'],
                'storage_capacity': 50000.0,
                'current_stock': 22000.0
            },
            {
                'name': 'Karnataka State Procurement Agency',
                'center_type': 'State Agency',
                'address': 'APMC Yard, Bangalore, Karnataka',
                'district': 'Bangalore Urban',
                'state': 'Karnataka',
                'pincode': '560001',
                'phone_number': '+91-80-23456789',
                'email': 'kspa.bangalore@karnataka.gov.in',
                'contact_person': 'Ravi Kumar',
                'operating_hours': '8:00 AM - 6:00 PM',
                'commodities_accepted': ['Rice', 'Maize', 'Tur', 'Groundnut', 'Sunflower'],
                'storage_capacity': 60000.0,
                'current_stock': 28000.0
            }
        ]
        
        for center_data in sample_centers:
            try:
                center = ProcurementCenter(**center_data)
                await store_procurement_center(center)
                logger.info("Stored procurement center", name=center.name, state=center.state)
            except Exception as e:
                logger.error("Error storing procurement center", center=center_data.get('name'), error=str(e))
        
        logger.info("Procurement centers sync completed", total_centers=len(sample_centers))