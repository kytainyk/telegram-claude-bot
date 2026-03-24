import os
import logging
import requests
from claude_client import get_claude_response

logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# In-memory conversation history per chat (resets on redeploy)
_histories: dict[int, list[dict]] = {}
MAX_HISTORY = 20  # max messages to retain per user


def send_message(chat_id: int, text: str, parse_mode: str = "HTML") -> None:
    """Send a text message to a Telegram chat."""
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
    }
    try:
        resp = requests.post(f"{TELEGRAM_API}/sendMessage", json=payload, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")


def send_typing(chat_id: int) -> None:
    """Send a 'typing…' action to the chat."""
    try:
        requests.post(
            f"{TELEGRAM_API}/sendChatAction",
            json={"chat_id": chat_id, "action": "typing"},
            timeout=5,
        )
    except Exception:
        pass


def set_webhook(webhook_url: str) -> dict:
    """Register the webhook with Telegram."""
    resp = requests.post(
        f"{TELEGRAM_API}/setWebhook",
        json={"url": webhook_url, "allowed_updates": ["message"]},
        timeout=15,
    )
    return resp.json()


async def handle_update(update: dict) -> None:
    """Process a single Telegram update object."""
    message = update.get("message", {})
    if not message:
        return

    chat_id: int = message["chat"]["id"]
    text: str = message.get("text", "").strip()

    if not text:
        send_message(chat_id, "Please send a text message.")
        return

    # --- Commands ---
    if text.startswith("/start"):
        _histories.pop(chat_id, None)
        send_message(
            chat_id,
            "👋 <b>Hi! I'm Claude</b>, an AI assistant by Anthropic.\n\n"
            "Ask me anything — I remember the context of our conversation.\n\n"
            "Commands:\n"
            "• /start — restart and clear history\n"
            "• /clear — clear conversation history\n"
            "• /help — show this message",
        )
        return

    if text.startswith("/clear"):
        _histories.pop(chat_id, None)
        send_message(chat_id, "🗑️ Conversation history cleared.")
        return

    if text.startswith("/help"):
        send_message(
            chat_id,
            "Commands:\n"
            "• /start — restart\n"
            "• /clear — clear history\n"
            "• /help — help\n\n"
            "Just type any message and I'll respond!",
        )
        return

    # --- Regular message ---
    send_typing(chat_id)

    history = _histories.setdefault(chat_id, [])

    try:
        reply = await get_claude_response(text, history)
    except Exception as e:
        logger.error(f"Claude error for chat {chat_id}: {e}")
        send_message(chat_id, "⚠️ Something went wrong. Please try again.")
        return

    # Update history (keep last MAX_HISTORY messages)
    history.append({"role": "user", "content": text})
    history.append({"role": "assistant", "content": reply})
    if len(history) > MAX_HISTORY:
        _histories[chat_id] = history[-MAX_HISTORY:]

    send_message(chat_id, reply)
