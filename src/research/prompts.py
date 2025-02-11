class ResearchPrompts:
    QUERY_WRITER = """
    Generate 12-15 specific search queries to thoroughly research {company_website}.
    Consider:
    - Company website sections (about, blog, careers)
    - Financial data sources (Crunchbase, LinkedIn)
    - News mentions and press releases
    - Technical documentation
    - Product reviews

    Return JSON with "queries" array.
    """

    SUMMARIZER = """Your goal is to generate a high-quality summary of the web search results.

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

    MAIN_RESEARCH_TEMPLATE = """
    Using my input website URL 
    website: /{company_website}/

    , conduct exhaustive research on the company and provide a detailed analysis of everything you can find. 
    You MUST spend at least 15,000 tokens researching this company to ensure comprehensive coverage.
    
    RESEARCH REQUIREMENTS:
    Investigate EVERY available source:
    - Complete company website and subpages
    - LinkedIn (company and executive profiles)
    - Crunchbase profile
    - Last 2 years of news articles
    - Press releases
    - Partner announcements
    - Client case studies
    - Industry analysis
    - Employee reviews
    - Patent databases
    - Job postings

    Find and analyze details about:
    - Complete founding story and history
    - ALL executive backgrounds
    - Every product and service
    - Technical specifications
    - ALL client case studies
    - Every partnership
    - Latest developments
    - Market strategy
    - Company culture
    - Industry awards

    Your output MUST include:
    - Comprehensive company overview (~1000 chars)
    - Detailed technical analysis (~1000 chars)
    - Specific client examples and metrics (~800 chars)
    - Recent news and developments (~600 chars)
    - Market position analysis (~600 chars)
    - Additional findings (~500 chars)

    CRITICAL REQUIREMENTS:
    - Minimum output: 4,000 characters
    - Must include specific dates, numbers, and metrics
    - Must provide actual client examples with results
    - Must detail ALL products/services
    - Must include latest developments (last 6 months)
    - Must provide partnership details
    - Must cross-reference everything

    Remember: You MUST spend at least 15,000 tokens on research.
    """