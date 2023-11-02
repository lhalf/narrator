import openai


def from_messages(messages):
    print("Querying ChatGPT...")
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)
    return completion.choices[0].message.content
