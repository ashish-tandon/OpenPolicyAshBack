"""
AI Services for OpenPolicy Backend Ash Aug 2025

Provides AI-powered bill summaries, analysis, and insights using OpenAI's API.
"""

import os
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import openai
from sqlalchemy.orm import Session
import asyncio
import json

from database import Bill, Jurisdiction, JurisdictionType
from database import get_session_factory, get_database_config, create_engine_from_config

logger = logging.getLogger(__name__)

# OpenAI configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
AI_SUMMARIES_ENABLED = os.getenv("AI_SUMMARIES_ENABLED", "false").lower() == "true"

class AIBillAnalyzer:
    """AI-powered bill analysis and summarization"""
    
    def __init__(self):
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        self.SessionLocal = get_session_factory(engine)
        self.model = "gpt-4o-mini"  # Cost-effective model for summaries
    
    async def summarize_bill(self, bill: Bill) -> Dict[str, Any]:
        """Generate AI summary for a bill"""
        if not AI_SUMMARIES_ENABLED or not openai.api_key:
            return {"error": "AI summaries not enabled or API key not configured"}
        
        try:
            # Prepare bill text for analysis
            bill_text = self._prepare_bill_text(bill)
            
            # Generate summary
            summary_prompt = f"""
            Please analyze this Canadian legislative bill and provide a comprehensive summary:

            Bill: {bill.identifier}
            Title: {bill.title}
            Status: {bill.status}
            Content: {bill_text}

            Provide a JSON response with the following structure:
            {{
                "executive_summary": "Brief 2-3 sentence overview",
                "key_provisions": ["List of main provisions"],
                "impact_analysis": "Who and what will be affected",
                "parliamentary_stage": "Current stage in legislative process",
                "controversy_level": "Low/Medium/High with explanation",
                "public_interest": "Low/Medium/High with explanation",
                "implementation_timeline": "When changes would take effect",
                "related_legislation": "Any related or conflicting bills",
                "stakeholder_impact": {{
                    "citizens": "Impact on general public",
                    "businesses": "Impact on business sector",
                    "government": "Impact on government operations"
                }}
            }}
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert Canadian parliamentary analyst. Provide accurate, objective analysis of legislative bills."},
                    {"role": "user", "content": summary_prompt}
                ],
                max_tokens=1500,
                temperature=0.3
            )
            
            # Parse AI response
            ai_analysis = json.loads(response.choices[0].message.content)
            
            # Add metadata
            ai_analysis["generated_at"] = datetime.now().isoformat()
            ai_analysis["model_used"] = self.model
            ai_analysis["bill_id"] = bill.id
            ai_analysis["confidence_score"] = self._calculate_confidence(bill_text, ai_analysis)
            
            return ai_analysis
            
        except Exception as e:
            logger.error(f"Failed to generate AI summary for bill {bill.identifier}: {e}")
            return {"error": f"AI analysis failed: {str(e)}"}
    
    def _prepare_bill_text(self, bill: Bill) -> str:
        """Prepare bill text for AI analysis"""
        text_parts = []
        
        if bill.title:
            text_parts.append(f"Title: {bill.title}")
        
        if bill.summary:
            text_parts.append(f"Summary: {bill.summary}")
        
        # In a real implementation, you would fetch the full bill text
        # For now, we'll work with available fields
        text_parts.append(f"Status: {bill.status}")
        
        return "\n\n".join(text_parts)
    
    def _calculate_confidence(self, bill_text: str, analysis: Dict[str, Any]) -> float:
        """Calculate confidence score for AI analysis"""
        # Simple heuristic based on text length and analysis completeness
        text_length_score = min(len(bill_text) / 1000, 1.0)  # More text = higher confidence
        analysis_completeness = len([k for k, v in analysis.items() if v and k != "error"]) / 8
        
        return round((text_length_score + analysis_completeness) / 2, 2)
    
    async def analyze_federal_bills(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Analyze recent federal bills with AI"""
        with self.SessionLocal() as db:
            # Get recent federal bills
            federal_jurisdiction = db.query(Jurisdiction).filter(
                Jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL
            ).first()
            
            if not federal_jurisdiction:
                return []
            
            recent_bills = db.query(Bill).filter(
                Bill.jurisdiction_id == federal_jurisdiction.id,
                Bill.updated_at >= datetime.now() - timedelta(days=days_back)
            ).limit(10).all()  # Limit to prevent excessive API calls
            
            analyses = []
            for bill in recent_bills:
                analysis = await self.summarize_bill(bill)
                if "error" not in analysis:
                    analyses.append({
                        "bill": {
                            "id": bill.id,
                            "identifier": bill.identifier,
                            "title": bill.title,
                            "status": bill.status
                        },
                        "ai_analysis": analysis
                    })
            
            return analyses
    
    async def detect_critical_bills(self, bills: List[Bill]) -> List[Dict[str, Any]]:
        """Use AI to detect potentially critical bills"""
        if not AI_SUMMARIES_ENABLED:
            return []
        
        critical_bills = []
        
        for bill in bills:
            try:
                prompt = f"""
                Analyze this Canadian bill and determine if it's critically important for public interest:

                Bill: {bill.identifier}
                Title: {bill.title}
                Summary: {bill.summary or "No summary available"}

                Rate the bill's importance on a scale of 1-10 and provide reasoning.
                Consider factors like:
                - Public impact scope
                - Economic implications
                - Constitutional significance
                - Social policy changes
                - Emergency/urgent nature

                Respond with JSON: {{"importance_score": 1-10, "reasoning": "explanation", "category": "budget/healthcare/security/etc"}}
                """
                
                response = await openai.ChatCompletion.acreate(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a Canadian policy expert. Rate bill importance objectively."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.2
                )
                
                analysis = json.loads(response.choices[0].message.content)
                
                if analysis.get("importance_score", 0) >= 7:  # High importance threshold
                    critical_bills.append({
                        "bill": bill,
                        "importance_score": analysis["importance_score"],
                        "reasoning": analysis["reasoning"],
                        "category": analysis.get("category", "general")
                    })
                    
            except Exception as e:
                logger.error(f"Failed to analyze bill criticality for {bill.identifier}: {e}")
        
        return sorted(critical_bills, key=lambda x: x["importance_score"], reverse=True)
    
    async def generate_daily_briefing(self) -> Dict[str, Any]:
        """Generate daily AI briefing of parliamentary activity"""
        try:
            analyses = await self.analyze_federal_bills(days_back=1)
            
            if not analyses:
                return {"briefing": "No recent federal bill activity to report."}
            
            briefing_prompt = f"""
            Create a daily briefing for Canadian parliamentary activity based on these bill analyses:

            {json.dumps(analyses, indent=2)}

            Provide a professional briefing in this format:
            {{
                "headline": "Brief headline summarizing today's activity",
                "summary": "2-3 paragraph executive summary",
                "key_developments": ["List of important developments"],
                "bills_to_watch": ["Bills requiring public attention"],
                "next_steps": "What to expect next"
            }}
            """
            
            response = await openai.ChatCompletion.acreate(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a parliamentary correspondent creating daily briefings for informed citizens."},
                    {"role": "user", "content": briefing_prompt}
                ],
                max_tokens=1000,
                temperature=0.4
            )
            
            briefing = json.loads(response.choices[0].message.content)
            briefing["generated_at"] = datetime.now().isoformat()
            briefing["bills_analyzed"] = len(analyses)
            
            return briefing
            
        except Exception as e:
            logger.error(f"Failed to generate daily briefing: {e}")
            return {"error": f"Briefing generation failed: {str(e)}"}

