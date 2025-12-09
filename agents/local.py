"""
Local Services Agent - Nearby facilities and services
"""

from typing import Dict, Any, List
import asyncio
import httpx
from loguru import logger

class LocalAgent:
    """
    Finds nearby services, restaurants, hospitals, etc.
    """
    
    def __init__(self):
        # Using Nominatim (OpenStreetMap) - free, no API key
        self.geocoding_api = "https://nominatim.openstreetmap.org"
        self.overpass_api = "https://overpass-api.de/api/interpreter"
    
    async def find_nearby(self, query: str, location: str = None, radius: int = 5000) -> List[Dict]:
        """
        Find nearby places using OpenStreetMap
        """
        logger.info(f"📍 Finding: {query} near {location}")
        
        try:
            async with httpx.AsyncClient() as client:
                # First, geocode the location
                if location:
                    geo_response = await client.get(
                        f"{self.geocoding_api}/search",
                        params={
                            "q": location,
                            "format": "json",
                            "limit": 1
                        },
                        headers={"User-Agent": "AI-Agent-Platform"}
                    )
                    
                    if geo_response.status_code == 200:
                        geo_data = geo_response.json()
                        if geo_data:
                            lat = float(geo_data[0]['lat'])
                            lon = float(geo_data[0]['lon'])
                            
                            # Query Overpass API for nearby places
                            overpass_query = f"""
                            [out:json];
                            node(around:{radius},{lat},{lon})
                              [name~"{query}",i];
                            out 10;
                            """
                            
                            places_response = await client.post(
                                self.overpass_api,
                                data={"data": overpass_query},
                                headers={"User-Agent": "AI-Agent-Platform"}
                            )
                            
                            if places_response.status_code == 200:
                                places = places_response.json().get('elements', [])
                                
                                results = []
                                for place in places:
                                    results.append({
                                        'name': place.get('tags', {}).get('name', 'Unknown'),
                                        'type': place.get('tags', {}).get('amenity', 'place'),
                                        'lat': place.get('lat'),
                                        'lon': place.get('lon'),
                                        'address': place.get('tags', {}).get('addr:street', 'N/A')
                                    })
                                
                                logger.info(f"✅ Found {len(results)} nearby places")
                                return results
        
        except Exception as e:
            logger.error(f"Local search failed: {e}")
        
        return []
    
    async def find_hospitals(self, location: str) -> List[Dict]:
        """Find hospitals near location"""
        return await self.find_nearby("hospital", location, radius=10000)
    
    async def find_restaurants(self, location: str, cuisine: str = None) -> List[Dict]:
        """Find restaurants near location"""
        query = f"{cuisine} restaurant" if cuisine else "restaurant"
        return await self.find_nearby(query, location)

# Global instance
local_agent = LocalAgent()