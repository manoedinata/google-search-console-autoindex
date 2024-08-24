from google.oauth2 import service_account
from googleapiclient.discovery import build
import requests
from bs4 import BeautifulSoup
import sys


# Path to your service account key file
KEY_FILE_LOCATION = sys.argv[1]
SCOPES = ['https://www.googleapis.com/auth/webmasters']
SITE_URL = sys.argv[2]

# Authenticate using service account
credentials = service_account.Credentials.from_service_account_file(
    KEY_FILE_LOCATION, scopes=SCOPES)

# Build the service
service = build('searchconsole', 'v1', credentials=credentials)

# Function: Submit index request
def submit_index_request(service, site_url, page_url):
    # Create the request body
    request_body = {
        'inspectionUrl': page_url,
        'siteUrl': site_url
    }

    # Execute the request to Google Search Console API
    try:
        response = service.urlInspection().index().inspect(body=request_body).execute()
        return response
    except Exception as e:
        print(f"Failed to submit URL: {page_url}, error: {e}")
        return None

# Function: Parse a sitemap/sitemap index
temp_total_urls = []
def fetch_and_parse_sitemap(sitemap: str):

    request = requests.get(sitemap)
    if not request.ok: return []

    # Parse the XML content
    xml_parse = BeautifulSoup(request.content, "xml")
    # Extract URLs
    if xml_parse.find_all("sitemap"):
        # Sitemap index = Sitemap berisi sitemap
        print("Sitemap index terdeteksi!")
        child_sitemap_urls = [loc.text for loc in xml_parse.find_all("loc")]
        for urls in child_sitemap_urls:
            fetch_and_parse_sitemap(urls)
    else:
        # Regular sitemap: fetch all <loc> elements ignoring <image:loc>
        for loc in xml_parse.find_all("loc"):
            if loc.parent.name == "url":
                temp_total_urls.append(loc.text)

    return temp_total_urls

# Get sitemaps
sitemaps = service.sitemaps().list(siteUrl=SITE_URL).execute()
sitemap_urls = [sitemap for sitemap in sitemaps.get('sitemap', [])]

# Fetch and parse each sitemap
all_urls = []
for sitemap in sitemap_urls:
    urls = fetch_and_parse_sitemap(sitemap["path"])
    all_urls.append(urls)

# Print all the URLs
for i, urls_in_each_sitemaps in enumerate(all_urls, 1):
    print(f"Sitemap {i}:")
    for url in urls_in_each_sitemaps:
        print(f"Submitting index request for: {url}")
        submit_index_request(service, SITE_URL, url)
