"""
Orchestrator Agent - The Brain
Routes user queries to specialized agents
"""

from typing import Dict, Any, Optional
from enum import Enum
import os
from loguru import logger

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available - using fallback")

class AgentType(Enum):
    """Available specialized agents"""
    SEARCH = "search"
    CAREER = "career"
    TRAVEL = "travel"
    SHOPPING = "shopping"
    LOCAL = "local"
    BROWSER = "browser"
    DATA = "data"

class Orchestrator:
    """
    Main orchestrator that analyzes queries and routes to appropriate agents
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.llm = None
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            try:
                self.llm = ChatGoogleGenerativeAI(
                    model="gemini-2.0-flash-exp",
                    google_api_key=self.api_key,
                    temperature=0.3
                )
                logger.info("✅ Orchestrator initialized with Gemini")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze user query and determine intent
        """
        # Simple keyword-based routing (will be enhanced with LLM)
        query_lower = query.lower()
        
        # Career-related
        if any(word in query_lower for word in ['job', 'career', 'apply', 'resume', 'interview', 'hiring']):
            return {
                "agent": AgentType.CAREER.value,
                "confidence": 0.9,
                "reasoning": "Career-related query detected"
            }
        
        # Travel-related
        if any(word in query_lower for word in ['train', 'bus', 'flight', 'travel', 'ticket', 'route']):
            return {
                "agent": AgentType.TRAVEL.value,
                "confidence": 0.9,
                "reasoning": "Travel-related query detected"
            }
        
        # Local services
        if any(word in query_lower for word in ['near me', 'nearby', 'hospital', 'restaurant', 'store']):
            return {
                "agent": AgentType.LOCAL.value,
                "confidence": 0.9,
                "reasoning": "Local service query detected"
            }
        
        # Shopping
        if any(word in query_lower for word in ['buy', 'purchase', 'price', 'shop', 'order']):
            return {
                "agent": AgentType.SHOPPING.value,
                "confidence": 0.85,
                "reasoning": "Shopping query detected"
            }
        
        # Default to search
        return {
            "agent": AgentType.SEARCH.value,
            "confidence": 0.7,
            "reasoning": "General information query"
        }
    
    async def route_task(self, query: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Main routing function - determines which agent handles the task
        """
        analysis = await self.analyze_query(query)
        
        logger.info(f"🎯 Query routed to: {analysis['agent']}")
        logger.info(f"🎯 Confidence: {analysis['confidence']}")
        
        return {
            "status": "routed",
            "target_agent": analysis['agent'],
            "confidence": analysis['confidence'],
            "reasoning": analysis['reasoning'],
            "original_query": query
        }

# Global instance
orchestrator = Orchestrator()