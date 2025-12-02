#%%
from openai import OpenAI
#%%
# Initialize synchronous client
sync_client = OpenAI(
    base_url="http://71.178.110.3:28080/v1",
    api_key="SPRILA",
)
#%%
# Make a single synchronous call
response = sync_client.chat.completions.create(
    model="Qwen/Qwen3-8B",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Say hello in one short sentence."},
    ],
    temperature=0.2,
)

print(response.choices[0].message.content)


#%%

from openai import AsyncOpenAI
import asyncio

#%%
client = AsyncOpenAI(
    base_url="http://71.178.110.3:28080/v1",
    api_key="SPRILA",
)

async def make_call(index):
    """Make a single async API call."""
    resp = await client.chat.completions.create(
        model="Qwen/Qwen3-8B",  # must match --served-model-name
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello in one short sentence."},
        ],
        temperature=0.8,
    )
    return f"Call {index}: {resp.choices[0].message.content}"

# pressure test: Make 64 concurrent async calls
tasks = [make_call(i) for i in range(64)]
results = await asyncio.gather(*tasks)
for result in results:
    print(result)