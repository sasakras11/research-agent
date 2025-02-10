from pydantic_ai import Agent, RunContext, Tool
from pydantic_ai.models.openai import OpenAIModel
from dotenv import load_dotenv
from IPython.display import display, Markdown  # Capital "I"
from pydantic import BaseModel
from dataclasses import dataclass, field
from typing import List
from litellm import completion
from tavily import TavilyClient
import json
import litellm
import os
import nest_asyncio
import logging

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

# MAKE SURE to set the TAVILY_API_KEY environment variable
# export TAVILY_API_KEY=<your_tavily_api_key>

# Enable async support in Jupyter
nest_asyncio.apply()

# Load environment variables
load_dotenv()

# Initialize TavilyClient
tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))

# Set LiteLLM verbosity
litellm.set_verbose = False

# Define maximum web search loops
MAX_WEB_SEARCH_LOOPS = 2

# Query writer system prompt
query_writer_system_prompt = """
Generate 7-10 specific search queries to thoroughly research {company_website}.
Consider:
- Company website sections (about, blog, careers)
- Financial data sources (Crunchbase, LinkedIn)
- News mentions and press releases
- Technical documentation
- Product reviews

Return JSON with "queries" array.
"""

# Summarizer system prompt
summarizer_system_prompt = """Your goal is to generate a high-quality summary of the web search results.

When EXTENDING an existing summary:
1. Seamlessly integrate new information without repeating what's already covered
2. Maintain consistency with the existing content's style and depth
3. Only add new, non-redundant information
4. Ensure smooth transitions between existing and new content

When creating a NEW summary:
1. Highlight the most relevant information from each source
2. Provide a concise overview of the key points related to the report topic
3. Emphasize significant findings or insights
4. Ensure a coherent flow of information

In both cases:
- Focus on factual, objective information
- Maintain a consistent technical depth
- Avoid redundancy and repetition
- DO NOT use phrases like "based on the new results" or "according to additional sources"
- DO NOT add a preamble like "Here is an extended summary ..." Just directly output the summary.
- DO NOT add a References or Works Cited section.
"""

def format_sources(sources):
    """
    Formats a list of source dictionaries into a structured text for LLM input.
    
    Args:
        sources (list): A list of dictionaries containing "title", "url", "content", and "score".
        
    Returns:
        str: Formatted text beginning with "Sources:\n\n" and each source's details on separate lines.
    """
    formatted_text = "Sources:\n\n"
    for i, source in enumerate(sources, start=1):
        formatted_text += (
            f"Source {i}:\n"
            f"Title: {source['title']}\n"
            f"Url: {source['url']}\n"
            f"Content: {source['content']}\n\n"
        )
    return formatted_text.strip()

@dataclass
class ResearchDeps:
    company_website: str = None
    prompt_template: str = None
    search_topics: List[str] = field(default_factory=list)
    current_topic_index: int = 0
    search_query: str = None
    current_summary: str = None
    final_summary: str = None
    sources: List[str] = field(default_factory=list)
    latest_web_search_result: str = None
    research_loop_count: int = 0

