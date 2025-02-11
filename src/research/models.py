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

class CompanyInfo(BaseModel):
    website: str
    description: str

class PersonInfo(BaseModel):
    first_name: str
    last_name: str
    linkedin_url: str
    email: Optional[str] = None
