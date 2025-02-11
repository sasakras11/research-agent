from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from typing import List, Dict
from litellm import completion
from tavily import TavilyClient
import json
import logging
import os
from .web_scraper import WebScraper
from .config import Config
from .models import CompanyInfo, PersonInfo, Challenge  # Add Challenge to imports
from .email_finder import EmailFinder
from .prompts import ResearchPrompts  # Add this import

logger = logging.getLogger(__name__)

class CompanyResearchAgent:
    def __init__(self):
        self.web_scraper = WebScraper()
        self.tavily_client = TavilyClient(api_key=Config.get_api_key('TAVILY_API_KEY'))
        self.email_finder = EmailFinder()
        self.solutions = self.load_solutions()

    def load_solutions(self):
        """Load software solutions from JSON file"""
        try:
            with open("solutions.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("solutions.json not found")
            return {}
        except json.JSONDecodeError:
            logger.error("Invalid JSON in solutions.json")
            return {}

    async def get_company_description(self, website: str) -> CompanyInfo:
        """Get basic company description and analyze specific challenges"""
        # Get basic description
        content = await self.web_scraper.get_page_content(website)
        
        # Gather comprehensive company context
        company_searches = [
            f"what does {website} company do",
            f"{website} company size employees funding",
            f"{website} company recent news developments",
            f"{website} company technology stack infrastructure"
        ]
        
        all_results = []
        for query in company_searches:
            results = self.tavily_client.search(query, max_results=2)
            all_results.extend(results["results"])
        
        combined_info = {
            "website_content": content or "",
            "search_results": [r["content"] for r in all_results],
            "domain": website
        }
        
        # Get company description
        description_response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": ResearchPrompts.COMPANY_DESCRIPTION
            }, {
                "role": "user",
                "content": json.dumps(combined_info)
            }]
        )
        
        description = description_response.choices[0].message.content

        # Analyze company-specific challenges with full context
        challenges_response = completion(
            model="gpt-4o-mini",
            messages=[{
                "role": "system",
                "content": ResearchPrompts.CHALLENGES_ANALYSIS
            }, {
                "role": "user",
                "content": json.dumps({
                    "company_description": description,
                    "context": combined_info
                })
            }],
            response_format={"type": "json_object"}
        )
        
        challenges_data = json.loads(challenges_response.choices[0].message.content)
        
        challenges = []
        for c in challenges_data.get("challenges", []):
            solution_type = c.get("solution_type", "N/A")  # Default value if solution_type is missing
            solution = self.solutions.get(solution_type, {})  # Get solution details from the loaded solutions
            
            challenges.append(Challenge(
                category=c.get("category", "N/A"),
                description=c.get("description", "N/A"),
                impact_level=c.get("impact_level", "N/A"),
                timeframe=c.get("timeframe", "N/A"),
                context=c.get("context", "N/A"),
                reasoning=c.get("reasoning", "N/A"),
                solution_type=solution_type,
                solution_name=solution.get("name", "N/A"),
                solution_description=solution.get("description", "N/A"),
                solution_key_features=solution.get("key_features", []),
                solution_implementation_time=solution.get("implementation_time", "N/A"),
                solution_integration_points=solution.get("integration_points", []),
                solution_impact_minimum=solution.get("impact", {}).get("minimum", "N/A"),
                solution_impact_expected=solution.get("impact", {}).get("expected", "N/A"),
                solution_impact_maximum=solution.get("impact", {}).get("maximum", "N/A"),
                solution_impact_metrics=solution.get("impact", {}).get("metrics", []),
                sources=c.get("sources", [])
            ))
        
        return CompanyInfo(
            website=website,
            description=description,
            challenges=challenges
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