import asyncio
import os

from picoagents import Agent
from picoagents.llm import OpenAIChatCompletionClient
from picoagents.orchestration import RoundRobinOrchestrator
from picoagents.termination import MaxMessageTermination, TextMentionTermination
from picoagents.webui import serve

client = OpenAIChatCompletionClient(
    model='gpt-4.1-mini',
    api_key=os.getenv('OPENAI_API_KEY')
)

poet = Agent(
    name="poet",
    description='Haiku poet.',
    instructions='You are a haiku poet.',
    model_client=client
)

async def test_poet():
    response = await poet.run("Write a haiku about Star Wars and Imperialism")
    print(f'Poet says: {response}')
    return response

#test_haiku = asyncio.run(test_poet())

critic = Agent(
    name = 'critic',
    description='Poetry critic who provides constructive feedback on haikus.',
    instructions="You are a haiku critic."
                 "When you see a haiku, provide 2-3 specific, actionable"
                 "suggestions for improvement. Be constructive and brief"
                 "If satisfied with the haiku, restpiond with 'APPROVED'",
    model_client=client
)

async def test_critic():
    haiku = asyncio.run(test_poet())
    response = await critic.run(f'Please critique this haiku {haiku}')
    print(f"Critic says {response}")

async def run_orchestration():
    task = "Write a haiku about star wars and imperialism"
    stream = orchestrator.run_stream(task)
    async for message in stream:
        print(f"{message}")


termination = (MaxMessageTermination(max_messages=12) |
               TextMentionTermination(text="APPROVED"))

orchestrator = RoundRobinOrchestrator(
    agents=[poet,critic],
    termination=termination,
    max_iterations=30
)



serve(entities=[orchestrator], port=8070, auto_open=True)

