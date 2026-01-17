"""
Craigslist URL building and scraping utilities.
"""

import time
from urllib.parse import urlencode, urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://sfbay.craigslist.org"


def build_search_url(search_term):
    """
    Build a Craigslist search URL.

    Args:
        search_term: The search query

    Returns:
        Complete search URL
    """
    params = {"query": search_term}
    query_string = urlencode(params)
    return f"{BASE_URL}/search/sss?{query_string}"


def get_page(url, session=None):
    """Fetch a page and return its BeautifulSoup object."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    if session is None:
        session = requests.Session()

    response = session.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def get_listing_urls(soup, base_url):
    """Extract all listing URLs from a Craigslist search results page."""
    urls = []

    # Modern Craigslist layout
    listings = soup.select("a.posting-title")
    if listings:
        for link in listings:
            href = link.get("href")
            if href:
                urls.append(urljoin(base_url, href))
        return urls

    # Alternative layout - gallery view
    listings = soup.select("li.cl-static-search-result a")
    if listings:
        for link in listings:
            href = link.get("href")
            if href:
                urls.append(urljoin(base_url, href))
        return urls

    # Older layout fallback
    listings = soup.select(".result-row a.result-title")
    if listings:
        for link in listings:
            href = link.get("href")
            if href:
                urls.append(urljoin(base_url, href))
        return urls

    return urls


def get_listing_details(soup):
    """Extract title and description from a Craigslist listing page."""
    title = None
    description = None
    price = None

    # Get title
    title_elem = soup.select_one("#titletextonly")
    if title_elem:
        title = title_elem.get_text(strip=True)
    else:
        title_elem = soup.select_one("h1.postingtitle")
        if title_elem:
            title = title_elem.get_text(strip=True)

    # Get price
    price_elem = soup.select_one(".price")
    if price_elem:
        price = price_elem.get_text(strip=True)

    # Get description
    desc_elem = soup.select_one("#postingbody")
    if desc_elem:
        for unwanted in desc_elem.select(".print-information"):
            unwanted.decompose()
        description = desc_elem.get_text(strip=True)

    return {
        "title": title,
        "description": description,
        "price": price
    }


def scrape_search_results(search_term, session=None, delay=1.0):
    """
    Scrape Craigslist search results for a given search term.

    Args:
        search_term: The search query
        session: Optional requests.Session for connection reuse
        delay: Delay between requests in seconds

    Returns:
        List of listing dicts with url, title, description, price
    """
    if session is None:
        session = requests.Session()

    url = build_search_url(search_term)
    print(f"Search URL: {url}")

    soup = get_page(url, session)
    listing_urls = get_listing_urls(soup, url)
    print(f"Found {len(listing_urls)} listings")

    listings = []

    for i, listing_url in enumerate(listing_urls, 1):
        print(f"  [{i}/{len(listing_urls)}] {listing_url}")

        try:
            listing_soup = get_page(listing_url, session)
            details = get_listing_details(listing_soup)

            listing = {
                "url": listing_url,
                **details
            }

            listings.append(listing)

            if i < len(listing_urls):
                time.sleep(delay)

        except requests.RequestException as e:
            print(f"      Error: {e}")
            listings.append({
                "url": listing_url,
                "title": None,
                "description": None,
                "price": None,
                "error": str(e)
            })

    return listings
