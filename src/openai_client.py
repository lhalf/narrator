import functools

import openai


@functools.cache
def client():
    import sensitive  # imported here so modules can be imported without credentials

    return openai.OpenAI(api_key=sensitive.api_key)
