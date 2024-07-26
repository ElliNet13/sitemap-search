import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

"""
This script was made by ElliNet13
If you use this script please give credit.
"""
print("Made by ElliNet13")

def fetch_sitemap(sitemap_url):
    """
    Fetches the sitemap XML from the specified URL and extracts the URLs along with their titles.

    Args:
        sitemap_url (str): The URL of the sitemap XML.

    Returns:
        list: A list of dictionaries containing the titles and links of the URLs in the sitemap.
    """
    try:
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            xml_text = response.text
            xml_data = ET.fromstring(xml_text)

            sitemap_data = []
            # Process <url> elements
            urls = xml_data.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url')
            for url in urls:
                loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                name = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}name')
                title = name.text if name is not None and name.text else fetch_title(loc)
                sitemap_data.append({'title': title if title else loc, 'link': loc})

            # Process nested sitemaps
            sitemaps = xml_data.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap')
            for sitemap in sitemaps:
                loc = sitemap.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
                nested_sitemap_data = fetch_sitemap(loc)
                if nested_sitemap_data:
                    sitemap_data.extend(nested_sitemap_data)

            return sitemap_data
        else:
            print('Failed to fetch sitemap:', response.status_code)
            return None
    except Exception as e:
        print('Error fetching or parsing XML sitemap:', e)
        return None

def fetch_title(url):
    """
    Fetches the title of a webpage from the specified URL.

    Args:
        url (str): The URL of the webpage.

    Returns:
        str: The title of the webpage, or None if the title cannot be fetched.
    """
    try:
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.title.string.strip() if soup.title else None
        else:
            return None
    except Exception as e:
        print('Error fetching or parsing HTML page:', e)
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

def main():
    sitemap_url = input("Enter the URL of the sitemap XML (Leave empty to use https://ellinet13.github.io/sitemap.xml): ")
    if not sitemap_url:
        sitemap_url = "https://ellinet13.github.io/sitemap.xml"

    print("Loading sitemap...")
    sitemap_data = fetch_sitemap(sitemap_url)
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
    main()
