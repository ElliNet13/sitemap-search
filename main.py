import asyncio
import aiohttp
import os
import hashlib
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
import sys
from tqdm import tqdm

"""
This script was made by ElliNet13
If you use this script please give credit.
"""
print("Made by ElliNet13")

# Define the namespaces
NAMESPACE_0_9 = 'http://www.sitemaps.org/schemas/sitemap/0.9'
NAMESPACE_0_84 = 'http://www.google.com/schemas/sitemap/0.84'

# Cache directory
CACHE_DIR = 'cache'

def get_cache_filename(url):
    """
    Generates a cache filename based on the URL's hash.

    Args:
        url (str): The URL to generate the cache filename for.

    Returns:
        str: The cache filename.
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f'{url_hash}.xml')

async def fetch_with_cache(session, url, cache_enabled):
    """
    Fetches content from a URL, using cache if enabled.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The URL to fetch the content from.
        cache_enabled (bool): Whether caching is enabled.

    Returns:
        str: The fetched content.
    """
    cache_filename = get_cache_filename(url)
    if cache_enabled and os.path.exists(cache_filename):
        with open(cache_filename, 'r', encoding='utf-8') as f:
            return f.read()
    
    async with session.get(url) as response:
        content = await response.text()
        if cache_enabled:
            os.makedirs(CACHE_DIR, exist_ok=True)
            with open(cache_filename, 'w', encoding='utf-8') as f:
                f.write(content)
        return content

async def fetch_sitemap(session, semaphore, sitemap_url, show_errors, progress_bar, cache_enabled):
    """
    Fetches the sitemap XML from the specified URL and extracts the URLs along with their titles.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        semaphore (asyncio.Semaphore): Semaphore to limit concurrent requests.
        sitemap_url (str): The URL of the sitemap XML.
        show_errors (bool): Flag to determine if errors should be shown for child sitemaps.
        progress_bar (bool): Whether to show progress bar.
        cache_enabled (bool): Whether caching is enabled.

    Returns:
        list: A list of dictionaries containing the titles and links of the URLs in the sitemap.
    """
    async with semaphore:
        try:
            xml_text = await fetch_with_cache(session, sitemap_url, cache_enabled)
            xml_data = ET.fromstring(xml_text)

            sitemap_data = []

            # Determine the namespace used
            namespace = None
            if xml_data.tag.startswith(f'
