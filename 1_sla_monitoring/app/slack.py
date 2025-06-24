import os

# Simple print-based alert logging (replaced Slack with print)
SLACK_WEBHOOK = os.getenv("SLACK_WEBHOOK_URL", "")
async def send_alert(payload: dict):
    print("ALERT", payload, flush=True)
    if not SLACK_WEBHOOK:
        return
    import httpx
    async with httpx.AsyncClient() as client:
        try:
            await client.post(SLACK_WEBHOOK, json=payload)
        except Exception as e:
            print("Slack send failed", e, flush=True)