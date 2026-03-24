import asyncio
import logging
import os

from flask import Flask, jsonify, request

import bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/webhook", methods=["POST"])
def webhook():
    update = request.get_json(force=True, silent=True) or {}
    try:
        asyncio.run(bot.handle_update(update))
    except Exception as e:
        logger.error(f"Unhandled error processing update: {e}")
    return jsonify({"ok": True})


def register_webhook() -> None:
    webhook_url = os.environ.get("WEBHOOK_URL", "").rstrip("/")
    if not webhook_url:
        logger.warning("WEBHOOK_URL not set — skipping webhook registration.")
        return
    full_url = f"{webhook_url}/webhook"
    result = bot.set_webhook(full_url)
    if result.get("ok"):
        logger.info(f"Webhook registered: {full_url}")
    else:
        logger.error(f"Webhook registration failed: {result}")


if __name__ == "__main__":
    register_webhook()
    port = int(os.environ.get("PORT", 8080))
    logger.info(f"Starting server on port {port}")
    app.run(host="0.0.0.0", port=port)
