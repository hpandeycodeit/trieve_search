import requests
from bs4 import BeautifulSoup
import json

# Function to fetch and parse a webpage
def fetch_page(url):
    response = requests.get(url)
    response.raise_for_status() 
    return BeautifulSoup(response.content, 'html.parser')


def extract_links(main_url):
    soup = fetch_page(main_url)
    # Extract links from sidebar
    sidebar_links = soup.find('aside').find_all('a', href=True) if soup.find('aside') else []
    sidebar_urls = [f"https://developers.webflow.com{link['href']}" for link in sidebar_links]
    
    # Extract links from main content
    main_links = soup.find_all('a', href=True)
    main_urls = [f"https://developers.webflow.com{link['href']}" for link in main_links
                 if link['href'].startswith('/data/docs/') or
                    link['href'].startswith('/data/reference/') or
                    link['href'].startswith('/designer/reference/') or
                    link['href'].startswith('/data/changelog/') or
                    link['href'].startswith('/data/docs/support/')]

    # Combine and return all unique URLs
    all_urls = list(set(sidebar_urls + main_urls))
    return all_urls


# Function to extract data from a single page and create chunks
def create_chunks_from_page(url):
    soup = fetch_page(url)
    title = soup.title.text.strip()
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

# Function to upload chunks to the API
def upload_chunks(chunks, api_url, api_key, tr_dataset):
    headers = {
        "Content-Type": "application/json",
        "TR-Dataset": tr_dataset,   
        "Authorization": f"{api_key}"   
    }
    for chunk in chunks:
        #print(chunk)
        payload = {
            "chunk_html": chunk["chunk_html"],
            "link": chunk["link"]
        }
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        if response.status_code == 400:
            print(f"Failed to upload chunk: {response.status_code}, {response.text}")
        else:
            print(f"Successfully uploaded chunk: {chunk['chunk_html']}")

page_url = 'https://developers.webflow.com/data/docs/getting-started-apps'
api_url = 'https://api.trieve.ai/api/chunk'

# Replace these with your actual API key and dataset ID
API_KEY = os.getenv('API_KEY')
TR_DATASET = os.getenv('TR_DATASET_ID')

# Extract links from the main page and all sub-pages
page_urls = extract_links(page_url)

# Iterate over each page URL, create chunks, and upload them
all_chunks = []
for page_url in page_urls:
    chunks = create_chunks_from_page(page_url)
    all_chunks.extend(chunks)

# Upload all chunks to the API
upload_chunks(all_chunks, api_url, API_KEY, TR_DATASET)
