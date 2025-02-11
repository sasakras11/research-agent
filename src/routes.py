from flask import Blueprint, render_template, request, jsonify
from src.research.agent import research_agent
import asyncio
import nest_asyncio

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

main = Blueprint('main', __name__)

@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@main.route('/research', methods=['POST'])
def research():
    website = request.form.get('website')
    titles = request.form.get('titles')
    
    if not website or not titles:
        return jsonify({'error': 'Both website URL and titles are required'}), 400

    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Use process_company instead of run
        result = loop.run_until_complete(
            research_agent.process_company(website, titles)
        )
        
        print("Result from research_agent.process_company:", result)  # Log the result
        
        return jsonify({
            'success': True,
            **result  # This includes both company and people data
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
    finally:
        loop.close()