from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from typing import List, Dict
from litellm import completion
from tavily import TavilyClient
import json
import logging
from .web_scraper import WebScraper
from .config import Config
from .models import CompanyInfo, PersonInfo
from .email_finder import EmailFinder
from .prompts import ResearchPrompts  # Add this import

logger = logging.getLogger(__name__)

class CompanyResearchAgent:
    def __init__(self):
        self.web_scraper = WebScraper()
        self.tavily_client = TavilyClient(api_key=Config.get_api_key('TAVILY_API_KEY'))
        self.email_finder = EmailFinder()

    async def get_company_description(self, website: str) -> CompanyInfo:
        """Get basic company description from website"""
        content = await self.web_scraper.get_page_content(website)
        
        # Simple search for company overview
        search_results = self.tavily_client.search(
            f"what does {website} company do",
            max_results=2
        )
        
        # Combine and summarize information
        combined_info = f"""
        Website Content: {content or ''}
        Search Results: {json.dumps([r['content'] for r in search_results['results']])}
        """
        
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": ResearchPrompts.COMPANY_DESCRIPTION
            }, {
                "role": "user",
                "content": combined_info
            }]
        )
        
        return CompanyInfo(
            website=website,
            description=response.choices[0].message.content
        )

    def parse_titles(self, titles_input: str) -> List[str]:
        """Parse comma-separated titles into a list"""
        return [
            title.strip()
            for title in titles_input.split(",")
            if title.strip()
        ]

    async def process_company(self, website: str, titles_input: str) -> Dict:
        """Main method to process company and find people by titles"""
        # Get company info
        company_info = await self.get_company_description(website)
        
        # Parse and process titles
        titles = self.parse_titles(titles_input)
        people = await self.find_people_by_titles(website, titles)
        
        # Return combined results
        return {
            "company": company_info.dict(),
            "people": [person.dict() for person in people]
        }

    async def _extract_person_info(self, linkedin_url: str) -> PersonInfo:
        content = await self.web_scraper.get_page_content(linkedin_url)
        if not content:
            return None
            
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": ResearchPrompts.PERSON_EXTRACTOR
            }, {
                "role": "user",
                "content": content
            }],
            response_format={"type": "json_object"}
        )
        
        name_data = json.loads(response.choices[0].message.content)
        return PersonInfo(
            first_name=name_data.get('first_name', ''),
            last_name=name_data.get('last_name', ''),
            linkedin_url=linkedin_url
        )

    async def find_people_by_titles(self, website: str, titles: List[str]) -> List[PersonInfo]:
        """Find people by their titles at the company"""
        company_domain = website.split("//")[-1].split("/")[0]
        results = []
        
        for title in titles:
            # Search for person with this title
            search_results = self.tavily_client.search(
                f"{company_domain} {title} linkedin",
                max_results=2
            )
            
            if not search_results['results']:
                continue
                
            # Extract LinkedIn URLs
            linkedin_urls = [
                result['url'] for result in search_results['results']
                if 'linkedin.com/in/' in result['url']
            ]
            
            if linkedin_urls:
                # Get person details from LinkedIn URL
                person_info = await self._extract_person_info(linkedin_urls[0])
                if person_info:
                    # Find email
                    email = await self.email_finder.find_email(
                        person_info.first_name,
                        person_info.last_name,
                        company_domain
                    )
                    person_info.email = email
                    results.append(person_info)
        
        return results

# Initialize single research agent instance
try:
    research_agent = CompanyResearchAgent()
except Exception as e:
    logger.error(f"Error initializing research agent: {str(e)}")
    raise