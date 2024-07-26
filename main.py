import asyncio
import aiohttp
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
import sys
import os
import hashlib
import pickle
from tqdm import tqdm

"""
This script was made by ElliNet13
If you use this script please give credit.
"""
print("Made by ElliNet13")

# Define the namespaces
NAMESPACE_0_9 = 'http://www.sitemaps.org/schemas/sitemap/0.9'
NAMESPACE_0_84 = 'http://www.google.com/schemas/sitemap/0.84'

# Create cache directory if not exists
cache_dir = "cache"
if not os.path.exists(cache_dir):
    os.makedirs(cache_dir)

async def fetch_sitemap(session, sitemap_url, show_errors, use_cache):
    """
    Fetches the sitemap XML from the specified URL and extracts the URLs along with their titles.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        sitemap_url (str): The URL of the sitemap XML.
        show_errors (bool): Flag to determine if errors should be shown for child sitemaps.
        use_cache (bool): Flag to determine if cache should be used.

    Returns:
        list: A list of dictionaries containing the titles and links of the URLs in the sitemap.
    """
    # Generate a cache key based on the URL
    cache_key = hashlib.md5(sitemap_url.encode()).hexdigest()
    cache_path = os.path.join(cache_dir, cache_key + '.pkl')

    # Load from cache if available
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    try:
        async with session.get(sitemap_url) as response:
            if response.status == 200:
                xml_text = await response.text()
                xml_data = ET.fromstring(xml_text)

                sitemap_data = []

                # Determine the namespace used
                namespace = None
                if xml_data.tag.startswith(f'{{{NAMESPACE_0_9}}}'):
                    namespace = NAMESPACE_0_9
                elif xml_data.tag.startswith(f'{{{NAMESPACE_0_84}}}'):
                    namespace = NAMESPACE_0_84

                if not namespace:
                    if show_errors:
                        print(f'Unsupported sitemap namespace in {sitemap_url}')
                    return None

                # Process <url> elements
                urls = xml_data.findall(f'.//{{{namespace}}}url')
                tasks = [process_url(session, url, namespace, use_cache, show_errors) for url in urls]
                results = await asyncio.gather(*tasks)
                sitemap_data.extend(results)

                # Process <sitemap> elements
                sitemaps = xml_data.findall(f'.//{{{namespace}}}sitemap')
                nested_tasks = [fetch_sitemap(session, sitemap.find(f'{{{namespace}}}loc').text, show_errors, use_cache) for sitemap in sitemaps]
                
                nested_results = await asyncio.gather(*nested_tasks)
                for nested_data in nested_results:
                    if nested_data:
                        sitemap_data.extend(nested_data)

                # Save to cache
                if use_cache:
                    with open(cache_path, 'wb') as f:
                        pickle.dump(sitemap_data, f)

                return sitemap_data
            else:
                if show_errors:
                    print(f'Failed to fetch sitemap from {sitemap_url}: {response.status}')
                return None
    except Exception as e:
        if show_errors:
            print(f'Error fetching or parsing XML sitemap from {sitemap_url}: {e}')
        return None

async def process_url(session, url, namespace, use_cache, show_errors):
    """
    Processes a single <url> element to extract the link and title.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (Element): The <url> XML element.
        namespace (str): The namespace used in the sitemap.
        use_cache (bool): Flag to determine if cache should be used.
        show_errors (bool): Flag to determine if errors should be shown.

    Returns:
        dict: A dictionary containing the title and link of the URL.
    """
    loc = url.find(f'{{{namespace}}}loc').text
    name = url.find(f'{{{namespace}}}name')
    title = name.text if name is not None and name.text else await fetch_title(session, loc, use_cache, show_errors)
    return {'title': title if title else loc, 'link': loc}

async def fetch_title(session, url, use_cache, show_errors):
    """
    Fetches the title of a webpage from the specified URL.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The URL of the webpage.
        use_cache (bool): Flag to determine if cache should be used.
        show_errors (bool): Flag to determine if errors should be shown.

    Returns:
        str: The title of the webpage, or None if the title cannot be fetched.
    """
    # Generate a cache key based on the URL
    cache_key = hashlib.md5(url.encode()).hexdigest()
    cache_path = os.path.join(cache_dir, cache_key + '.pkl')

    # Load from cache if available
    if use_cache and os.path.exists(cache_path):
        with open(cache_path, 'rb') as f:
            return pickle.load(f)

    try:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                title = soup.title.string.strip() if soup.title else None
                # Save to cache
                if use_cache:
                    with open(cache_path, 'wb') as f:
                        pickle.dump(title, f)
                return title
            else:
                return None
    except Exception as e:
        if show_errors:
            print(f'Error fetching or parsing HTML page {url}: {e}')
        return None

def search_sitemap(sitemap_data, search_query):
    """
    Searches for sites in the sitemap data containing the specified search query.

    Args:
        sitemap_data (list): A list of dictionaries containing the titles and links of the URLs in the sitemap.
        search_query (str): The search query to match against the site titles.

    Returns:
        list: A list of dictionaries representing the matching sites.
    """
    return [site for site in sitemap_data if search_query.lower() in site['title'].lower()]

def list_sites(sitemap_data):
    """
    Lists all sites in the sitemap data along with their titles.

    Args:
        sitemap_data (list): A list of dictionaries containing the titles and links of the URLs in the sitemap.
    """
    for index, site in enumerate(sitemap_data, start=1):
        print(f"{index}. {site['title']}")

def select_site(sitemap_data):
    """
    Allows the user to select a site from the sitemap data and returns its URL.

    Args:
        sitemap_data (list): A list of dictionaries containing the titles and links of the URLs in the sitemap.

    Returns:
        str: The URL of the selected site.
    """
    list_sites(sitemap_data)
    selection = input("Enter the number of the site to see its URL: ")
    try:
        selection_index = int(selection) - 1
        if 0 <= selection_index < len(sitemap_data):
            return sitemap_data[selection_index]['link']
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Invalid input. Please enter a number.")
        return None

async def main():
    # Check if -showerrors flag is present
    show_errors = '-showerrors' in sys.argv
    use_cache = '-cache' in sys.argv
    show_bar = '-bar' in sys.argv

    sitemap_url = input("Enter the URL of the sitemap XML (Leave empty to use https://ellinet13.github.io/sitemap.xml): ")
    if not sitemap_url:
        sitemap_url = "https://ellinet13.github.io/sitemap.xml"

    print("Loading sitemap...")
    async with aiohttp.ClientSession() as session:
        if show_bar:
            sitemap_data = await fetch_sitemap(session, sitemap_url, show_errors, use_cache)
        else:
            sitemap_data = await fetch_sitemap(session, sitemap_url, show_errors, use_cache)
    
    if sitemap_data:
        print("Done!")
        search_query = input("Enter the search query (Leave empty to get all pages): ")
        sitemap_data = search_sitemap(sitemap_data, search_query)
        site_url = select_site(sitemap_data)
        if site_url:
            print("Page URL:", site_url)
            open_link = input("Would you like to open it? (yes/no): ").strip().lower()
            if open_link == 'yes':
                import webbrowser
                webbrowser.open(site_url)
        else:
            print("No site selected.")
    else:
        print("Failed to load sitemap.")

if __name__ == "__main__":
    asyncio.run(main())
