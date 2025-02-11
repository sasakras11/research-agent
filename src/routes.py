from flask import Blueprint, render_template, request, jsonify
from src.research.agent import research_agent
from src.research.dependencies import ResearchDeps
from src.research.prompts import ResearchPrompts
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
    if not website:
        return jsonify({'error': 'Website URL is required'}), 400

    # Initialize research dependencies
    research_deps = ResearchDeps(
        company_website=website,
        prompt_template=ResearchPrompts.MAIN_RESEARCH_TEMPLATE
    )

    # Run research in an event loop
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(
            research_agent.run(website, deps=research_deps)  # Note: using run instead of run_sync
        )
        
        return jsonify({
            'summary': research_deps.final_summary,
            'success': True
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'success': False
        }), 500
    finally:
        loop.close()