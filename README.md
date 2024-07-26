# Sitemap Search

Sitemap Search is a Python tool designed to search for specific keywords within a website's sitemap. It helps in quickly finding and identifying pages that match the given criteria.

## Features

- Efficiently parses XML sitemaps
- Searches for keywords within the sitemap URLs
- Outputs results in a clear, easy-to-read format

## Installation

1. Clone the repository to your local machine:

    ```bash
    git clone https://github.com/ElliNet13/sitemap-search.git
    ```

2. Navigate to the project directory:

    ```bash
    cd sitemap-search
    ```

3. Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

To use the Sitemap Search tool, run the `main.py` script:

```bash
python main.py
```
### Arguments
```-showerrors``` - Shows errors for child sitemaps if this flag is present. By default, errors for child sitemaps are not shown.
```-bar``` - Enables a progress bar to display the progress of processing URLs and sitemaps.
```-cache``` - Enables caching of sitemaps and pages to a `cache` directory to speed up subsequent runs by avoiding repeated requests to the same URLs.



## How to update
It's simple as this is Github its just one command:
```bash
git pull
```
