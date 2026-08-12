import os
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
MODEL = "gemini-flash-latest"


def stream_chat(messages, system: str):
    """messages: [{"role": "user"|"assistant", "content": str}]

    Gemini uses "model" where OpenAI and Anthropic use "assistant".
    We keep the common vocabulary at our API boundary and translate here,
    so the rest of the app never learns which provider we're using.
    """
    contents = [
        types.Content(
            role="model" if m["role"] == "assistant" else "user",
            parts=[types.Part.from_text(text=m["content"])],
        )
        for m in messages
    ]

    stream = client.models.generate_content_stream(
        model=MODEL,
        contents=contents,
        config=types.GenerateContentConfig(system_instruction=system),
    )

    for chunk in stream:
        if chunk.text:
            yield chunk.text
