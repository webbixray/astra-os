"""Telegram Bot Core for Astra OS - AI Advertising Agency Control"""

import asyncio
import logging
from typing import Any, Callable, Awaitable
from uuid import UUID

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, Filter
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.infrastructure.external_adapters.telegram.config import get_telegram_config, TelegramConfig
from app.application.use_cases.organizations.org_service import OrganizationService as OrgService
from app.application.use_cases.campaigns.campaign_use_cases import (
    CreateCampaignUseCase, GetCampaignUseCase, ListCampaignsUseCase, UpdateCampaignUseCase
)
from app.application.use_cases.content.content_use_cases import (
    CreateContentUseCase, ListContentUseCase
)
from app.application.use_cases.analytics.analytics_service import AnalyticsService
from app.application.use_cases.knowledge.knowledge_service import KnowledgeGraphService
from app.application.use_cases.advertising.ad_campaign_service import AdCampaignService
from app.application.use_cases.ai.content_generation_service import ContentGenerationService
from app.application.use_cases.ai.prompt_manager import PromptManager
from app.infrastructure.db.session import create_session_factory
from app.infrastructure.db.repositories.campaigns.campaign_repository import CampaignRepositoryImpl
from app.infrastructure.db.repositories.content.content_repository import ContentRepositoryImpl
from app.infrastructure.db.repositories.content_template_repository import ContentTemplateRepository
from app.infrastructure.db.repositories.brand_voice_repository import BrandVoiceRepository
from app.infrastructure.db.repositories.prompt_repository import SystemPromptRepositoryImpl
from app.infrastructure.external_adapters.knowledge.graph_store import GraphStore
from app.domain.entities.campaigns.campaign import Campaign
from app.domain.entities.content.content import Content
from app.domain.entities.content.content_template import ContentTemplate
from app.domain.entities.content.brand_voice import BrandVoice
from app.infrastructure.db.models.campaigns.campaign_model import CampaignModel
from app.infrastructure.db.models.content.content_model import ContentModel
from app.infrastructure.db.models.content.content_template_model import ContentTemplateModel
from app.infrastructure.db.models.content.brand_voice_model import BrandVoiceModel
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class BotStates(StatesGroup):
    """States for multi-step conversations."""
    IDLE = State()
    SELECTING_ORG = State()
    CREATING_CAMPAIGN_NAME = State()
    CREATING_CAMPAIGN_BUDGET = State()
    CREATING_CAMPAIGN_GOAL = State()
    GENERATING_CONTENT_TOPIC = State()
    QUERYING_KNOWLEDGE = State()


class UserContext:
    """Holds user context during conversation."""

    def __init__(self):
        self.user_id: int | None = None
        self.chat_id: int | None = None
        self.organization_id: UUID | None = None
        self.organization_name: str | None = None
        self.selected_campaign_id: UUID | None = None
        self.temp_data: dict = {}

    def clear(self):
        self.organization_id = None
        self.organization_name = None
        self.selected_campaign_id = None
        self.temp_data = {}


class AuthorizationFilter(Filter):
    """Filter to check if user is authorized to use the bot."""

    def __init__(self, config: TelegramConfig):
        self.config = config

    async def __call__(self, message: Message) -> bool:
        if not self.config.allowed_user_ids:
            return True  # No restrictions

        allowed_ids = [int(uid.strip()) for uid in self.config.allowed_user_ids.split(",") if uid.strip()]
        return message.from_user.id in allowed_ids if message.from_user else False


class AdminFilter(Filter):
    """Filter to check if user is admin."""

    def __init__(self, config: TelegramConfig):
        self.config = config

    async def __call__(self, message: Message) -> bool:
        if not self.config.admin_user_ids:
            return False

        admin_ids = [int(uid.strip()) for uid in self.config.admin_user_ids.split(",") if uid.strip()]
        return message.from_user.id in admin_ids if message.from_user else False


class WebhookValidationMiddleware:
    """Middleware to validate Telegram webhook secret token."""

    def __init__(self, config: TelegramConfig):
        self.config = config
        self.secret_token = config.webhook_secret_token

    async def __call__(self, handler, event, data):
        # For webhook updates, validate the secret token
        if hasattr(event, 'webhook_secret_token') and self.secret_token:
            if event.webhook_secret_token != self.secret_token:
                logger.warning("Invalid webhook secret token")
                return
        return await handler(event, data)


