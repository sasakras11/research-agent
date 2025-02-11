from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from typing import List
from litellm import completion
from tavily import TavilyClient
import json
import os
import logging
from .prompts import ResearchPrompts
from .dependencies import ResearchDeps

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

# Initialize TavilyClient
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

# Constants
MAX_WEB_SEARCH_LOOPS = 2

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
    """Execute web search using Tavily"""
    logger.info(f"Performing web search with query: {ctx.deps.search_query}")
    
    search_results = tavily_client.search(
        ctx.deps.search_query, 
        include_raw_content=False, 
        max_results=4
    )
    
    search_string = format_sources(search_results["results"])
    ctx.deps.sources.extend(search_results["results"])
    ctx.deps.latest_web_search_result = search_string
    ctx.deps.research_loop_count += 1
    
    return "summarize_sources"

async def summarize_sources(ctx: RunContext[ResearchDeps]) -> str:
    """Summarize the gathered sources"""
    logger.info("Summarizing sources...")
    
    current_summary = ctx.deps.current_summary
    most_recent_web_research = ctx.deps.latest_web_search_result
    current_query = ctx.deps.search_topics[ctx.deps.current_topic_index-1]
    
    user_prompt = f"Update summary with findings from search: '{current_query}'\nResults:\n{most_recent_web_research}"
    if current_summary:
        user_prompt = f"Current summary: {current_summary}\nAdd new findings from '{current_query}':\n{most_recent_web_research}"

    response = completion(
        model="gpt-4o-mini",
        messages=[
            {"content": ResearchPrompts.SUMMARIZER, "role": "system"},
            {"content": user_prompt, "role": "user"}
        ],
        max_tokens=1000,
    )
    
    ctx.deps.current_summary = response.choices[0].message.content
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
    """Format sources into a structured text"""
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(sources, start=1):
        formatted_text += (
            f"Source {i}:\n"
            f"Title: {source['title']}\n"
            f"Url: {source['url']}\n"
            f"Content: {source['content']}\n\n"
        )
    return formatted_text.strip()

# Initialize the agent
default_system_prompt = """You are a researcher. You need to use your tools and provide a research.
You must STOP your research if you have done {max_loop} iterations.
"""

model = OpenAIModel('gpt-4o-mini')

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