"""
Travel Agent - Transportation, Routes, and Bookings
"""

from typing import Dict, Any, List
import asyncio
import httpx
from datetime import datetime, timedelta
from loguru import logger

class TravelAgent:
    """
    Handles transportation queries, routes, and bookings
    """
    
    def __init__(self):
        self.transit_apis = {
            "germany": "https://v6.db.transport.rest",  # Deutsche Bahn API (free)
            "europe": "https://transport.rest"
        }
    
    async def search_trains(self, from_city: str, to_city: str, date: str = None) -> List[Dict]:
        """
        Search train connections (using Deutsche Bahn API - free, no key needed)
        """
        logger.info(f"🚆 Searching trains: {from_city} → {to_city}")
        
        try:
            # Use DB API to find stations
            base_url = self.transit_apis["germany"]
            
            # Search for departure station
            async with httpx.AsyncClient() as client:
                # Find station IDs
                from_response = await client.get(
                    f"{base_url}/locations",
                    params={"query": from_city, "results": 1}
                )
                to_response = await client.get(
                    f"{base_url}/locations",
                    params={"query": to_city, "results": 1}
                )
                
                if from_response.status_code == 200 and to_response.status_code == 200:
                    from_data = from_response.json()
                    to_data = to_response.json()
                    
                    if from_data and to_data:
                        from_id = from_data[0]['id']
                        to_id = to_data[0]['id']
                        
                        # Get journey options
                        journeys_response = await client.get(
                            f"{base_url}/journeys",
                            params={
                                "from": from_id,
                                "to": to_id,
                                "results": 5
                            }
                        )
                        
                        if journeys_response.status_code == 200:
                            journeys = journeys_response.json().get('journeys', [])
                            
                            results = []
                            for journey in journeys:
                                results.append({
                                    'departure': journey['legs'][0]['departure'],
                                    'arrival': journey['legs'][-1]['arrival'],
                                    'duration': journey.get('duration', 0) // 60,  # minutes
                                    'changes': len(journey['legs']) - 1,
                                    'price': journey.get('price', {}).get('amount', 'N/A')
                                })
                            
                            logger.info(f"✅ Found {len(results)} train connections")
                            return results
            
        except Exception as e:
            logger.error(f"Train search failed: {e}")
        
        return []
    
    async def get_route(self, from_location: str, to_location: str, mode: str = "public") -> Dict[str, Any]:
        """
        Get route information
        """
        logger.info(f"🗺️ Route: {from_location} → {to_location} ({mode})")
        
        if mode == "train":
            connections = await self.search_trains(from_location, to_location)
            
            if connections:
                return {
                    "status": "success",
                    "mode": "train",
                    "from": from_location,
                    "to": to_location,
                    "connections": connections,
                    "next_departure": connections[0] if connections else None
                }
        
        return {
            "status": "pending",
            "message": f"Route calculation for {mode} transport"
        }

# Global instance
travel_agent = TravelAgent()