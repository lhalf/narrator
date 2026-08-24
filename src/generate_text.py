import openai_client


def from_messages(messages):
    print("Querying ChatGPT...")
    completion = openai_client.client().chat.completions.create(model="gpt-4o-mini", messages=messages)
    return completion.choices[0].message.content


def summary_of(transcript):
    return from_messages([
        {"role": "system", "content": "Summarise this group chat in a few short bullet points."},
        {"role": "user", "content": transcript},
    ])


def answer_to(question, quoted_text):
    messages = [{"role": "system", "content": "You are a concise, helpful member of a group chat. Be brutally honest."}]
    if quoted_text:
        messages.append({"role": "user", "content": quoted_text})
    messages.append({"role": "user", "content": question})
    return from_messages(messages)