class GovernanceMiddleware:
    """Middleware to enforce governance rules on bot actions."""

    def __init__(self, bot: "TelegramBot"):
        self.bot = bot

    async def __call__(self, handler, event, data):
        # Check if this is a user action that needs governance
        ctx = self.bot.get_user_context(event.from_user.id) if event.from_user else None

        if ctx and ctx.organization_id:
            # Map callback/action to governance action
            action = self._map_action(event)
            if action:
                # Check governance
                allowed = await self._check_governance(ctx.organization_id, action, event.from_user.id)
                if not allowed:
                    if isinstance(event, CallbackQuery):
                        await event.answer("🚫 Action blocked by governance policy. Requires approval.", show_alert=True)
                    elif isinstance(event, Message):
                        await event.answer("🚫 Action blocked by governance policy. Requires approval.")
                    return

        return await handler(event, data)

    def _map_action(self, event) -> str | None:
        """Map Telegram event to governance action."""
        if isinstance(event, CallbackQuery):
            data = event.data
            if data.startswith("campaign_"):
                return "campaign.create" if data == "campaign_create" else "campaign.manage"
            elif data.startswith("content_"):
                return "content.generate"
            elif data.startswith("ads_"):
                return "ads.manage"
        elif isinstance(event, Message):
            # Check state for multi-step flows
            pass
        return None

    async def _check_governance(self, org_id: UUID, action: str, user_id: int) -> bool:
        """Check if action is allowed by governance."""
        try:
            async with self.bot._session_factory() as session:
                autonomy_repo = AutonomyRepositoryImpl(session)
                approval_repo = ApprovalRepositoryImpl(session)

                check_use_case = CheckAgentActionUseCase(
                    autonomy_repo=autonomy_repo,
                    approval_repo=approval_repo,
                )

                result = await check_use_case.execute(
                    organization_id=org_id,
                    agent_id=str(user_id),  # Using Telegram user ID as agent ID
                    agent_type="TELEGRAM_BOT",
                    action=action,
                )

                if result.requires_approval:
                    # Create approval request
                    create_approval = CreateApprovalRequestUseCase(approval_repo)
                    await create_approval.execute(
                        organization_id=org_id,
                        requested_by=user_id,
                        action=action,
                        payload={"telegram_user_id": user_id},
                    )
                    return False

                return result.allowed
        except Exception as e:
            logger.error(f"Governance check failed: {e}")
            return True  # Fail open for now

        return True


