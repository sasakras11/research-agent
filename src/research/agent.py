from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from typing import List, Dict
from litellm import completion
from tavily import TavilyClient
import json
import os
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from .prompts import ResearchPrompts
from .dependencies import ResearchDeps
from .web_scraper import WebScraper
from .config import Config, ConfigurationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('research_agent.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize WebScraper
web_scraper = WebScraper()

# Constants
MAX_WEB_SEARCH_LOOPS = 6

async def generate_search_query(ctx: RunContext[ResearchDeps]) -> str:
    """Generate search queries based on the company website"""
    if not ctx.deps.search_topics:
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "content": ResearchPrompts.QUERY_WRITER.format(company_website=ctx.deps.company_website),
                "role": "system"
            }],
            response_format={"type": "json_object"}
        )
        data = json.loads(response.choices[0].message.content)
        ctx.deps.search_topics = data["queries"]
    
    if ctx.deps.current_topic_index < len(ctx.deps.search_topics):
        ctx.deps.search_query = ctx.deps.search_topics[ctx.deps.current_topic_index]
        ctx.deps.current_topic_index += 1
        return "perform_web_search"
    return "finalize_summary"

async def perform_web_search(ctx: RunContext[ResearchDeps]) -> str:
    """Execute concurrent web searches and content fetching"""
    logger.info(f"Performing web search with query: {ctx.deps.search_query}")
    
    search_results = tavily_client.search(
        ctx.deps.search_query, 
        include_raw_content=False, 
        max_results=10
    )
    
    # Extract URLs for concurrent fetching
    urls = [result['url'] for result in search_results["results"]]
    content_map = await web_scraper.get_pages_content(urls)
    
    # Enhance results with fetched content
    enhanced_results = []
    for result in search_results["results"]:
        content = content_map.get(result['url'])
        if content:
            result['full_content'] = content
            enhanced_results.append(result)
    
    search_string = format_sources(enhanced_results)
    ctx.deps.sources.extend(enhanced_results)
    ctx.deps.latest_web_search_result = search_string
    ctx.deps.research_loop_count += 1
    
    return "summarize_sources"

async def process_chunk(chunk: List[dict], system_prompt: str) -> str:
    """Process a chunk of sources concurrently"""
    response = await asyncio.to_thread(
        completion,
        model="gpt-4o-mini",
        messages=[
            {"content": system_prompt, "role": "system"},
            {"content": format_sources(chunk), "role": "user"}
        ],
        max_tokens=2000,
    )
    return response.choices[0].message.content

async def summarize_sources(ctx: RunContext[ResearchDeps]) -> str:
    """Concurrent summarization of sources"""
    logger.info("Summarizing sources concurrently...")
    
    # Split sources into chunks for parallel processing
    chunk_size = 3
    source_chunks = [
        ctx.deps.sources[i:i + chunk_size] 
        for i in range(0, len(ctx.deps.sources), chunk_size)
    ]
    
    # Process chunks concurrently
    tasks = [
        process_chunk(chunk, ResearchPrompts.SUMMARIZER)
        for chunk in source_chunks
    ]
    summaries = await asyncio.gather(*tasks)
    
    # Combine summaries
    combined_summary = "\n\n".join(summaries)
    ctx.deps.current_summary = combined_summary
    
    return "continue_or_stop_research"

async def continue_or_stop_research(ctx: RunContext[ResearchDeps]) -> str:
    """Decide whether to continue research or stop"""
    if ctx.deps.research_loop_count >= MAX_WEB_SEARCH_LOOPS:
        return "finalize_summary"
    if ctx.deps.current_topic_index < len(ctx.deps.search_topics):
        return "generate_search_query"
    return "finalize_summary"

async def finalize_summary(ctx: RunContext[ResearchDeps]) -> str:
    """Create the final research summary"""
    logger.info("Finalizing research summary...")
    
    all_sources = "\n".join([f"- {s['url']}" for s in ctx.deps.sources])
    ctx.deps.final_summary = f"""## Comprehensive Report for {ctx.deps.company_website}
    
{ctx.deps.current_summary}

### Sources Consulted:
{all_sources}"""
    
    return "STOP: Research completed all topics"

def format_sources(sources: List[dict]) -> str:
    """Format sources with enhanced content into structured text"""
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(sources, start=1):
        formatted_text += (
            f"Source {i}:\n"
            f"Title: {source['title']}\n"
            f"Url: {source['url']}\n"
            f"Summary: {source.get('content', '')}\n"
            f"Detailed Content: {source.get('full_content', '')[:2000]}...\n\n"
        )
    return formatted_text.strip()

# Initialize the agent
default_system_prompt = """You are a researcher. You need to use your tools and provide a research.
You must STOP your research if you have done {max_loop} iterations.
"""

try:
    # Validate configuration
    Config.validate_api_keys()
    
    # Initialize clients with validated keys
    tavily_client = TavilyClient(api_key=Config.get_api_key('TAVILY_API_KEY'))
    
    model = OpenAIModel(
        'gpt-4o-mini',
        api_key=Config.get_api_key('OPENAI_API_KEY')
    )

    research_agent = Agent(
        model,
        system_prompt=default_system_prompt.format(max_loop=MAX_WEB_SEARCH_LOOPS),
        deps_type=ResearchDeps,
        tools=[
            Tool(generate_search_query),
            Tool(perform_web_search),
            Tool(summarize_sources),
            Tool(finalize_summary),
            Tool(continue_or_stop_research)
        ]
    )

except ConfigurationError as e:
    logger.error(f"Configuration error: {str(e)}")
    raise
except Exception as e:
    logger.error(f"Error initializing research agent: {str(e)}")
    raise