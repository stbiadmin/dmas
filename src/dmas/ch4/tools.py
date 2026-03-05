from __future__ import annotations

import ast
import math
import operator
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


_WMO_WEATHER_CODES: dict[int, str] = {
    0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Foggy", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains", 80: "Slight rain showers", 81: "Moderate rain showers",
    82: "Violent rain showers", 85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _get_weather_wttr(city: str) -> str | None:
    """Try wttr.in first. Returns weather string or None on failure."""
    query = city.split(",")[0].strip()
    url = f"https://wttr.in/{query}?format=j1"
    try:
        response = requests.get(url, timeout=8)
        response.raise_for_status()
        data = response.json()
        current = data["current_condition"][0]
        weather = current["weatherDesc"][0]["value"]
        temp_f = current["temp_F"]
        return f"The weather in {city} is {weather}, {temp_f}°F"
    except (requests.RequestException, KeyError, IndexError):
        return None


def _get_weather_open_meteo(city: str) -> str | None:
    """Fallback to Open-Meteo (geocode + forecast). Returns weather string or None."""
    query = city.split(",")[0].strip()
    try:
        geo = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 1},
            timeout=8,
        )
        geo.raise_for_status()
        results = geo.json().get("results")
        if not results:
            return None
        lat, lon = results[0]["latitude"], results[0]["longitude"]

        wx = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "current": "temperature_2m,weathercode",
                "temperature_unit": "fahrenheit",
            },
            timeout=8,
        )
        wx.raise_for_status()
        current = wx.json()["current"]
        temp_f = current["temperature_2m"]
        code = current.get("weathercode", -1)
        weather = _WMO_WEATHER_CODES.get(code, "Unknown")
        return f"The weather in {city} is {weather}, {temp_f}°F"
    except (requests.RequestException, KeyError, IndexError):
        return None


async def get_weather(city: str) -> str:
    """Get current weather for a city.

    Tries Open-Meteo first, falls back to wttr.in if unavailable.

    Args:
        city: City name (e.g. "Tokyo" or "Austin, Texas, USA").

    Returns:
        A human-readable weather report string.
    """
    result = _get_weather_open_meteo(city)
    if result:
        return result
    result = _get_weather_wttr(city)
    if result:
        return result
    return f"Could not fetch weather for {city}: both Open-Meteo and wttr.in are unavailable"


_MATH_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
}

_UNARY_OPS = {
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_MATH_FUNCS = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
_MATH_FUNCS.update({"abs": abs, "round": round})

_MATH_CONSTS = {k: v for k, v in _MATH_FUNCS.items() if not callable(v)}


def _eval_node(node: ast.AST) -> float:
    """Recursively evaluate an AST node for safe math expressions."""
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value
    if isinstance(node, ast.Name):
        if node.id in _MATH_CONSTS:
            return _MATH_CONSTS[node.id]
        raise ValueError(f"Unknown name: {node.id}")
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _MATH_OPS:
            raise ValueError(f"Unsupported operator: {op_type.__name__}")
        return _MATH_OPS[op_type](_eval_node(node.left), _eval_node(node.right))
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _UNARY_OPS:
            raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
        return _UNARY_OPS[op_type](_eval_node(node.operand))
    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only direct function calls allowed")
        func_name = node.func.id
        if func_name not in _MATH_FUNCS or not callable(_MATH_FUNCS[func_name]):
            raise ValueError(f"Unknown function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        return _MATH_FUNCS[func_name](*args)
    raise ValueError(f"Unsupported expression: {ast.dump(node)}")


def _safe_eval(expression: str) -> float:
    """Parse and evaluate a math expression using AST walking."""
    tree = ast.parse(expression, mode="eval")
    return _eval_node(tree)


async def calculate(expression: str) -> str:
    """Evaluate a mathematical expression and return the result.

    Args:
        expression: A math expression to evaluate (e.g. "15 * 24", "sqrt(144)").

    Returns:
        The result of the expression as a string.
    """
    try:
        result = _safe_eval(expression)
        return f"{expression} = {result}"
    except Exception as exc:
        return f"Error evaluating '{expression}': {exc}"
