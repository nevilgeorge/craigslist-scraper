#!/usr/bin/env python3
"""
Craigslist scraper with Gemini-based product matching.

Searches Craigslist for products defined in a config file and uses
Google's Gemini API to evaluate if listings match the target product.
"""

import argparse
import json
import time

import requests

from craigslist import scrape_search_results
from evaluator import GeminiEvaluator


def load_config(config_path):
    """Load product configuration from a JSON file."""
    with open(config_path, "r") as f:
        return json.load(f)


def scrape_product(product_config, evaluator, session, delay=1.0):
    """
    Scrape Craigslist for a specific product.

    Args:
        product_config: Dict with product search configuration
        evaluator: GeminiEvaluator instance (or None to skip evaluation)
        session: requests.Session for connection reuse
        delay: Delay between requests in seconds

    Returns:
        Dict containing product name and list of listings
    """
    product_name = product_config["name"]
    search_term = product_config["search_term"]
    criteria = product_config.get("criteria", f"Must be a {product_name}")

    print(f"\n{'='*60}")
    print(f"Searching for: {product_name}")
    print(f"Search term: '{search_term}'")
    print(f"{'='*60}")

    listings = scrape_search_results(
        search_term=search_term,
        session=session,
        delay=delay
    )

    # Evaluate each listing with Gemini
    if evaluator:
        for i, listing in enumerate(listings):
            if listing.get("error"):
                continue

            evaluation = evaluator.evaluate(product_name, criteria, listing)
            listing["evaluation"] = evaluation

            confidence = evaluation.get('confidence', 'N/A')
            reason = evaluation.get('reason', '')
            if evaluation.get("is_match"):
                print(f"      ✓ MATCH ({confidence} confidence): {reason}")
            else:
                print(f"      ✗ No match ({confidence} confidence): {reason}")

            # Rate limit: wait between Gemini API calls
            if i < len(listings) - 1:
                time.sleep(2)

    return {
        "product_name": product_name,
        "search_term": search_term,
        "listings": listings
    }


def print_results(results):
    """Print formatted results for all products."""
    print("\n")
    print("=" * 70)
    print("FINAL RESULTS")
    print("=" * 70)

    total_listings = 0
    total_matches = 0

    for result in results:
        product_name = result["product_name"]
        listings = result["listings"]
        matches = [l for l in listings if l.get("evaluation", {}).get("is_match")]

        total_listings += len(listings)
        total_matches += len(matches)

        print(f"\n{'─'*70}")
        print(f"📦 {product_name}")
        print(f"   Search: '{result['search_term']}'")
        print(f"   Listings scraped: {len(listings)} | Matches found: {len(matches)}")
        print(f"{'─'*70}")

        if matches:
            for i, match in enumerate(matches, 1):
                eval_info = match.get("evaluation", {})
                print(f"\n   Match {i}:")
                print(f"   URL: {match['url']}")
                print(f"   Title: {match.get('title', 'N/A')}")
                print(f"   Price: {match.get('price', 'N/A')}")
                print(f"   Confidence: {eval_info.get('confidence', 'N/A')}")
                print(f"   Reason: {eval_info.get('reason', 'N/A')}")
        else:
            print(f"\n   No matches found for {product_name}")

    print(f"\n{'='*70}")
    print(f"SUMMARY: {total_listings} total listings scraped, {total_matches} total matches found")
    print(f"{'='*70}")


def main():
    parser = argparse.ArgumentParser(
        description="Scrape Craigslist listings for multiple products"
    )
    parser.add_argument(
        "--config",
        default="products.json",
        help="Path to products config JSON file (default: products.json)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between requests in seconds (default: 1.0)"
    )
    parser.add_argument(
        "--no-eval",
        action="store_true",
        help="Skip Gemini evaluation (just scrape)"
    )
    parser.add_argument(
        "--product",
        type=str,
        help="Only scrape a specific product by name (case-insensitive partial match)"
    )
    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)
    products = config.get("products", [])

    if not products:
        print("No products found in configuration file.")
        return

    # Filter to specific product if requested
    if args.product:
        products = [
            p for p in products
            if args.product.lower() in p["name"].lower()
        ]
        if not products:
            print(f"No products matching '{args.product}' found in configuration.")
            return

    # Initialize Gemini evaluator
    evaluator = None
    if not args.no_eval:
        print("Initializing Gemini API...")
        evaluator = GeminiEvaluator()

    # Create session for connection reuse
    session = requests.Session()

    # Scrape all products
    results = []
    for product_config in products:
        result = scrape_product(product_config, evaluator, session, args.delay)
        results.append(result)

    # Print results
    print_results(results)


if __name__ == "__main__":
    main()
