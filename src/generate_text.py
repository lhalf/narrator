import openai

import sensitive

client = openai.OpenAI(api_key=sensitive.api_key)


def from_messages(messages):
    print("Querying ChatGPT...")
    completion = client.chat.completions.create(model="gpt-4o-mini", messages=messages)
    return completion.choices[0].message.content
