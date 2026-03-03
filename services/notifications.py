"""Telegram bot alert sender for watched grocery deals."""

import requests


def send_telegram_alert(bot_token: str, chat_id: str, items: list[dict]) -> bool:
    """Send a Markdown-formatted deal list to Telegram.

    items: list of dicts with keys: name, merchant, price, sale_story (optional)
    Returns True on success.
    """
    if not items:
        return False

    capped = items[:20]
    lines = ["*Edmonton Grocery Deals Alert*\n"]
    for item in capped:
        price = item.get("price", "")
        merchant = item.get("merchant", "")
        name = item.get("name", "")
        story = item.get("sale_story", "")
        line = f"• *{name}* — {price} ({merchant})"
        if story:
            line += f"\n  _{story}_"
        lines.append(line)

    if len(items) > 20:
        lines.append(f"\n_...and {len(items) - 20} more deals_")

    text = "\n".join(lines)
    resp = requests.post(
        f"https://api.telegram.org/bot{bot_token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
        },
        timeout=10,
    )
    return resp.ok
