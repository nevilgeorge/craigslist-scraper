"""
Gemini-based listing evaluation.
"""

import json
import os

from google import genai

EVALUATION_PROMPT_TEMPLATE = """
You are evaluating a Craigslist listing to determine if it matches a specific product.

PRODUCT BEING SEARCHED: {product_name}

LISTING TITLE: {title}
LISTING PRICE: {price}
LISTING DESCRIPTION: {description}

MATCHING CRITERIA:
{criteria}

Does this listing match the product being searched?

Respond with ONLY a JSON object in this exact format:
{{"is_match": true/false, "confidence": "high/medium/low", "reason": "brief explanation"}}

Rules:
- is_match should be true if the listing appears to be for the product being searched
- When in doubt, lean toward marking as a match - it's better to surface a potential match than miss one
- Focus on whether the core product matches, not minor details
"""


class GeminiEvaluator:
    """Evaluates listings using Google's Gemini API."""

    def __init__(self, api_key=None, model_name="gemini-2.5-flash"):
        """
        Initialize the Gemini evaluator.

        Args:
            api_key: Gemini API key. If None, reads from GEMINI_API_KEY env var.
            model_name: Gemini model to use.
        """
        api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is required. "
                "Get your API key from https://aistudio.google.com/apikey"
            )

        self.client = genai.Client(api_key=api_key)
        self.model_name = model_name

    def evaluate(self, product_name, criteria, listing):
        """
        Evaluate if a listing matches the target product.

        Args:
            product_name: Name of the product being searched
            criteria: Matching criteria description
            listing: Dict with 'title', 'description', 'price'

        Returns:
            Dict with 'is_match', 'confidence', 'reason'
        """
        title = listing.get("title")
        description = listing.get("description")
        price = listing.get("price", "N/A")

        if not title and not description:
            return {
                "is_match": False,
                "confidence": "high",
                "reason": "No title or description available"
            }

        prompt = EVALUATION_PROMPT_TEMPLATE.format(
            product_name=product_name,
            criteria=criteria,
            title=title or "N/A",
            description=description or "N/A",
            price=price or "N/A"
        )

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            response_text = response.text.strip()

            # Handle potential markdown code blocks
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            return json.loads(response_text)

        except Exception as e:
            return {
                "is_match": False,
                "confidence": "low",
                "reason": f"Evaluation error: {e}"
            }
