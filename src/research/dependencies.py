from dataclasses import dataclass, field
from typing import List, Dict

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
    detailed_sources: List[dict] = field(default_factory=list)
    content_cache: Dict[str, str] = field(default_factory=dict)
    processing_chunks: List[List[dict]] = field(default_factory=list)
    parallel_summaries: List[str] = field(default_factory=list)

    def get_formatted_prompt(self) -> str:
        """Format the prompt template with the company website"""
        if self.prompt_template and self.company_website:
            return self.prompt_template.format(company_website=self.company_website)
        return ""

    def add_detailed_source(self, source: dict) -> None:
        """Add a detailed source with full content"""
        self.detailed_sources.append(source)
        if 'url' in source and 'full_content' in source:
            self.content_cache[source['url']] = source['full_content']

    async def process_sources_concurrently(self, chunk_size: int = 3) -> None:
        """Split and process sources in parallel chunks"""
        self.processing_chunks = [
            self.sources[i:i + chunk_size] 
            for i in range(0, len(self.sources), chunk_size)
        ]