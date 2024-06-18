import requests
from bs4 import BeautifulSoup
import json
import os

headers = {}

def set_headers():
    global headers
    headers = {
        "Content-Type": "application/json",
        "TR-Dataset": os.getenv('TR_DATASET'),
        "Authorization": f"{os.getenv('API_KEY')}",
    }

# Fetch and parse a webpage
def fetch_page(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.content, 'html.parser')
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None

# Extract links from a URL/page
def extract_links(main_url):
    soup = fetch_page(main_url)
    if not soup:
        return []

    # Extract all links
    all_links = soup.find_all('a', href=True)
    all_urls = [f"https://developers.webflow.com{link['href']}" for link in all_links if link['href'].startswith('/')]

    relevant_patterns = [
        '/designer/',
        '/data/',
    ]

    filtered_urls = [url for url in all_urls if any(pattern in url for pattern in relevant_patterns)]
    print("filtered_urls -", filtered_urls)
    return list(set(filtered_urls))


# Extract data from a single page and create chunks
def create_chunks_from_page(url):
    soup = fetch_page(url)

    if soup is None:
        return []

    try:
        title = soup.title.text.strip()
    except AttributeError as e:
        print(f"Error retrieving title from {url}: {e}")
        title = ""

    paragraphs = soup.find_all('p')
    chunks = []
    for paragraph in paragraphs:
        chunk = {
            "chunk_html": paragraph.text.strip(),
            "link": url,
            "convert_html_to_text": False
        }
        chunks.append(chunk)
    return chunks

# Upload chunks to the API
def upload_chunk(chunks):
    api_url = "https://api.trieve.ai/api/chunk"

    #print(chunk)
    payload = {
        "chunk_html": chunk["chunk_html"],
        "link": chunk["link"]
    }
    try:
        response = requests.post(api_url, json=payload, headers=headers)
        response.raise_for_status()
        chunk_id = response.json().get("chunk_metadata", {}).get("id")
        print(f"Successfully created chunk: {chunk_id}")
        return chunk_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating chunk: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        return None

# Create a Group
def create_group(group_name):

    api_url = "https://api.trieve.ai/api/chunk_group"
    
    if not group_name: 
        group_name = "other"

    data = {"description": f"This is the group {group_name}",
    "metadata": None,
    "name": group_name,
    "tag_set": [group_name],
    "tracking_id": None,
    "upsert_by_tracking_id": True
    }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()

        print("response for group is --++>>> ", response.json().get("id"))
        group_id = response.json().get("id")
        print(f"Successfully created group: {group_id}")
        return group_id
    except requests.exceptions.RequestException as e:
        print(f"Error creating group {group_name}: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        return None

# Add chunk to the group
def add_chunk_to_group(chunk_id, group_id):

    api_url = f"https://api.trieve.ai/api/chunk_group/chunk/{group_id}"

    data = {
        "chunk_id": chunk_id,
        "tracking_id": None
        }
    try:
        response = requests.post(api_url, json=data, headers=headers)
        response.raise_for_status()
        print(f"Successfully added chunk {chunk_id} to group {group_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error adding chunk {chunk_id} to group {group_id}: {e}")
        if response.content:
            print(f"Response content: {response.content}")
        # Retry mechanism for 502 errors
        if response.status_code == 502:
            print("Retrying in 30 seconds...")
            time.sleep(30)
            add_chunk_to_group(chunk_id, group_id, api_key, tr_dataset)


if __name__ == '__main__':

    # Webflow Docs URL
    url = 'https://developers.webflow.com/data/docs/getting-started-apps'


    set_headers()

    # Scrape the main URL and extract all relevant links
    all_urls = extract_links(url)

    for page_url in all_urls:
        # Create a group name by using the last part of the URL
        group_name = page_url.rstrip('/').split('/')[-1]

        chunks = create_chunks_from_page(page_url)

        if chunks:
           group_id = create_group(group_name)
           if group_id:
               for chunk in chunks:
                   chunk_id = upload_chunk(chunk)
                   if chunk_id:
                       add_chunk_to_group(chunk_id, group_id)