async def generate_search_query(ctx: RunContext[ResearchDeps]) -> str:
    if not ctx.deps.search_topics:
        response = completion(
            model="gpt-4o-mini",
            messages=[{
                "content": query_writer_system_prompt.format(company_website=ctx.deps.company_website),
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
    """Do search and collect information"""
    print("==== CALLING perform_web_search... ====")
    print(f"Search query: {ctx.deps.search_query}")

    search_results = tavily_client.search(ctx.deps.search_query, include_raw_content=False, max_results=4)
    search_string = format_sources(search_results["results"])
    ctx.deps.sources.extend(search_results["results"])
    ctx.deps.latest_web_search_result = search_string
    ctx.deps.research_loop_count += 1
    return "summarize_sources"

async def continue_or_stop_research(ctx: RunContext[ResearchDeps]) -> str:
    if ctx.deps.research_loop_count >= MAX_WEB_SEARCH_LOOPS:
        return "finalize_summary"
    if ctx.deps.current_topic_index < len(ctx.deps.search_topics):
        return "generate_search_query"
    return "finalize_summary"


# Update the summarize_sources function to use current search topic
async def summarize_sources(ctx: RunContext[ResearchDeps]) -> str:
    """Summarize the gathered sources"""
    print("==== CALLING summarize_sources... ====")
    current_summary = ctx.deps.current_summary
    most_recent_web_research = ctx.deps.latest_web_search_result
    
    # Get current search query from the list
    current_query = ctx.deps.search_topics[ctx.deps.current_topic_index-1]
    
    user_prompt = f"Update summary with findings from search: '{current_query}'\nResults:\n{most_recent_web_research}"
    if current_summary:
        user_prompt = f"Current summary: {current_summary}\nAdd new findings from '{current_query}':\n{most_recent_web_research}"

    response = completion(
        model="gpt-4o-mini",
        messages=[
            {"content": summarizer_system_prompt, "role": "system"},
            {"content": user_prompt, "role": "user"}
        ],
        max_tokens=1000,
    )
    ctx.deps.current_summary = response.choices[0].message.content
    return "continue_or_stop_research"


async def finalize_summary(ctx: RunContext[ResearchDeps]) -> str:
    """Finalize the summary"""
    print("==== CALLING finalize_summary... ====")
    all_sources = "\n".join([f"- {s['url']}" for s in ctx.deps.sources])
    ctx.deps.final_summary = f"""## Comprehensive Report for {ctx.deps.company_website}
    
{ctx.deps.current_summary}

### Sources Consulted:
{all_sources}"""
    return f"STOP: Research completed all topics"



# Initialize the agent
from pydantic_ai.models.gemini import GeminiModel
model = OpenAIModel('gpt-4o-mini')
# model = GeminiModel('gemini-1.5-flash-8b')

default_system_prompt = """You are a researcher. You need to use your tools and provide a research.
You must STOP your research if you have done {max_loop} iterations.
"""

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

website = "https://linktr.ee/"
prompt_template = """
Using my input website URL 

website: /{company_website}/


, conduct exhaustive research on the company and provide a detailed analysis of everything you can find. 
You MUST spend at least 15,000 tokens researching this company to ensure comprehensive coverage.
RESEARCH REQUIREMENTS:

Investigate EVERY available source:


Complete company website and subpages
LinkedIn (company and executive profiles)
Crunchbase profile
Last 2 years of news articles
Press releases
Partner announcements
Client case studies
Industry analysis
Employee reviews
Patent databases
Job postings


Find and analyze details about:


Complete founding story and history
ALL executive backgrounds
Every product and service
Technical specifications
ALL client case studies
Every partnership
Latest developments
Market strategy
Company culture
Industry awards


Your output MUST include:


Comprehensive company overview (~1000 chars)
Detailed technical analysis (~1000 chars)
Specific client examples and metrics (~800 chars)
Recent news and developments (~600 chars)
Market position analysis (~600 chars)
Additional findings (~500 chars)


For EVERY piece of information:


Find multiple supporting sources
Get specific examples
Include actual metrics when available
Look for recent updates
Cross-reference with other sources

CRITICAL REQUIREMENTS:

Minimum output: 4,000 characters
Must include specific dates, numbers, and metrics
Must provide actual client examples with results
Must detail ALL products/services
Must include latest developments (last 6 months)
Must provide partnership details
Must cross-reference everything

Remember: You MUST spend at least 15,000 tokens on research. My job and a $7,000 bonus depend 
on finding EVERYTHING about this company. Never stop at surface information - dig deeper 
for specifics, examples, and details
"""
research_deps = ResearchDeps(company_website=website, prompt_template=prompt_template)
result = research_agent.run_sync(website, deps=research_deps)
print(research_deps.final_summary)

