import os
from openai import OpenAI

# This automatically reads OPENAI_API_KEY from environment variables
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def chat_completion(
    system: str,
    user: str,
    temperature: float = 0.7,
) -> str:
    """
    Simple OpenAI chat wrapper.
    Returns the assistant message content as plain text.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
    )

    return response.choices[0].message.content
