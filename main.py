import asyncio
import aiohttp
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
import sys

"""
This script was made by ElliNet13
If you use this script please give credit.
"""
print("Made by ElliNet13")

# Define the namespaces
NAMESPACE_0_9 = 'http://www.sitemaps.org/schemas/sitemap/0.9'
NAMESPACE_0_84 = 'http://www.google.com/schemas/sitemap/0.84'

async def fetch_sitemap(session, sitemap_url, show_errors):
    """
    Fetches the sitemap XML from the specified URL and extracts the URLs along with their titles.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        sitemap_url (str): The URL of the sitemap XML.
        show_errors (bool): Flag to determine if errors should be shown for child sitemaps.

    Returns:
        list: A list of dictionaries containing the titles and links of the URLs in the sitemap.
    """
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
                    print(f'Unsupported sitemap namespace in {sitemap_url}')
                    return None

                # Process <url> elements
                urls = xml_data.findall(f'.//{{{namespace}}}url')
                tasks = [process_url(session, url, namespace) for url in urls]
                results = await asyncio.gather(*tasks)
                sitemap_data.extend(results)

                # Process <sitemap> elements
                sitemaps = xml_data.findall(f'.//{{{namespace}}}sitemap')
                if show_errors:
                    nested_tasks = [fetch_sitemap(session, sitemap.find(f'{{{namespace}}}loc').text, show_errors) for sitemap in sitemaps]
                else:
                    nested_tasks = [fetch_sitemap(session, sitemap.find(f'{{{namespace}}}loc').text, False) for sitemap in sitemaps]
                
                nested_results = await asyncio.gather(*nested_tasks)
                for nested_data in nested_results:
                    if nested_data:
                        sitemap_data.extend(nested_data)

                return sitemap_data
            else:
                print(f'Failed to fetch sitemap from {sitemap_url}: {response.status}')
                return None
    except Exception as e:
        print(f'Error fetching or parsing XML sitemap from {sitemap_url}: {e}')
        return None

async def process_url(session, url, namespace):
    """
    Processes a single <url> element to extract the link and title.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (Element): The <url> XML element.
        namespace (str): The namespace used in the sitemap.

    Returns:
        dict: A dictionary containing the title and link of the URL.
    """
    loc = url.find(f'{{{namespace}}}loc').text
    name = url.find(f'{{{namespace}}}name')
    title = name.text if name is not None and name.text else await fetch_title(session, loc)
    return {'title': title if title else loc, 'link': loc}

async def fetch_title(session, url):
    """
    Fetches the title of a webpage from the specified URL.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        url (str): The URL of the webpage.

    Returns:
        str: The title of the webpage, or None if the title cannot be fetched.
    """
    try:
        async with session.get(url) as response:
            if response.status == 200:
                soup = BeautifulSoup(await response.text(), 'html.parser')
                return soup.title.string.strip() if soup.title else None
            else:
                return None
    except Exception as e:
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
    
    sitemap_url = input("Enter the URL of the sitemap XML (Leave empty to use https://ellinet13.github.io/sitemap.xml): ")
    if not sitemap_url:
        sitemap_url = "https://ellinet13.github.io/sitemap.xml"

    print("Loading sitemap...")
    async with aiohttp.ClientSession() as session:
        sitemap_data = await fetch_sitemap(session, sitemap_url, True)
    
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
