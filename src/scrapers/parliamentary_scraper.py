"""
Parliamentary Data Scraper - Enhanced OpenParliament Integration
Processes Hansard debates, committee meetings, and parliamentary sessions
Based on patterns from michaelmulley/openparliament
"""

import xml.etree.ElementTree as ET
import requests
from datetime import datetime, date
from typing import List, Dict, Optional
import re
import logging
from sqlalchemy.orm import Session
from bs4 import BeautifulSoup

from src.database.models import (
    HansardRecord, ParliamentarySession, Speech, CommitteeMeeting
)
from src.database.connection import get_db_session

logger = logging.getLogger(__name__)

class ParliamentaryScraper:
    def __init__(self):
        self.base_url = "https://www.parl.gc.ca"
        self.hansard_base = f"{self.base_url}/HousePublications"
        self.committee_base = f"{self.base_url}/Committees"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OpenPolicy Parliamentary Scraper (contact@openpolicy.ca)'
        })
        
    def get_current_session(self) -> ParliamentarySession:
        """Get or create the current parliamentary session"""
        with get_db_session() as db:
            # For now, using 44th Parliament, 1st Session (current as of 2024)
            session = db.query(ParliamentarySession).filter_by(
                parliament_number=44, 
                session_number=1
            ).first()
            
            if not session:
                session = ParliamentarySession(
                    parliament_number=44,
                    session_number=1,
                    start_date=date(2021, 11, 22)  # 44th Parliament start date
                )
                db.add(session)
                db.commit()
                db.refresh(session)
                
            return session
    
    def scrape_hansard_list(self, parliament: int = 44, session: int = 1) -> List[Dict]:
        """Scrape list of available Hansard debates"""
        url = f"{self.hansard_base}/Publication.aspx"
        params = {
            'Language': 'E',
            'Mode': '1',
            'Parl': parliament,
            'Ses': session
        }
        
        try:
            logger.info(f"Scraping Hansard list for Parliament {parliament}, Session {session}")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            debates = []
            
            # Look for debate links in the publication list
            debate_links = soup.find_all('a', href=re.compile(r'DocId=\d+'))
            
            for link in debate_links:
                href = link.get('href', '')
                doc_id_match = re.search(r'DocId=(\d+)', href)
                
                if doc_id_match:
                    doc_id = doc_id_match.group(1)
                    title = link.get_text(strip=True)
                    
                    # Extract date if possible
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', title)
                    debate_date = None
                    if date_match:
                        try:
                            debate_date = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                        except:
                            pass
                    
                    # Construct XML URL
                    xml_url = f"{self.hansard_base}/Publication.aspx?DocId={doc_id}&Language=E&xml=true"
                    pdf_url = f"{self.hansard_base}/Publication.aspx?DocId={doc_id}&Language=E&File=4"
                    
                    debates.append({
                        'doc_id': doc_id,
                        'title': title,
                        'date': debate_date,
                        'document_url': f"{self.base_url}{href}" if href.startswith('/') else href,
                        'xml_url': xml_url,
                        'pdf_url': pdf_url
                    })
            
            logger.info(f"Found {len(debates)} Hansard debates")
            return debates
            
        except Exception as e:
            logger.error(f"Error scraping Hansard list: {e}")
            return []
    
    def save_hansard_records(self, debates: List[Dict], session_id: int) -> List[HansardRecord]:
        """Save Hansard records to database"""
        saved_records = []
        
        with get_db_session() as db:
            for debate in debates:
                # Check if record already exists
                existing = db.query(HansardRecord).filter_by(
                    date=debate['date'],
                    session_id=session_id
                ).first()
                
                if not existing and debate['date']:
                    record = HansardRecord(
                        date=debate['date'],
                        document_url=debate['document_url'],
                        xml_url=debate['xml_url'],
                        pdf_url=debate['pdf_url'],
                        session_id=session_id,
                        processed=False
                    )
                    db.add(record)
                    saved_records.append(record)
            
            db.commit()
            
        logger.info(f"Saved {len(saved_records)} new Hansard records")
        return saved_records
    
    def process_hansard_xml(self, xml_url: str, hansard_id: int) -> int:
        """Process Hansard XML document to extract speeches"""
        try:
            logger.info(f"Processing Hansard XML: {xml_url}")
            response = self.session.get(xml_url, timeout=30)
            response.raise_for_status()
            
            # Parse XML content
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.error(f"XML parsing error for {xml_url}: {e}")
                return 0
            
            # XML namespace handling (Hansard XML uses specific namespaces)
            # Note: Actual namespace may vary, this is a common pattern
            namespaces = {}
            
            # Try to extract namespaces from root element
            if root.tag.startswith('{'):
                namespace = root.tag[1:].split('}')[0]
                namespaces['hansard'] = namespace
            
            speeches = []
            
            # Extract speeches from XML - multiple possible structures
            speech_elements = (
                root.findall('.//Speech', namespaces) or
                root.findall('.//speech', namespaces) or
                root.findall('.//*[contains(local-name(), "speech")]') or
                root.findall('.//*[contains(local-name(), "intervention")]')
            )
            
            for speech_elem in speech_elements:
                speech_data = self.extract_speech_data(speech_elem, namespaces)
                if speech_data:
                    speech_data['hansard_id'] = hansard_id
                    speeches.append(speech_data)
            
            # Save speeches to database
            with get_db_session() as db:
                for speech_data in speeches:
                    speech = Speech(**speech_data)
                    db.add(speech)
                
                # Update hansard record
                hansard = db.query(HansardRecord).get(hansard_id)
                if hansard:
                    hansard.processed = True
                    hansard.speech_count = len(speeches)
                
                db.commit()
                
            logger.info(f"Processed {len(speeches)} speeches from Hansard {hansard_id}")
            return len(speeches)
            
        except Exception as e:
            logger.error(f"Error processing Hansard XML {xml_url}: {e}")
            return 0
    
    def extract_speech_data(self, speech_elem, namespaces: Dict) -> Optional[Dict]:
        """Extract individual speech data from XML element"""
        try:
            # Try different possible structures for speaker information
            speaker_name = ""
            speaker_title = ""
            
            # Method 1: Direct attributes
            speaker_name = speech_elem.get('speaker', '') or speech_elem.get('SpeakerName', '')
            speaker_title = speech_elem.get('title', '') or speech_elem.get('SpeakerTitle', '')
            
            # Method 2: Child elements
            if not speaker_name:
                speaker_elem = (
                    speech_elem.find('./Speaker') or
                    speech_elem.find('./speaker') or
                    speech_elem.find('.//PersonSpeaking')
                )
                if speaker_elem is not None:
                    speaker_name = speaker_elem.get('name', '') or speaker_elem.text or ""
                    speaker_title = speaker_elem.get('title', '')
            
            # Extract content - try different possible structures
            content = ""
            content_elem = (
                speech_elem.find('./Content') or
                speech_elem.find('./content') or
                speech_elem.find('.//ParaText') or
                speech_elem
            )
            
            if content_elem is not None:
                # Get all text content, preserving structure
                content = ET.tostring(content_elem, encoding='unicode', method='text').strip()
                # Clean up excessive whitespace
                content = re.sub(r'\s+', ' ', content)
            
            # Skip if no meaningful content
            if not content or len(content.strip()) < 10:
                return None
            
            # Extract time if available
            time_spoken = None
            time_attr = speech_elem.get('time') or speech_elem.get('Time')
            if time_attr:
                try:
                    time_spoken = datetime.fromisoformat(time_attr.replace('Z', '+00:00'))
                except:
                    pass
            
            # Determine speech type
            speech_type = speech_elem.get('type', 'statement')
            if not speech_type:
                # Infer from content or structure
                if '?' in content[-50:]:  # Question at end
                    speech_type = 'question'
                elif speaker_title and 'Minister' in speaker_title:
                    speech_type = 'ministerial_response'
                else:
                    speech_type = 'statement'
            
            return {
                'speaker_name': speaker_name[:200] if speaker_name else "Unknown Speaker",
                'speaker_title': speaker_title[:200] if speaker_title else "",
                'content': content,
                'time_spoken': time_spoken,
                'speech_type': speech_type[:50] if speech_type else 'statement'
            }
            
        except Exception as e:
            logger.error(f"Error extracting speech data: {e}")
            return None
    
    def scrape_committee_meetings(self, committee_acronym: str) -> List[Dict]:
        """Scrape committee meeting evidence"""
        url = f"{self.committee_base}/{committee_acronym}/Meetings"
        
        try:
            logger.info(f"Scraping committee meetings for {committee_acronym}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            meetings = []
            
            # Look for meeting links
            meeting_links = soup.find_all('a', href=re.compile(r'MeetingId=\d+'))
            
            for link in meeting_links:
                href = link.get('href', '')
                meeting_id_match = re.search(r'MeetingId=(\d+)', href)
                
                if meeting_id_match:
                    meeting_id = meeting_id_match.group(1)
                    
                    # Extract meeting information from surrounding text
                    meeting_text = link.get_text(strip=True)
                    
                    # Try to extract date
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', meeting_text)
                    meeting_date = None
                    if date_match:
                        try:
                            meeting_date = datetime.strptime(date_match.group(1), '%Y-%m-%d').date()
                        except:
                            pass
                    
                    # Extract meeting number if available
                    number_match = re.search(r'Meeting (\d+)', meeting_text, re.IGNORECASE)
                    meeting_number = int(number_match.group(1)) if number_match else None
                    
                    meetings.append({
                        'meeting_id': meeting_id,
                        'committee_acronym': committee_acronym,
                        'meeting_date': meeting_date,
                        'meeting_number': meeting_number,
                        'evidence_url': f"{self.base_url}{href}" if href.startswith('/') else href
                    })
            
            logger.info(f"Found {len(meetings)} meetings for committee {committee_acronym}")
            return meetings
            
        except Exception as e:
            logger.error(f"Error scraping committee meetings for {committee_acronym}: {e}")
            return []
    
    def save_committee_meetings(self, meetings: List[Dict], session_id: int) -> List[CommitteeMeeting]:
        """Save committee meetings to database"""
        saved_meetings = []
        
        with get_db_session() as db:
            for meeting in meetings:
                if not meeting['meeting_date']:
                    continue
                    
                # Check if meeting already exists
                existing = db.query(CommitteeMeeting).filter_by(
                    committee_name=meeting['committee_acronym'],
                    meeting_date=meeting['meeting_date'],
                    session_id=session_id
                ).first()
                
                if not existing:
                    record = CommitteeMeeting(
                        committee_name=meeting['committee_acronym'],
                        meeting_date=meeting['meeting_date'],
                        meeting_number=meeting['meeting_number'],
                        evidence_url=meeting['evidence_url'],
                        session_id=session_id,
                        processed=False
                    )
                    db.add(record)
                    saved_meetings.append(record)
            
            db.commit()
            
        logger.info(f"Saved {len(saved_meetings)} new committee meetings")
        return saved_meetings
    
    def run_full_parliamentary_scrape(self) -> Dict:
        """Run complete parliamentary data collection"""
        results = {
            'parliamentary_session': None,
            'hansard_records': 0,
            'speeches_processed': 0,
            'committee_meetings': 0,
            'errors': []
        }
        
        try:
            # Get or create current session
            session = self.get_current_session()
            results['parliamentary_session'] = f"{session.parliament_number}-{session.session_number}"
            
            # Scrape Hansard debates
            debates = self.scrape_hansard_list(session.parliament_number, session.session_number)
            hansard_records = self.save_hansard_records(debates, session.id)
            results['hansard_records'] = len(hansard_records)
            
            # Process a few recent Hansard records (limit to avoid overwhelming)
            for record in hansard_records[:5]:  # Process 5 most recent
                speeches_count = self.process_hansard_xml(record.xml_url, record.id)
                results['speeches_processed'] += speeches_count
            
            # Scrape committee meetings for major committees
            major_committees = ['FINA', 'HESA', 'JUST', 'ETHI', 'PROC']  # Finance, Health, Justice, Ethics, Procedure
            
            for committee in major_committees:
                try:
                    meetings = self.scrape_committee_meetings(committee)
                    saved_meetings = self.save_committee_meetings(meetings, session.id)
                    results['committee_meetings'] += len(saved_meetings)
                except Exception as e:
                    results['errors'].append(f"Committee {committee}: {str(e)}")
            
            logger.info(f"Parliamentary scrape completed: {results}")
            
        except Exception as e:
            logger.error(f"Error in full parliamentary scrape: {e}")
            results['errors'].append(str(e))
        
        return results

# Utility functions for integration with existing scraper system
def get_parliamentary_scraper():
    """Get parliamentary scraper instance"""
    return ParliamentaryScraper()

def run_parliamentary_data_collection():
    """Run parliamentary data collection - can be called from manage.py"""
    scraper = ParliamentaryScraper()
    return scraper.run_full_parliamentary_scrape()