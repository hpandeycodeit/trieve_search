import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Replace these with your actual API key and dataset ID
API_KEY = os.getenv('API_KEY')
TR_DATASET = os.getenv('TR_DATASET_ID')
API_URL_CHUNK_SEARCH = 'https://api.trieve.ai/api/chunk/search'
API_URL_GROUP_SEARCH = 'https://api.trieve.ai/api/chunk_group/group_oriented_search'

@app.route('/')
def index():
    return  render_template('index.html')

def get_main_heading(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        main_heading = soup.find('h1')
        return main_heading.text.strip() if main_heading else 'No heading found'
    except Exception as e:
        print(f"Error fetching heading from {url}: {e}")
        return 'No heading found'

@app.route('/search', methods=['POST'])
def search_chunks():
    data = request.json
    query = data.get('query')
    search_in_gp = data.get('searchInGroups')

    page = data.get('page', 1)
    per_page = data.get('per_page', 10)

    #print(" --- --- search_in_gp -- ", search_in_gp)
    if search_in_gp:
        API_URL = API_URL_GROUP_SEARCH
    else:
        API_URL = API_URL_CHUNK_SEARCH
    #search_type = data.get('search_type', 'text')  # Default to 'text' if not provided
    
    headers = {
        "Content-Type": "application/json",
        "TR-Dataset": TR_DATASET,
        "Authorization": f"{API_KEY}"
    }
    
    payload = {
        "query": query,
        "page": page,
        "per_page": per_page,
        "search_type": "hybrid"
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        results = response.json()

        if search_in_gp:
            # Process group search results
            for group in results.get('group_chunks', []):
                #print("group is -- ", group)
                group['group_name'] = group.get('group_name')
        else:
            # Process chunk search results
            for chunk in results.get('score_chunks', []):
                for meta in chunk.get('metadata', []):
                    meta['main_heading'] = get_main_heading(meta['link'])

        print("results -- ", results)
        return jsonify(results)

    except requests.exceptions.HTTPError as err:
        error_message = f"HTTP error occurred: {err}"
        print(error_message)
        return jsonify({'error': error_message}), 500
    except Exception as e:
        error_message = f"Error occurred: {str(e)}"
        print(error_message)
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    app.run(debug=True)
