"""
Telegram Bot Webhook Routes for Astra OS API
"""

from fastapi import APIRouter, Request, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.external_adapters.telegram.bot import get_telegram_bot, shutdown_telegram_bot
from app.infrastructure.external_adapters.telegram.config import get_telegram_config
from app.config import config

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(request: Request):
    """
    Telegram webhook endpoint.
    This receives updates from Telegram and processes them through the bot.
    """
    bot = await get_telegram_bot()

    if not bot.dp:
        raise HTTPException(status_code=503, detail="Bot not initialized")

    # Get the update data
    update_data = await request.json()

    # Process the update through aiogram
    from aiogram.types import Update
    update = Update.model_validate(update_data, context={"bot": bot.bot})

    await bot.dp.feed_update(bot.bot, update)

    return {"status": "ok"}


@router.get("/webhook")
async def telegram_webhook_get():
    """Health check for webhook endpoint."""
    return {"status": "ok", "message": "Telegram webhook endpoint is ready"}


@router.post("/setup-webhook")
async def setup_telegram_webhook():
    """
    Set up the Telegram webhook.
    Call this after deploying to production to register the webhook URL.
    """
    bot = await get_telegram_bot()
    telegram_config = get_telegram_config()

    if not telegram_config.webhook_url:
        raise HTTPException(
            status_code=400,
            detail="TELEGRAM_WEBHOOK_URL not configured"
        )

    webhook_url = f"{telegram_config.webhook_url.rstrip('/')}{telegram_config.webhook_path}"

    await bot.bot.set_webhook(
        url=webhook_url,
        allowed_updates=bot.dp.resolve_used_update_types(),
        drop_pending_updates=True,
    )

    return {
        "status": "ok",
        "webhook_url": webhook_url,
        "message": "Webhook configured successfully"
    }


@router.delete("/webhook")
async def delete_telegram_webhook():
    """Delete the Telegram webhook."""
    bot = await get_telegram_bot()

    await bot.bot.delete_webhook()

    return {"status": "ok", "message": "Webhook deleted"}


@router.get("/status")
async def telegram_bot_status():
    """Get Telegram bot status."""
    bot = await get_telegram_bot()
    telegram_config = get_telegram_config()

    return {
        "bot_initialized": bot.bot is not None,
        "running": bot._running,
        "mode": "polling" if telegram_config.use_polling else "webhook",
        "webhook_url": telegram_config.webhook_url if not telegram_config.use_polling else None,
        "webhook_path": telegram_config.webhook_path,
    }


@router.post("/start-polling")
async def start_telegram_polling():
    """Start the bot in polling mode (development only)."""
    telegram_config = get_telegram_config()

    if not telegram_config.use_polling:
        raise HTTPException(
            status_code=400,
            detail="Polling mode not enabled. Set TELEGRAM_USE_POLLING=true"
        )

    bot = await get_telegram_bot()

    # Start polling in background
    import asyncio
    asyncio.create_task(bot.start_polling())

    return {"status": "started", "message": "Bot started in polling mode"}


@router.post("/stop")
async def stop_telegram_bot():
    """Stop the Telegram bot."""
    await shutdown_telegram_bot()
    return {"status": "stopped", "message": "Bot stopped"}


# Health check for the bot
@router.get("/health")
async def telegram_health():
    """Telegram bot health check."""
    bot = await get_telegram_bot()

    try:
        me = await bot.bot.get_me()
        return {
            "status": "healthy",
            "bot_username": me.username,
            "bot_id": me.id,
            "running": bot._running,
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
        }