class TelegramBot:
    """Telegram Bot for controlling the Astra OS AI Advertising Agency."""

    def __init__(self, config: TelegramConfig | None = None):
        self.config = config or get_telegram_config()
        self.bot: Bot | None = None
        self.dp: Dispatcher | None = None
        self.user_contexts: dict[int, UserContext] = {}
        self._running = False
        self._webhook_app: web.Application | None = None
        self._redis: Redis | None = None
        self._redis_storage: RedisStorage | None = None

        # Repository instances (created per request)
        self._session_factory = None

    async def initialize(self):
        """Initialize the bot and dispatcher."""
        if not self.config.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN is required but not set")

        # Initialize Redis for FSM storage and session persistence
        if self.config.redis_url:
            self._redis = Redis.from_url(
                self.config.redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
            self._redis_storage = RedisStorage(
                redis=self._redis,
                key_builder=lambda key: f"telegram:fsm:{key}",
            )

        # Create bot instance
        self.bot = Bot(
            token=self.config.bot_token,
            default=DefaultBotProperties(
                parse_mode=ParseMode(self.config.parse_mode),
            ),
        )

        # Create dispatcher with Redis storage (or memory fallback)
        self.dp = Dispatcher(storage=self._redis_storage or MemoryStorage())

        # Register filters
        self.dp.message.filter(AuthorizationFilter(self.config))
        self.dp.callback_query.filter(AuthorizationFilter(self.config))

        # Register middleware for webhook secret validation
        self.dp.message.middleware(WebhookValidationMiddleware(self.config))
        self.dp.callback_query.middleware(WebhookValidationMiddleware(self.config))

        # Register handlers
        self._register_handlers()

        # Set bot commands
        await self._set_bot_commands()

        # Initialize session factory
        _, self._session_factory = create_session_factory()

        logger.info("Telegram bot initialized successfully")

    def _register_handlers(self):
        """Register all message and callback handlers."""
        from app.infrastructure.external_adapters.telegram.handlers import register_handlers
        register_handlers(self)

    async def _set_bot_commands(self):
        """Set the bot commands menu."""
        commands = [
            types.BotCommand(command="start", description="🚀 Start the AI Advertising Agency"),
            types.BotCommand(command="help", description="📖 Show help and available commands"),
            types.BotCommand(command="org", description="🏢 Select organization"),
            types.BotCommand(command="campaigns", description="📊 List and manage campaigns"),
            types.BotCommand(command="create_campaign", description="➕ Create new campaign"),
            types.BotCommand(command="content", description="✍️ Generate content"),
            types.BotCommand(command="analytics", description="📈 View analytics and reports"),
            types.BotCommand(command="ads", description="📢 Manage ad campaigns"),
            types.BotCommand(command="knowledge", description="🧠 Knowledge base queries"),
            types.BotCommand(command="status", description="📋 Show current status"),
            types.BotCommand(command="cancel", description="❌ Cancel current operation"),
        ]

        if self.config.admin_user_ids:
            commands.extend([
                types.BotCommand(command="admin", description="⚙️ Admin panel"),
                types.BotCommand(command="users", description="👥 List users"),
                types.BotCommand(command="logs", description="📋 View logs"),
            ])

        await self.bot.set_my_commands(commands)

    def get_user_context(self, user_id: int) -> UserContext:
        """Get or create user context."""
        if user_id not in self.user_contexts:
            self.user_contexts[user_id] = UserContext()
        ctx = self.user_contexts[user_id]
        ctx.user_id = user_id
        return ctx

    # === Bot Running Methods ===

    async def start_polling(self):
        """Start the bot in polling mode (development)."""
        if not self.bot or not self.dp:
            await self.initialize()

        self._running = True
        logger.info("Starting Telegram bot in polling mode...")

        try:
            await self.dp.start_polling(
                self.bot,
                allowed_updates=self.dp.resolve_used_update_types(),
                timeout=self.config.request_timeout,
            )
        finally:
            self._running = False

    async def start_webhook(self, host: str = "0.0.0.0", port: int = 8080):
        """Start the bot in webhook mode (production)."""
        if not self.bot or not self.dp:
            await self.initialize()

        if not self.config.webhook_url:
            raise ValueError("TELEGRAM_WEBHOOK_URL is required for webhook mode")

        # Create aiohttp app
        self._webhook_app = web.Application()

        # Setup webhook handler
        webhook_handler = SimpleRequestHandler(
            dispatcher=self.dp,
            bot=self.bot,
        )
        webhook_handler.register(self._webhook_app, path=self.config.webhook_path)

        # Setup application
        setup_application(self._webhook_app, self.dp, bot=self.bot)

        # Set webhook
        webhook_url = f"{self.config.webhook_url.rstrip('/')}{self.config.webhook_path}"
        await self.bot.set_webhook(
            url=webhook_url,
            allowed_updates=self.dp.resolve_used_update_types(),
            drop_pending_updates=True,
        )

        logger.info(f"Starting Telegram bot webhook on {host}:{port}")
        logger.info(f"Webhook URL: {webhook_url}")

        # Run web server
        runner = web.AppRunner(self._webhook_app)
        await runner.setup()
        site = web.TCPSite(runner, host, port)
        await site.start()

        self._running = True

        # Keep running
        try:
            while self._running:
                await asyncio.sleep(3600)
        finally:
            await self.stop()

    async def stop(self):
        """Stop the bot gracefully."""
        self._running = False

        if self._webhook_app:
            await self.bot.delete_webhook()

        if self.bot:
            await self.bot.session.close()

        logger.info("Telegram bot stopped")

    # === Helper Methods for Handlers ===

    def create_main_keyboard(self, is_admin: bool = False) -> InlineKeyboardMarkup:
        """Create main menu keyboard."""
        buttons = [
            [InlineKeyboardButton(text="📊 Campaigns", callback_data="menu_campaigns")],
            [InlineKeyboardButton(text="➕ Create Campaign", callback_data="menu_create_campaign")],
            [InlineKeyboardButton(text="✍️ Generate Content", callback_data="menu_content")],
            [InlineKeyboardButton(text="📈 Analytics", callback_data="menu_analytics")],
            [InlineKeyboardButton(text="📢 Ad Management", callback_data="menu_ads")],
            [InlineKeyboardButton(text="🧠 Knowledge Base", callback_data="menu_knowledge")],
            [InlineKeyboardButton(text="🏢 Switch Organization", callback_data="menu_org")],
        ]

        if is_admin:
            buttons.append([InlineKeyboardButton(text="⚙️ Admin Panel", callback_data="menu_admin")])

        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def create_campaign_keyboard(self) -> InlineKeyboardMarkup:
        """Create campaign management keyboard."""
        buttons = [
            [InlineKeyboardButton(text="📋 List Campaigns", callback_data="campaign_list")],
            [InlineKeyboardButton(text="➕ Create New", callback_data="campaign_create")],
            [InlineKeyboardButton(text="🔄 Sync from Platforms", callback_data="campaign_sync")],
            [InlineKeyboardButton(text="⏸️ Pause Campaign", callback_data="campaign_pause")],
            [InlineKeyboardButton(text="▶️ Resume Campaign", callback_data="campaign_resume")],
            [InlineKeyboardButton(text="📊 Campaign Performance", callback_data="campaign_performance")],
            [InlineKeyboardButton(text="🔙 Back to Main", callback_data="menu_main")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def create_content_keyboard(self) -> InlineKeyboardMarkup:
        """Create content generation keyboard."""
        buttons = [
            [InlineKeyboardButton(text="📝 Blog Post", callback_data="content_blog")],
            [InlineKeyboardButton(text="🐦 Social Media Post", callback_data="content_social")],
            [InlineKeyboardButton(text="📧 Email Newsletter", callback_data="content_email")],
            [InlineKeyboardButton(text="🎬 Video Script", callback_data="content_video")],
            [InlineKeyboardButton(text="🖼️ Ad Creative", callback_data="content_ad")],
            [InlineKeyboardButton(text="📅 Schedule Content", callback_data="content_schedule")],
            [InlineKeyboardButton(text="🔙 Back to Main", callback_data="menu_main")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def create_analytics_keyboard(self) -> InlineKeyboardMarkup:
        """Create analytics keyboard."""
        buttons = [
            [InlineKeyboardButton(text="📊 Overview", callback_data="analytics_overview")],
            [InlineKeyboardButton(text="📈 Campaign Report", callback_data="analytics_campaign")],
            [InlineKeyboardButton(text="💰 Budget Utilization", callback_data="analytics_budget")],
            [InlineKeyboardButton(text="🎯 ROI Analysis", callback_data="analytics_roi")],
            [InlineKeyboardButton(text="👥 Audience Insights", callback_data="analytics_audience")],
            [InlineKeyboardButton(text="📱 Channel Performance", callback_data="analytics_channels")],
            [InlineKeyboardButton(text="🔙 Back to Main", callback_data="menu_main")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def create_ads_keyboard(self) -> InlineKeyboardMarkup:
        """Create ad management keyboard."""
        buttons = [
            [InlineKeyboardButton(text="📋 List Ad Accounts", callback_data="ads_accounts")],
            [InlineKeyboardButton(text="🔗 Connect Ad Account", callback_data="ads_connect")],
            [InlineKeyboardButton(text="📊 Ad Campaigns", callback_data="ads_campaigns")],
            [InlineKeyboardButton(text="🎨 Ad Creatives", callback_data="ads_creatives")],
            [InlineKeyboardButton(text="💰 Budget Management", callback_data="ads_budget")],
            [InlineKeyboardButton(text="🎯 Targeting", callback_data="ads_targeting")],
            [InlineKeyboardButton(text="🔙 Back to Main", callback_data="menu_main")],
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    def create_org_selection_keyboard(self, orgs: list) -> InlineKeyboardMarkup:
        """Create organization selection keyboard."""
        buttons = []
        for org in orgs:
            buttons.append([
                InlineKeyboardButton(
                    text=f"🏢 {org.name}",
                    callback_data=f"org_select_{org.id}"
                )
            ])
        buttons.append([InlineKeyboardButton(text="🔙 Back", callback_data="menu_main")])
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    async def send_typing(self, chat_id: int):
        """Send typing indicator."""
        await self.bot.send_chat_action(chat_id, "typing")

    async def safe_edit_message(
        self,
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ):
        """Safely edit message, handling exceptions."""
        try:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.warning(f"Failed to edit message: {e}")
            # Send new message if edit fails
            await message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

    async def safe_answer(
        self,
        message: Message,
        text: str,
        reply_markup: InlineKeyboardMarkup | None = None,
    ):
        """Safely answer message."""
        try:
            await message.answer(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            logger.error(f"Failed to send message: {e}")

    # === Database Session Helpers ===

    async def get_session(self):
        """Get database session."""
        async with self._session_factory() as session:
            yield session

    async def get_campaign_repo(self):
        """Get campaign repository."""
        async with self._session_factory() as session:
            yield CampaignRepositoryImpl(session)

    async def get_content_repo(self):
        """Get content repository."""
        async with self._session_factory() as session:
            yield ContentRepositoryImpl(session)

    async def get_ad_campaign_repo(self):
        """Get ad campaign repository."""
        async with self._session_factory() as session:
            yield AdCampaignRepositoryImpl(session)


# Global bot instance
_bot_instance: TelegramBot | None = None


async def get_telegram_bot(config: TelegramConfig | None = None) -> TelegramBot:
    """Get or create the global Telegram bot instance."""
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = TelegramBot(config)
        await _bot_instance.initialize()
    return _bot_instance


async def shutdown_telegram_bot():
    """Shutdown the global Telegram bot instance."""
    global _bot_instance
    if _bot_instance:
        await _bot_instance.stop()
        _bot_instance = None
