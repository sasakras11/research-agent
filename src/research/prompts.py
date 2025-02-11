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
    3. The *type* of software solution that would be most appropriate (e.g., "CRM", "Marketing Automation", "Data Analytics", "Communication Platform").
    It is VERY IMPORTANT to provide a software solution category for each challenge.

    For the recommended software solution, you MUST also provide:
    - A detailed description of the software's functionality and how it directly addresses the challenge in the context of THIS SPECIFIC company. Aim for 2-3 sentences.
    - Key features that the software should include. List at least 3-5 key features that are particularly relevant to this company's needs. These features should be specific and not generic.
    - Potential implementation considerations (e.g., integration with existing systems, training requirements, data migration). Aim for 1-2 sentences.

    Example Output:
    {{
        "challenges": [
            {{
                "category": "OPERATIONAL",
                "description": "Inefficient lead qualification process...",
                "impact_level": "HIGH",
                "timeframe": "IMMEDIATE",
                "context": "As a lead generation service provider...",
                "reasoning": "Weak lead qualification can result in wasted marketing...",
                "software_solution_category": "CRM",
                "solution_description": "A CRM system would help Ak-Leadz streamline their lead qualification process by automating lead scoring and providing a centralized platform for managing lead interactions. This would enable them to focus on high-quality leads and improve their overall efficiency.",
                "solution_key_features": ["Lead scoring based on engagement", "Automated email sequences for lead nurturing", "Integration with LinkedIn Sales Navigator for lead enrichment", "Reporting and analytics dashboard", "Task management and reminders"],
                "solution_implementation_considerations": "Integration with existing marketing tools like HubSpot or Mailchimp would be necessary. Training would be required for the sales team to effectively use the CRM.",
                "sources": ["https://example.com/source1", "https://example.com/source2"]
            }}
        ]
    }}

    Return JSON in format:
    {{
        "challenges": [
            {{
                "category": "OPERATIONAL|BUSINESS|TECHNICAL",
                "description": "Clear problem statement",
                "impact_level": "HIGH|MEDIUM|LOW",
                "timeframe": "IMMEDIATE|SHORT_TERM|LONG_TERM",
                "context": "Why this is specifically a problem for them",
                "reasoning": "Evidence-based explanation of the challenge",
                "software_solution_category": "The *type* of software solution (e.g., CRM)",
                "solution_description": "Detailed description of the software's functionality",
                "solution_key_features": ["key feature 1", "key feature 2", ...],
                "solution_implementation_considerations": "Potential implementation considerations",
                "sources": ["supporting URLs..."]
            }}
        ]
    }}

    Focus on specific, measurable improvements. Include real metrics and KPIs where possible.
    """