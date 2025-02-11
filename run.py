import sys
import os
import asyncio
import nest_asyncio

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Apply nest_asyncio
nest_asyncio.apply()

from src import create_app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000, threaded=True)