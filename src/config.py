import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev')
    TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')
    MAX_WEB_SEARCH_LOOPS = 2