from flask import Flask, request, jsonify, render_template
import requests
import os
from bs4 import BeautifulSoup

app = Flask(__name__)

# Replace these with your actual API key and dataset ID
API_URL = 'https://api.trieve.ai/api/chunk/search'
API_KEY = os.getenv('API_KEY')
TR_DATASET = os.getenv('TR_DATASET_ID')

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
    search_type = data.get('search_type', 'text')  # Default to 'text' if not provided
    
    headers = {
        "Content-Type": "application/json",
        "TR-Dataset": TR_DATASET,
        "Authorization": f"{API_KEY}"
    }
    
    payload = {
        "query": query,
        "page": 1,
        "per_page": 10,
        "search_type": "hybrid"
    }
    
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        results = response.json()
        for chunk in results.get('score_chunks', []):
            #print(" chunk is --" , chunk)
            for meta in chunk.get('metadata', []):
                meta['main_heading'] = get_main_heading(meta['link'])
        return jsonify(results)
    else:
        return jsonify({"error": response.text}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
