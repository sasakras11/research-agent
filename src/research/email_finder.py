import aiohttp
from typing import Optional
import logging
from .config import Config

logger = logging.getLogger(__name__)

class EmailFinder:
    """Email finder using FindyMail API"""
    
    def __init__(self):
        self.api_key = Config.get_api_key('FINDYMAIL_API_KEY')
        self.base_url = "https://app.findymail.com/api/search/name"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def find_email(self, first_name: str, last_name: str, domain: str, linkedin_url: Optional[str] = None) -> Optional[str]:
        """Find email using FindyMail API"""
        try:
            full_name = f"{first_name} {last_name}"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.base_url,
                    headers=self.headers,
                    json={
                        "name": full_name,
                        "domain": domain,
                        # Could add webhook_url here if needed
                        "linkedin_url": linkedin_url  # Additional context that might help
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("contact", {}).get("email"):
                            return data["contact"]["email"]
                    elif response.status == 402:
                        logger.error("FindyMail API: No credits remaining")
                    elif response.status == 423:
                        logger.error("FindyMail API: Rate limited")
                    else:
                        logger.error(f"FindyMail API error: {response.status}")
            
            # Fallback to pattern-based email if API fails
            return f"{first_name.lower()}.{last_name.lower()}@{domain}"
            
        except Exception as e:
            logger.error(f"Error finding email: {str(e)}")
            return None
