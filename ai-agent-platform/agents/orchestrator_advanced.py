"""
Advanced Orchestrator with Cost-Effective Claude Haiku Integration
Uses keyword-based routing first, Claude Haiku only for ambiguous queries
"""

from typing import Dict, Any, Optional, List
import os
from pydantic import BaseModel, Field
from loguru import logger

try:
    from anthropic import AsyncAnthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

class AgentRouting(BaseModel):
    agent: str = Field(description="Target agent name")
    confidence: float = Field(description="Confidence score 0-1")
    reasoning: str = Field(description="Why this agent was chosen")
    parameters: Dict[str, Any] = Field(default={}, description="Extracted parameters")

class KeywordRule(BaseModel):
    keywords: List[str]
    agent: str
    confidence: float
    reasoning: str
    parameters: Dict[str, Any] = Field(default={})

class AdvancedOrchestrator:
    def __init__(self, agents: Optional[Dict[str, Any]] = None):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.client = None
        self.agents = agents or {}

        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)

        # Keyword-based routing rules (cost-free)
        self.keyword_rules = [
            KeywordRule(
                keywords=["job", "career", "apply", "resume", "hiring", "position", "work", "employment"],
                agent="career",
                confidence=0.95,
                reasoning="Career-related keywords detected",
                parameters={"query_type": "job_search"}
            ),
            KeywordRule(
                keywords=["train", "bus", "flight", "travel", "route", "transport", "journey", "booking"],
                agent="travel",
                confidence=0.95,
                reasoning="Travel/transportation keywords detected",
                parameters={"query_type": "transport"}
            ),
            KeywordRule(
                keywords=["near", "nearby", "hospital", "restaurant", "hotel", "store", "shop", "location"],
                agent="local",
                confidence=0.90,
                reasoning="Local services/location keywords detected",
                parameters={"query_type": "local_search"}
            ),
            KeywordRule(
                keywords=["buy", "price", "purchase", "shop", "product", "cost", "expensive", "shopping"],
                agent="transaction",
                confidence=0.90,
                reasoning="Shopping/purchase keywords detected",
                parameters={"query_type": "product_search"}
            ),
            KeywordRule(
                keywords=["movie", "film", "show", "watch", "entertainment", "game", "music", "cinema"],
                agent="entertainment",
                confidence=0.85,
                reasoning="Entertainment/media keywords detected",
                parameters={"query_type": "media_search"}
            ),
            KeywordRule(
                keywords=["task", "todo", "schedule", "calendar", "meeting", "organize", "reminder"],
                agent="productivity",
                confidence=0.85,
                reasoning="Productivity/organization keywords detected",
                parameters={"query_type": "task_management"}
            ),
            KeywordRule(
                keywords=["analytics", "stats", "monitor", "track", "dashboard", "performance", "metrics"],
                agent="monitoring",
                confidence=0.85,
                reasoning="Analytics/monitoring keywords detected",
                parameters={"query_type": "analytics"}
            ),
            KeywordRule(
                keywords=["email", "message", "social", "post", "communicate", "chat", "contact"],
                agent="communication",
                confidence=0.80,
                reasoning="Communication/social keywords detected",
                parameters={"query_type": "communication"}
            ),
            KeywordRule(
                keywords=["search", "find", "lookup", "information", "what", "how", "why", "when"],
                agent="search",
                confidence=0.70,
                reasoning="General search/information keywords detected",
                parameters={"query_type": "general_search"}
            ),
            KeywordRule(
                keywords=["web", "browser", "scrape", "automation", "crawl", "site", "page"],
                agent="browser",
                confidence=0.80,
                reasoning="Web browsing/automation keywords detected",
                parameters={"query_type": "web_automation"}
            ),
            KeywordRule(
                keywords=["data", "crawl", "large", "scale", "web", "archive", "bulk"],
                agent="common_crawl",
                confidence=0.75,
                reasoning="Large-scale data/web crawling keywords detected",
                parameters={"query_type": "bulk_data"}
            )
        ]

    def _keyword_routing(self, query: str) -> Optional[AgentRouting]:
        """Fast keyword-based routing - no API costs"""
        query_lower = query.lower()
        best_match = None
        best_score = 0

        for rule in self.keyword_rules:
            # Check if any keyword from the rule appears in the query
            if any(keyword in query_lower for keyword in rule.keywords):
                # Use confidence directly if any keyword matches
                score = rule.confidence
                if score > best_score:
                    best_score = score
                    best_match = rule

        if best_match:
            return AgentRouting(
                agent=best_match.agent,
                confidence=best_score,
                reasoning=best_match.reasoning,
                parameters=best_match.parameters
            )

        return None

    async def _claude_routing(self, query: str, context: Optional[Dict] = None) -> AgentRouting:
        """Use Claude Haiku for ambiguous queries only"""
        if not self.client:
            return AgentRouting(
                agent="search",
                confidence=0.5,
                reasoning="No Claude client available, falling back to search",
                parameters={"query_type": "general_search"}
            )

        prompt = f"""You are an intelligent task router for an AI agent platform.

Available agents:
- search: General web search, information lookup, facts, definitions
- career: Job search, career advice, resume help, applications
- travel: Transportation, routes, trains, buses, flights, bookings
- local: Nearby places, restaurants, hospitals, services
- transaction: Shopping, purchases, price comparison, product search
- communication: Email, messaging, social media, communication
- entertainment: Movies, shows, games, music, entertainment
- productivity: Tasks, scheduling, organization, reminders
- monitoring: System monitoring, performance tracking, analytics
- browser: Web automation, scraping, browser control
- common_crawl: Large-scale web data analysis

User Query: {query}

Context: {str(context) if context else "No prior context"}

Analyze the query and return ONLY a JSON object with these exact fields:
{{
    "agent": "agent_name",
    "confidence": 0.95,
    "reasoning": "Brief explanation",
    "parameters": {{"key": "value"}}
}}

Choose the most appropriate agent based on the query intent."""

        try:
            response = await self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=200,
                temperature=0.1,
                system="You are a task routing AI. Always respond with valid JSON only.",
                messages=[{"role": "user", "content": prompt}]
            )

            content = response.content[0].text.strip()

            # Parse JSON response
            import json
            result = json.loads(content)

            return AgentRouting(
                agent=result.get("agent", "search"),
                confidence=float(result.get("confidence", 0.5)),
                reasoning=result.get("reasoning", "Claude analysis"),
                parameters=result.get("parameters", {})
            )

        except Exception as e:
            logger.error(f"Claude routing failed: {e}")
            return AgentRouting(
                agent="search",
                confidence=0.5,
                reasoning=f"Claude routing failed: {str(e)}",
                parameters={"query_type": "general_search"}
            )

    async def analyze_with_ai(self, query: str, context: Optional[Dict] = None) -> AgentRouting:
        """Hybrid routing: Keywords first, Claude for ambiguous queries"""
        # Try keyword routing first (free)
        keyword_result = self._keyword_routing(query)
        if keyword_result:
            logger.info(f"Keyword routing: {keyword_result.agent} (confidence: {keyword_result.confidence})")
            return keyword_result

        # Fall back to Claude Haiku for ambiguous queries
        logger.info("No strong keyword match, using Claude Haiku")
        claude_result = await self._claude_routing(query, context)
        return claude_result

    async def execute(self, query: str, user_id: str = "anonymous", context: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute agent routing and call appropriate agent"""
        routing = await self.analyze_with_ai(query, context)
        agent_name = routing.agent

        if agent_name not in self.agents:
            return {
                "status": "error",
                "message": f"Unknown agent: {agent_name}",
                "routing": routing.dict()
            }

        agent = self.agents[agent_name]

        try:
            # Try different execution methods with flexible signatures
            if hasattr(agent, "search"):
                result = await agent.search(query)
            elif hasattr(agent, "execute"):
                # Try different signatures for execute method
                try:
                    # Try with all parameters
                    result = await agent.execute(query, user_id, context)
                except TypeError:
                    try:
                        # Try with query only
                        result = await agent.execute(query)
                    except TypeError:
                        try:
                            # Try with query and user_id
                            result = await agent.execute(query, user_id)
                        except TypeError:
                            result = {"status": "error", "message": f"Agent {agent_name} execute method signature not supported"}
            else:
                result = {"status": "error", "message": f"Agent {agent_name} has no suitable execution method"}

            return {
                "status": "success",
                "agent": agent_name,
                "confidence": routing.confidence,
                "reasoning": routing.reasoning,
                "result": result
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {e}")
            return {
                "status": "error",
                "agent": agent_name,
                "error": str(e),
                "routing": routing.dict()
            }

# Global instance for backward compatibility
advanced_orchestrator = AdvancedOrchestrator()
