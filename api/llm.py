import os
from google import genai
from google.genai import types
from groq import Groq

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
groq_client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "gemini-3.6-flash"          # was gemini-2.5-flash — deprecated for new users, per Google's own error
GROQ_MODEL = "openai/gpt-oss-20b"


def _stream_gemini(messages, system: str):
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


def _stream_groq(messages, system: str):
    groq_messages = [{"role": "system", "content": system}] + [
        {"role": m["role"], "content": m["content"]} for m in messages
    ]
    stream = groq_client.chat.completions.create(
        model=GROQ_MODEL, messages=groq_messages, stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta


def stream_chat(messages, system: str):
    """messages: [{"role": "user"|"assistant", "content": str}]

    Tries Gemini first. If Gemini fails before yielding anything (quota,
    outage, deprecated model), falls back to Groq behind the same
    interface — the caller never knows which provider actually answered.
    """
    try:
        yield from _stream_gemini(messages, system)
    except Exception as e:
        print(f"[doc-qa] Gemini failed ({type(e).__name__}: {e}), falling back to Groq")
        yield from _stream_groq(messages, system)