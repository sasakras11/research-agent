from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class LeadershipInfo(BaseModel):
    name: str
    title: str
    background: str
    linkedin: Optional[str] = None

class FundingInfo(BaseModel):
    total_raised: Optional[float] = None
    latest_round: Optional[str] = None
    latest_round_date: Optional[datetime] = None
    investors: List[str] = []
    valuation: Optional[float] = None

class ProductInfo(BaseModel):
    name: str
    description: str
    features: List[str] = []
    pricing: Optional[str] = None

class CompanyResearch(BaseModel):
    company_name: str
    website: str
    summary: str = ""
    founding_info: dict = {}
    leadership: List[LeadershipInfo] = []
    funding: FundingInfo = FundingInfo()
    products: List[ProductInfo] = []
    recent_developments: List[dict] = []
    market_position: str = ""
    company_culture: str = ""
    metrics: dict = {}
    last_updated: datetime = datetime.now()

class SolutionImpact(BaseModel):
    minimum: str  # Minimum expected improvement
    expected: str  # Expected/average improvement
    maximum: str  # Best case scenario
    metrics: List[str]  # Key metrics that would improve

class SolutionRecommendation(BaseModel):
    name: str  # Name of the software solution
    description: str  # What the solution does
    key_features: List[str]  # Main features needed
    implementation_time: str  # Estimated implementation timeline
    integration_points: List[str]  # Where it would integrate
    impact: SolutionImpact  # Potential impact analysis

class Challenge(BaseModel):
    category: str  # "OPERATIONAL" | "BUSINESS" | "TECHNICAL"
    description: str
    impact_level: str
    timeframe: str
    context: str
    reasoning: str
    solution_type: str  # The *type* of software solution (e.g., CRM)
    solution_name: Optional[str] = None
    solution_description: Optional[str] = None
    solution_key_features: List[str] = []
    solution_implementation_time: Optional[str] = None
    solution_integration_points: List[str] = []
    solution_impact_minimum: Optional[str] = None
    solution_impact_expected: Optional[str] = None
    solution_impact_maximum: Optional[str] = None
    solution_impact_metrics: List[str] = []
    sources: List[str] = []

class CompanyInfo(BaseModel):
    website: str
    description: str
    challenges: List[Challenge] = []

class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    linkedin_url: str
    email: Optional[str] = None
