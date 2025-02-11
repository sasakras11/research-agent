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