class DataEnricher:
    """Cross-reference and enrich civic data with external sources"""
    
    def __init__(self):
        config = get_database_config()
        engine = create_engine_from_config(config.get_url())
        self.SessionLocal = get_session_factory(engine)
    
    async def enrich_bill_data(self, bill: Bill) -> Dict[str, Any]:
        """Enrich bill data with external sources"""
        enrichment = {
            "bill_id": bill.id,
            "enriched_at": datetime.now().isoformat(),
            "sources": []
        }
        
        try:
            # Parliamentary website link
            if bill.jurisdiction and bill.jurisdiction.jurisdiction_type == JurisdictionType.FEDERAL:
                parl_link = f"https://www.parl.ca/legisinfo/en/bill/{bill.identifier.lower()}"
                enrichment["parliamentary_link"] = parl_link
                enrichment["sources"].append("Parliament of Canada")
            
            # OpenParliament.ca integration
            openparl_link = f"https://openparliament.ca/bills/{bill.identifier.lower()}/"
            enrichment["openparliament_link"] = openparl_link
            enrichment["sources"].append("OpenParliament.ca")
            
            # Related news and media (would integrate with news APIs)
            enrichment["related_news"] = await self._fetch_related_news(bill)
            
            # Stakeholder analysis
            enrichment["stakeholders"] = await self._identify_stakeholders(bill)
            
            return enrichment
            
        except Exception as e:
            logger.error(f"Failed to enrich bill data for {bill.identifier}: {e}")
            return {"error": f"Data enrichment failed: {str(e)}"}
    
    async def _fetch_related_news(self, bill: Bill) -> List[Dict[str, str]]:
        """Fetch related news articles (placeholder for news API integration)"""
        # In a real implementation, integrate with news APIs like:
        # - Google News API
        # - NewsAPI
        # - CBC News API
        
        return [
            {
                "title": f"Analysis: {bill.title}",
                "source": "CBC News",
                "url": f"https://cbc.ca/news/politics/bill-{bill.identifier.lower()}",
                "date": datetime.now().strftime("%Y-%m-%d")
            }
        ]
    
    async def _identify_stakeholders(self, bill: Bill) -> List[str]:
        """Identify key stakeholders affected by the bill"""
        # Use AI to identify stakeholders
        if not AI_SUMMARIES_ENABLED:
            return ["General Public"]
        
        try:
            prompt = f"""
            Identify the key stakeholders affected by this Canadian bill:
            
            Title: {bill.title}
            Summary: {bill.summary or "No summary available"}
            
            List the main groups, organizations, or sectors that would be impacted.
            Respond with a JSON array of stakeholder names.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Identify stakeholders affected by Canadian legislation."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.3
            )
            
            stakeholders = json.loads(response.choices[0].message.content)
            return stakeholders if isinstance(stakeholders, list) else ["General Public"]
            
        except Exception as e:
            logger.error(f"Failed to identify stakeholders for {bill.identifier}: {e}")
            return ["General Public"]

# Global instances
ai_analyzer = AIBillAnalyzer()
data_enricher = DataEnricher()