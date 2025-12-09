"""
Advanced Orchestrator with Full Gemini Integration
"""

from typing import Dict, Any, Optional
from loguru import logger
import os
from pydantic import BaseModel, Field

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.output_parsers import PydanticOutputParser
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

class AgentRouting(BaseModel):
    """Agent routing decision"""
    agent: str = Field(description="Target agent name")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Why this agent was chosen")
    parameters: Dict[str, Any] = Field(default={}, description="Extracted parameters")

class AdvancedOrchestrator:
    """
    AI-powered orchestrator using Gemini for intelligent routing
    """
    
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.llm = None
        
        if LANGCHAIN_AVAILABLE and self.api_key:
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-2.0-flash-exp",
                google_api_key=self.api_key,
                temperature=0.1
            )
            logger.info("✅ Advanced Orchestrator initialized with Gemini 2.0")
    
    async def analyze_with_ai(self, query: str, context: Optional[Dict] = None) -> AgentRouting:
        """
        Use Gemini to analyze query and route to best agent
        """
        
        if not self.llm:
            # Fallback to keyword matching
            return await self._keyword_routing(query)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an intelligent task router for an AI agent platform.
            
Available agents:
- search: General web search, information lookup, facts, definitions
- career: Job search, career advice, resume help, applications
- travel: Transportation, routes, trains, buses, flights, bookings
- local: Nearby places, restaurants, hospitals, services
- shopping: Product search, price comparison, purchases
- data: Analytics, monitoring, tracking

Analyze the user query and decide which agent should handle it.
Return JSON with: agent, confidence (0-1), reasoning, parameters (extracted entities)"""),
            ("user", "Query: {query}\n\nContext: {context}")
        ])
        
        try:
            chain = prompt | self.llm
            
            result = await chain.ainvoke({
                "query": query,
                "context": str(context) if context else "No prior context"
            })
            
            # Parse response
            content = result.content
            
            # Extract agent routing (simple parsing)
            if "career" in content.lower() or "job" in query.lower():
                agent = "career"
            elif "travel" in content.lower() or "train" in query.lower() or "bus" in query.lower():
                agent = "travel"
            elif "near" in query.lower() or "nearby" in query.lower():
                agent = "local"
            elif "buy" in query.lower() or "price" in query.lower():
                agent = "shopping"
            else:
                agent = "search"
            
            return AgentRouting(
                agent=agent,
                confidence=0.9,
                reasoning=f"Gemini analysis: {content[:200]}",
                parameters={}
            )
            
        except Exception as e:
            logger.error(f"AI routing failed: {e}")
            return await self._keyword_routing(query)
    
    async def _keyword_routing(self, query: str) -> AgentRouting:
        """Fallback keyword-based routing"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['job', 'career', 'apply', 'resume']):
            return AgentRouting(agent="career", confidence=0.8, reasoning="Career keywords detected")
        elif any(word in query_lower for word in ['train', 'bus', 'flight', 'travel']):
            return AgentRouting(agent="travel", confidence=0.8, reasoning="Travel keywords detected")
        elif any(word in query_lower for word in ['near', 'nearby', 'hospital', 'restaurant']):
            return AgentRouting(agent="local", confidence=0.8, reasoning="Local search keywords detected")
        else:
            return AgentRouting(agent="search", confidence=0.7, reasoning="Default to search")

# Global instance
advanced_orchestrator = AdvancedOrchestrator()