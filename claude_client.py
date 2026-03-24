import os
import asyncio
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

SYSTEM_PROMPT = (
    "You are a helpful AI assistant powered by Claude. "
    "Be concise, accurate, and friendly. "
    "If asked who you are, say you're Claude, an AI assistant by Anthropic."
)


def _call_claude(messages: list[dict]) -> str:
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


async def get_claude_response(user_message: str, history: list[dict] | None = None) -> str:
    """Call Claude API asynchronously. Optionally pass conversation history."""
    messages = list(history or [])
    messages.append({"role": "user", "content": user_message})
    return await asyncio.to_thread(_call_claude, messages)
