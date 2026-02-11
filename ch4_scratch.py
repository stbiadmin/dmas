import asyncio
from picoagents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.orchestration import RoundRobinOrchestrator, MaxMessageTermination, TextMentionTermination
import os, random, requests
import numpy as np

def get_location():
    rand_cities =  [
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
    idx = random.randint(0,49)
    return rand_cities[idx]

def get_weather(location: str) -> str:
    """
    Given a location string in format "City, State/Province, Country",
    returns weather as "weather, temperature in °F".
    """
    # Extract city name (first part before comma)
    city = location.split(",")[0].strip()

    # Query wttr.in API (free, no API key needed)
    url = f"https://wttr.in/{city}?format=j1"

    response = requests.get(url, timeout=10)
    response.raise_for_status()

    data = response.json()

    # Extract current condition
    current = data["current_condition"][0]
    weather = current["weatherDesc"][0]["value"]
    temp_f = current["temp_F"]

    weather_report = f"{weather}, {temp_f}"

    return f"The weather in {location} is {weather_report}"




async def run_orchestration():
    # Create client inside async context
    client = OpenAIChatCompletionClient(
        model='gpt-4.1-mini',
        api_key=os.getenv('OPENAI_API_KEY')
    )

    weather_agent = Agent(
        name="assistant",
        description="You are a helpful assistant",
        instructions="You are helpful. Use tools when appropriate. Only return the location, weather and temperature",
        model_client=client,
        tools=[get_weather]
    )

    termination = (MaxMessageTermination(max_messages=4) |
                   TextMentionTermination(text='weather'))

    orchestrator = RoundRobinOrchestrator(
        agents=[weather_agent],
        termination=termination,
        max_iterations=1
    )

    task = f"What's the Weather in {get_location()}?"
    async for event in orchestrator.run_stream(task):
        print(event)


asyncio.run(run_orchestration())
