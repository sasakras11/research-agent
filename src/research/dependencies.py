from dataclasses import dataclass, field
from typing import List

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

    def get_formatted_prompt(self) -> str:
        """Format the prompt template with the company website"""
        if self.prompt_template and self.company_website:
            return self.prompt_template.format(company_website=self.company_website)
        return ""