# Craigslist Scraper

Scrapes Craigslist listings and uses Google's Gemini API to identify products you're looking for.

## Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set your Gemini API key
export GEMINI_API_KEY="your-api-key"
```

Get your API key at: https://aistudio.google.com/apikey

## Usage

```bash
# Run for all products in config
python scraper.py

# Run for a specific product
python scraper.py --product sony

# Scrape without Gemini evaluation
python scraper.py --no-eval
```

## Configuration

Edit `products.json` to add products you want to search for:

```json
{
  "products": [
    {
      "name": "Sony RX100 camera",
      "search_term": "sony rx100",
      "criteria": "Sony RX100 camera (any version). Accessories are NOT matches."
    }
  ]
}
```

- `name`: Display name for the product
- `search_term`: What to search on Craigslist
- `criteria`: Instructions for Gemini to identify matches
