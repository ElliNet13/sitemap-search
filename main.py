import asyncio
import aiohttp
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

async def fetch_sitemap(session, sitemap_url, show_errors, progress_bar, total_count):
    """
    Fetches the sitemap XML from the specified URL and extracts the URLs along with their titles.

    Args:
        session (aiohttp.ClientSession): The aiohttp session to use for the request.
        sitemap_url (str): The URL of the sitemap XML.
        show_errors (bool): Flag to determine if errors should be shown for child sitemaps.
        progress_bar (tqdm): The tqdm progress bar object.
        total_count (int): Total number of tasks to process.

    Returns:
        tuple: A tuple containing the list of dictionaries with sitemap data and a list of errors.
    """
    errors = []
    sitemap_data = []
    try:
        async with session.get(sitemap_url) as response:
            if response.status == 200:
                xml_text = await response.text()
                xml_data = ET.fromstring(xml_text)

                # Determine the namespace used
                namespace = None
                if xml_data.tag.startswith(f'{{{NAMESPACE_0_9}}}'):
                    namespace = NAMESPACE_0_9
                elif xml_data.tag.startswith(f'{{{NAMESPACE_0_84}}}'):
                    namespace = NAMESPACE_0_84

                if not namespace:
                    if show_errors:
                        errors.append(f'Unsupported sitemap namespace in {sitemap_url}')
                    return sitemap_data, errors

                # Process <url> elements
                urls = xml_data.findall(f'.//{{{namespace}}}url')
                tasks = [process_url(session, url, namespace) for url in urls]

                if progress_bar:
                    results = []
                    for coro in tqdm(asyncio.as_completed(tasks), total=len(tasks), desc="Processing URLs"):
                        try:
                            results.append(await coro)
                            progress_bar.update(1)
                        except Exception as e:
                            if show_errors:
                                errors.append(f'Error processing URL: {e}')
                            results.append({'title': 'Error', 'link': 'Error'})
                    sitemap_data.extend(results)
                else:
                    results = await asyncio.gather(*tasks)
                    sitemap_data.extend(results)

                # Process <sitemap> elements
                sitemaps = xml_data.findall(f'.//{{{namespace}}}sitemap')
                if progress_bar:
                    nested_tasks = [
                        fetch_sitemap(session, sitemap.find(f'{{{namespace}}}loc').text, show_errors, progress_bar, len(sitemaps))
                        for sitemap in sitemaps
                    ]
                    nested_results = []
                    for coro in tqdm(asyncio.as_completed(nested_tasks), total=len(nested_tasks), desc="Processing Sitemaps"):
                        result, nested_errors = await coro
                        nested_results.append(result)
                        if show_errors:
                            errors.extend(nested_errors)
                        progress_bar.update(1)
                    for nested_data in nested_results:
                        if nested_data:
                            sitemap_data.extend(nested_data)
                else:
                    nested_tasks = [fetch_sitemap(session, sitemap.find(f'{{{namespace}}}loc').text, show_errors, None, 0) for sitemap in sitemaps]
                    nested_results = await asyncio.gather(*nested_tasks)
                    for nested_data in nested_results:
                        if nested_data:
                            sitemap_data.extend(nested_data)

                return sitemap_data, errors
            else:
                if show_errors:
                    errors.append(f'Failed to fetch sitemap from {sitemap_url}: {response.status}')
                return None, errors
    except Exception as e:
        if show_errors:
            errors.append(f'Error fetching or parsing XML sitemap from {sitemap_url}: {e}')
        return None, errors

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
    # Check if -showerrors, -bar or -onebar flags are present
    show_errors = '-showerrors' in sys.argv
    progress_bar = '-bar' in sys.argv or '-onebar' in sys.argv
    one_bar = '-onebar' in sys.argv

    sitemap_url = input("Enter the URL of the sitemap XML (Leave empty to use https://ellinet13.github.io/sitemap.xml): ")
    if not sitemap_url:
        sitemap_url = "https://ellinet13.github.io/sitemap.xml"

    print("Loading sitemap...")

    errors = []

    if one_bar:
        # Initialize single progress bar
        with tqdm(total=1, desc="Processing Sitemaps") as pbar:
            async with aiohttp.ClientSession() as session:
                sitemap_data, errors = await fetch_sitemap(session, sitemap_url, show_errors, pbar, 1)
            pbar.update(1)
    else:
        async with aiohttp.ClientSession() as session:
            sitemap_data, errors = await fetch_sitemap(session, sitemap_url, show_errors, None, 0)

    if progress_bar:
        if show_errors and errors:
            print("\nErrors encountered:")
            for error in errors:
                print(f"  - {error}")

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
