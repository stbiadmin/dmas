import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
response = client.chat.completions.create(
    model='gpt-4.1-mini',
    messages=[{'role': 'user', 'content': 'Say hello'}],
    max_tokens=10
)
print(response.choices[0].message.content)

