class ResearchPrompts:
    COMPANY_DESCRIPTION: str = """
    Analyze this information and provide a clear, concise description of what the company does.
    Focus on:
    - Main product/service
    - Target market
    - Key value proposition
    
    Keep it to 2-3 sentences maximum.
    """

    PERSON_EXTRACTOR: str = """
    Extract the person's information from the provided LinkedIn content.
    Return JSON in format:
    {
        "first_name": "...",
        "last_name": "..."
    }
    Only include these two fields.
    """

    CHALLENGES_ANALYSIS: str = """
    Analyze the top 3 most critical challenges for this company that could be solved with software solutions.
    
    For each challenge, provide:
    1. Clear problem description
    2. Business impact analysis
    3. The *type* of software solution that would be most appropriate (e.g., "CRM", "Marketing Automation", "Data Analytics", "Communication Platform")

    Return JSON in format:
    {
        "challenges": [
            {
                "category": "OPERATIONAL|BUSINESS|TECHNICAL",
                "description": "Clear problem statement",
                "impact_level": "HIGH|MEDIUM|LOW",
                "timeframe": "IMMEDIATE|SHORT_TERM|LONG_TERM",
                "context": "Why this is specifically a problem for them",
                "reasoning": "Evidence-based explanation of the challenge",
                "solution_type": "The *type* of software solution (e.g., CRM)"
                "sources": ["supporting URLs..."]
            }
        ]
    }

    Focus on specific, measurable improvements. Include real metrics and KPIs where possible.
    """