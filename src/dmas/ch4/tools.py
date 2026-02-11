from __future__ import annotations

import random

import requests


CITIES: list[str] = [
    "Austin, Texas, USA",
    "Melbourne, Victoria, Australia",
    "Toronto, Ontario, Canada",
    "Munich, Bavaria, Germany",
    "Kyoto, Kyoto Prefecture, Japan",
    "Cape Town, Western Cape, South Africa",
    "Barcelona, Catalonia, Spain",
    "Vancouver, British Columbia, Canada",
    "Stockholm, Stockholm County, Sweden",
    "Mumbai, Maharashtra, India",
    "Lyon, Auvergne-Rhône-Alpes, France",
    "Denver, Colorado, USA",
    "Auckland, Auckland Region, New Zealand",
    "Edinburgh, Scotland, United Kingdom",
    "São Paulo, São Paulo, Brazil",
    "Milan, Lombardy, Italy",
    "Seoul, Seoul Capital Area, South Korea",
    "Portland, Oregon, USA",
    "Vienna, Vienna, Austria",
    "Buenos Aires, Buenos Aires, Argentina",
    "Dublin, Leinster, Ireland",
    "Osaka, Osaka Prefecture, Japan",
    "Montreal, Quebec, Canada",
    "Prague, Central Bohemia, Czech Republic",
    "Singapore, Central Region, Singapore",
    "Nashville, Tennessee, USA",
    "Zurich, Zurich Canton, Switzerland",
    "Brisbane, Queensland, Australia",
    "Guadalajara, Jalisco, Mexico",
    "Copenhagen, Capital Region, Denmark",
    "Chennai, Tamil Nadu, India",
    "Lisbon, Lisbon District, Portugal",
    "Calgary, Alberta, Canada",
    "Krakow, Lesser Poland, Poland",
    "San Diego, California, USA",
    "Helsinki, Uusimaa, Finland",
    "Bogotá, Cundinamarca, Colombia",
    "Perth, Western Australia, Australia",
    "Amsterdam, North Holland, Netherlands",
    "Bangalore, Karnataka, India",
    "Oslo, Oslo, Norway",
    "Santiago, Santiago Metropolitan, Chile",
    "Manchester, England, United Kingdom",
    "Marseille, Provence-Alpes-Côte d'Azur, France",
    "Hanoi, Hanoi, Vietnam",
    "Phoenix, Arizona, USA",
    "Warsaw, Masovian, Poland",
    "Nairobi, Nairobi County, Kenya",
    "Kuala Lumpur, Federal Territory, Malaysia",
    "Hamburg, Hamburg, Germany",
]


def get_location() -> str:
    """Return a random city from the curated list."""
    return random.choice(CITIES)


async def get_weather(city: str) -> str:
    """Get current weather for a city.

    Args:
        city: City name (e.g. "Tokyo" or "Austin, Texas, USA").

    Returns:
        A human-readable weather report string.
    """
    # Use just the city name (before the first comma) for the API query
    query = city.split(",")[0].strip()
    url = f"https://wttr.in/{query}?format=j1"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        current = data["current_condition"][0]
        weather = current["weatherDesc"][0]["value"]
        temp_f = current["temp_F"]
        return f"The weather in {city} is {weather}, {temp_f}°F"
    except requests.RequestException as exc:
        return f"Could not fetch weather for {city}: {exc}"


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result.

    Args:
        expression: A math expression to evaluate (e.g. "15 * 24", "sqrt(144)").

    Returns:
        The result of the expression as a string.
    """
    import math

    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed_names["abs"] = abs
    allowed_names["round"] = round
    try:
        result = eval(expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return f"{expression} = {result}"
    except Exception as exc:
        return f"Error evaluating '{expression}': {exc}"
