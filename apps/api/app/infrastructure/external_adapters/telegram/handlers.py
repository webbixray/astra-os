"""Telegram Bot Handlers for Astra OS - Command and Callback Handlers"""

import logging
from typing import TYPE_CHECKING
from uuid import UUID

from aiogram import F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

from app.application.use_cases.organizations.org_service import OrganizationService as OrgService
from app.application.use_cases.ai.content_generation_service import ContentGenerationService
from app.application.use_cases.ai.prompt_manager import PromptManager

if TYPE_CHECKING:
    from app.infrastructure.external_adapters.telegram.bot import TelegramBot, UserContext, BotStates

logger = logging.getLogger(__name__)

# Create router
router = Router()


# === State Machine for Conversations ===

class BotStates(StatesGroup):
    """States for multi-step conversations."""
    IDLE = State()
    SELECTING_ORG = State()
    CREATING_CAMPAIGN_NAME = State()
    CREATING_CAMPAIGN_BUDGET = State()
    CREATING_CAMPAIGN_GOAL = State()
    GENERATING_CONTENT_TOPIC = State()
    QUERYING_KNOWLEDGE = State()


# === Start and Help Handlers ===

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Handle /start command."""
    await state.clear()
    ctx = bot.get_user_context(message.from_user.id)
    ctx.chat_id = message.chat.id
    ctx.clear()
    
    welcome_text = (
        "🚀 <b>Welcome to Astra OS - Your AI Advertising Agency!</b>\n\n"
        "I'm your AI assistant that can control the entire marketing department:\n\n"
        "📊 <b>Campaign Management</b> - Create, monitor, and optimize campaigns\n"
        "✍️ <b>Content Generation</b> - AI-powered content for all channels\n"
        "📈 <b>Analytics & Reports</b> - Real-time insights and ROI tracking\n"
        "📢 <b>Ad Management</b> - Google Ads, Meta, LinkedIn, TikTok\n"
        "🧠 <b>Knowledge Base</b> - Market research and competitor analysis\n\n"
        "To get started, please select your organization:"
    )
    
    # Get organizations
    try:
        async with bot._session_factory() as session:
            org_service = OrgService(session)
            orgs = await org_service.list_organizations()
            
            if not orgs:
                await message.answer(
                    "⚠️ No organizations found. Please contact admin to set up your organization first.",
                    parse_mode=ParseMode.HTML
                )
                return
            
            keyboard = bot.create_org_selection_keyboard(orgs)
            await message.answer(welcome_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            await state.set_state(BotStates.SELECTING_ORG)
    except Exception as e:
        logger.error(f"Error in start command: {e}")
        await message.answer(
            "❌ Error loading organizations. Please try again later.",
            parse_mode=ParseMode.HTML
        )


@router.message(Command("help"))
async def cmd_help(message: Message, bot: "TelegramBot"):
    """Handle /help command."""
    help_text = (
        "📖 <b>Astra OS - AI Advertising Agency Bot Help</b>\n\n"
        "<b>Available Commands:</b>\n"
        "/start - Start the bot and select organization\n"
        "/help - Show this help message\n"
        "/org - Switch organization\n"
        "/campaigns - List and manage campaigns\n"
        "/create_campaign - Create a new campaign\n"
        "/content - Generate content\n"
        "/analytics - View analytics and reports\n"
        "/ads - Manage ad campaigns\n"
        "/knowledge - Query knowledge base\n"
        "/status - Show current status\n"
        "/cancel - Cancel current operation\n\n"
        "<b>Quick Actions:</b>\n"
        "Use the inline keyboard menus for guided workflows.\n\n"
        "<b>Workflow Examples:</b>\n"
        "1. <code>/start</code> → Select org → <code>/create_campaign</code> → Follow prompts\n"
        "2. <code>/content</code> → Choose type → Enter topic → Get AI content\n"
        "3. <code>/analytics</code> → Select report → View insights\n\n"
        "<b>Need Help?</b>\n"
        "Contact support or use <code>/cancel</code> to reset anytime."
    )
    await message.answer(help_text, parse_mode=ParseMode.HTML)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Handle /cancel command."""
    await state.clear()
    ctx = bot.get_user_context(message.from_user.id)
    ctx.clear()
    
    await message.answer(
        "❌ <b>Operation cancelled.</b> You're back to the main menu.",
        reply_markup=bot.create_main_keyboard(),
        parse_mode=ParseMode.HTML
    )


# === Organization Selection ===

@router.callback_query(F.data.startswith("org_select_"))
async def callback_org_select(callback: CallbackQuery, state: FSMContext, bot: "TelegramBot"):
    """Handle organization selection."""
    org_id_str = callback.data.replace("org_select_", "")
    try:
        org_id = UUID(org_id_str)
    except ValueError:
        await callback.answer("❌ Invalid organization ID", show_alert=True)
        return
    
    ctx = bot.get_user_context(callback.from_user.id)
    ctx.organization_id = org_id
    
    # Get org name
    try:
        async with bot._session_factory() as session:
            org_service = OrgService(session)
            org = await org_service.get_organization(org_id)
            ctx.organization_name = org.name if org else "Selected Organization"
    except Exception as e:
        logger.error(f"Error fetching org: {e}")
        ctx.organization_name = "Selected Organization"
    
    await state.clear()
    
    await bot.safe_edit_message(
        callback.message,
        f"✅ <b>Organization selected:</b> {ctx.organization_name}\n\n"
        f"What would you like to do?",
        reply_markup=bot.create_main_keyboard()
    )


@router.message(Command("org"))
async def cmd_org(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Handle /org command to switch organization."""
    await state.clear()
    ctx = bot.get_user_context(message.from_user.id)
    ctx.clear()
    
    try:
        async with bot._session_factory() as session:
            org_service = OrgService(session)
            orgs = await org_service.list_organizations()
            
            if not orgs:
                await message.answer("⚠️ No organizations found.")
                return
            
            keyboard = bot.create_org_selection_keyboard(orgs)
            await message.answer(
                "🏢 <b>Select Organization:</b>",
                reply_markup=keyboard,
                parse_mode=ParseMode.HTML
            )
            await state.set_state(BotStates.SELECTING_ORG)
    except Exception as e:
        logger.error(f"Error in org command: {e}")
        await message.answer("❌ Error loading organizations.")


# === Main Menu Handlers ===

@router.callback_query(F.data == "menu_main")
async def callback_main_menu(callback: CallbackQuery, state: FSMContext, bot: "TelegramBot"):
    """Return to main menu."""
    await state.clear()
    ctx = bot.get_user_context(callback.from_user.id)
    ctx.clear()
    
    org_name = ctx.organization_name or "Not selected"
    
    await bot.safe_edit_message(
        callback.message,
        f"🏠 <b>Main Menu</b>\n\n"
        f"🏢 Organization: <b>{org_name}</b>\n\n"
        f"Choose an action:",
        reply_markup=bot.create_main_keyboard()
    )


@router.callback_query(F.data == "menu_campaigns")
async def callback_menu_campaigns(callback: CallbackQuery, bot: "TelegramBot"):
    """Show campaigns menu."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.safe_edit_message(
        callback.message,
        "📊 <b>Campaign Management</b>\n\nSelect an action:",
        reply_markup=bot.create_campaign_keyboard()
    )


@router.callback_query(F.data == "menu_content")
async def callback_menu_content(callback: CallbackQuery, bot: "TelegramBot"):
    """Show content generation menu."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.safe_edit_message(
        callback.message,
        "✍️ <b>Content Generation</b>\n\nWhat type of content would you like to create?",
        reply_markup=bot.create_content_keyboard()
    )


@router.callback_query(F.data == "menu_analytics")
async def callback_menu_analytics(callback: CallbackQuery, bot: "TelegramBot"):
    """Show analytics menu."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.safe_edit_message(
        callback.message,
        "📈 <b>Analytics & Reports</b>\n\nSelect a report type:",
        reply_markup=bot.create_analytics_keyboard()
    )


@router.callback_query(F.data == "menu_ads")
async def callback_menu_ads(callback: CallbackQuery, bot: "TelegramBot"):
    """Show ads management menu."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.safe_edit_message(
        callback.message,
        "📢 <b>Ad Campaign Management</b>\n\nSelect an action:",
        reply_markup=bot.create_ads_keyboard()
    )


@router.callback_query(F.data == "menu_knowledge")
async def callback_menu_knowledge(callback: CallbackQuery, state: FSMContext, bot: "TelegramBot"):
    """Show knowledge base menu."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await state.set_state(BotStates.QUERYING_KNOWLEDGE)
    
    await bot.safe_edit_message(
        callback.message,
        "🧠 <b>Knowledge Base</b>\n\n"
        "Ask me anything about:\n"
        "• Market trends and insights\n"
        "• Competitor analysis\n"
        "• Industry benchmarks\n"
        "• Best practices\n"
        "• Campaign optimization tips\n\n"
        "Type your question:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_main")
        ]]),
        parse_mode=ParseMode.HTML
    )


# === Campaign Handlers ===

@router.callback_query(F.data == "campaign_list")
async def callback_campaign_list(callback: CallbackQuery, bot: "TelegramBot"):
    """List campaigns for the organization."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.send_typing(callback.message.chat.id)
    
    try:
        async with bot._session_factory() as session:
            campaign_repo = CampaignRepositoryImpl(session)
            use_case = ListCampaignsUseCase(campaign_repo)
            campaigns = await use_case.execute(ctx.organization_id)
            
            if not campaigns:
                text = "📭 No campaigns found. Create your first campaign!"
            else:
                text = f"📋 <b>Campaigns ({len(campaigns)})</b>\n\n"
                for c in campaigns[:10]:
                    status_emoji = "🟢" if c.status == "active" else "🔴" if c.status == "paused" else "⚪"
                    text += f"{status_emoji} <b>{c.name}</b>\n"
                    text += f"   Status: {c.status} | Budget: ${c.budget_amount or 0:,.2f}\n\n"
                
                if len(campaigns) > 10:
                    text += f"... and {len(campaigns) - 10} more"
            
            await bot.safe_edit_message(
                callback.message,
                text,
                reply_markup=bot.create_campaign_keyboard()
            )
    except Exception as e:
        logger.error(f"Error listing campaigns: {e}")
        await bot.safe_edit_message(
            callback.message,
            "❌ Error loading campaigns. Please try again.",
            reply_markup=bot.create_campaign_keyboard()
        )


@router.callback_query(F.data == "campaign_create")
async def callback_campaign_create(callback: CallbackQuery, state: FSMContext, bot: "TelegramBot"):
    """Start campaign creation flow."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await state.set_state(BotStates.CREATING_CAMPAIGN_NAME)
    ctx.temp_data = {"step": "name"}
    
    await bot.safe_edit_message(
        callback.message,
        "➕ <b>Create New Campaign</b>\n\n"
        "Step 1/3: Enter campaign name:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_campaigns")
        ]])
    )


@router.message(StateFilter(BotStates.CREATING_CAMPAIGN_NAME))
async def process_campaign_name(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Process campaign name input."""
    ctx = bot.get_user_context(message.from_user.id)
    ctx.temp_data["name"] = message.text.strip()
    ctx.temp_data["step"] = "budget"
    
    await state.set_state(BotStates.CREATING_CAMPAIGN_BUDGET)
    
    await message.answer(
        f"✅ Name: <b>{message.text}</b>\n\n"
        "Step 2/3: Enter budget (USD):",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_campaigns")
        ]]),
        parse_mode=ParseMode.HTML
    )


@router.message(StateFilter(BotStates.CREATING_CAMPAIGN_BUDGET))
async def process_campaign_budget(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Process campaign budget input."""
    try:
        budget = float(message.text.replace("$", "").replace(",", "").strip())
    except ValueError:
        await message.answer("❌ Please enter a valid number (e.g., 1000 or 1,000)")
        return
    
    ctx = bot.get_user_context(message.from_user.id)
    ctx.temp_data["budget"] = budget
    ctx.temp_data["step"] = "goal"
    
    await state.set_state(BotStates.CREATING_CAMPAIGN_GOAL)
    
    await message.answer(
        f"✅ Budget: <b>${budget:,.2f}</b>\n\n"
        "Step 3/3: Enter campaign goal/objective:\n"
        "<i>(e.g., 'Increase brand awareness', 'Drive sales for new product', 'Generate leads')</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_campaigns")
        ]]),
        parse_mode=ParseMode.HTML
    )


@router.message(StateFilter(BotStates.CREATING_CAMPAIGN_GOAL))
async def process_campaign_goal(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Process campaign goal and create campaign."""
    ctx = bot.get_user_context(message.from_user.id)
    goal = message.text.strip()
    
    await bot.send_typing(message.chat.id)
    
    try:
        async with bot._session_factory() as session:
            campaign_repo = CampaignRepositoryImpl(session)
            use_case = CreateCampaignUseCase(campaign_repo)
            
            # Need a user ID - using a system user for bot
            from app.domain.entities.users.user import User
            # For bot, we'll use a system user or the first member
            from app.infrastructure.db.repositories.organizations.organization_repository import OrganizationRepositoryImpl
            org_repo = OrganizationRepositoryImpl(session)
            members = await org_repo.get_members(ctx.organization_id)
            creator_id = members[0].user_id if members else None
            
            if not creator_id:
                await message.answer("❌ No organization members found. Cannot create campaign.")
                return
            
            campaign = await use_case.execute(
                organization_id=ctx.organization_id,
                name=ctx.temp_data["name"],
                created_by=creator_id,
                description=goal,
                budget_amount=ctx.temp_data["budget"],
                budget_currency="USD",
                objective=goal,
            )
        
        await state.clear()
        ctx.clear()
        
        await message.answer(
            f"🎉 <b>Campaign Created Successfully!</b>\n\n"
            f"📋 <b>Name:</b> {campaign.name}\n"
            f"💰 <b>Budget:</b> ${campaign.budget_amount:,.2f}\n"
            f"🎯 <b>Goal:</b> {goal}\n"
            f"🆔 <b>ID:</b> <code>{campaign.id}</code>\n\n"
            f"The campaign is ready. You can now activate it or add content.",
            reply_markup=bot.create_campaign_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        await message.answer(
            "❌ Error creating campaign. Please try again.",
            reply_markup=bot.create_campaign_keyboard(),
            parse_mode=ParseMode.HTML
        )


# === Content Generation Handlers ===

@router.callback_query(F.data.startswith("content_"))
async def callback_content_type(callback: CallbackQuery, state: FSMContext, bot: "TelegramBot"):
    """Handle content type selection."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    content_type_map = {
        "content_blog": "blog_post",
        "content_social": "social_post",
        "content_email": "email",
        "content_video": "video_script",
        "content_ad": "ad_copy",
    }
    
    content_type = content_type_map.get(callback.data, "blog_post")
    ctx.temp_data["content_type"] = content_type
    
    await state.set_state(BotStates.GENERATING_CONTENT_TOPIC)
    
    type_names = {
        "blog_post": "Blog Post",
        "social_post": "Social Media Post",
        "email": "Email Newsletter",
        "video_script": "Video Script",
        "ad_copy": "Ad Creative",
    }
    
    await bot.safe_edit_message(
        callback.message,
        f"✍️ <b>Generate {type_names.get(content_type, 'Content')}</b>\n\n"
        f"Enter the topic or brief:\n"
        f"<i>(e.g., 'Benefits of AI in marketing', 'Summer sale announcement', 'Product launch email')</i>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="❌ Cancel", callback_data="menu_content")
        ]]),
        parse_mode=ParseMode.HTML
    )


@router.message(StateFilter(BotStates.GENERATING_CONTENT_TOPIC))
async def process_content_topic(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Process content topic and generate content using real AI."""
    ctx = bot.get_user_context(message.from_user.id)
    topic = message.text.strip()
    content_type = ctx.temp_data.get("content_type", "blog_post")
    
    await bot.send_typing(message.chat.id)
    
    try:
        async with bot._session_factory() as session:
            # Get content generation service
            prompt_repo = SystemPromptRepositoryImpl(session)
            prompt_manager = PromptManager(repository=prompt_repo)
            content_service = ContentGenerationService(prompt_manager=prompt_manager)
            
            # Get template for content type
            template_repo = ContentTemplateRepository(session)
            voice_repo = BrandVoiceRepository(session)
            
            # Map content types to template names
            template_map = {
                "blog_post": "Blog Post",
                "social_post": "Social Post",
                "email": "Email Newsletter",
                "video_script": "Video Script",
                "ad_copy": "Ad Copy",
            }
            template_name = template_map.get(content_type, "Blog Post")
            template = await template_repo.find_by_name(template_name)
            
            if not template:
                # Use built-in templates
                from app.application.use_cases.ai.content_generation_service import BUILTIN_TEMPLATES
                template = next((t for t in BUILTIN_TEMPLATES if t.content_type == content_type), BUILTIN_TEMPLATES[0])
            
            # Get brand voice if available
            brand_voice = None
            # Check if user has a default brand voice
            voice = await voice_repo.get_default_by_organization(ctx.organization_id)
            if voice:
                brand_voice = BrandVoice(
                    id=voice.id,
                    name=voice.name,
                    tone=voice.tone,
                    style_guide=voice.style_guide,
                    vocabulary=voice.vocabulary,
                    target_audience=voice.target_audience,
                )
            
            # Generate content
            result = await content_service.generate(
                template=template,
                variables={"topic": topic},
                brand_voice=brand_voice,
            )
            
            generated_content = result.get("content", "")
            sections = result.get("sections", {})
            
            # Save content to workspace
            content_repo = ContentRepositoryImpl(session)
            # Get creator ID (first member of org)
            from app.infrastructure.db.repositories.organizations.organization_repository import OrganizationRepositoryImpl
            org_repo = OrganizationRepositoryImpl(session)
            members = await org_repo.get_members(ctx.organization_id)
            creator_id = members[0].user_id if members else None
            
            if creator_id:
                content_obj = Content.create(
                    organization_id=ctx.organization_id,
                    title=f"{topic} - {content_type.replace('_', ' ').title()}",
                    content_type=content_type,
                    created_by=creator_id,
                    body=generated_content,
                    generated_by_ai=True,
                )
                await content_repo.save(content_obj)
        
        type_names = {
            "blog_post": "Blog Post",
            "social_post": "Social Media Post",
            "email": "Email Newsletter",
            "video_script": "Video Script",
            "ad_copy": "Ad Creative",
        }
        
        await state.clear()
        ctx.clear()
        
        # Format response with sections
        response_text = f"✨ <b>Content Generated: {type_names.get(content_type, 'Content')}</b>\n\n"
        response_text += f"📝 <b>Topic:</b> {topic}\n\n"
        response_text += f"{generated_content}\n\n"
        
        if sections:
            response_text += "📑 <b>Sections:</b>\n"
            for name, content in sections.items():
                response_text += f"• <b>{name.title()}:</b> {content[:200]}{'...' if len(content) > 200 else ''}\n"
        
        response_text += "\n💾 Content has been saved to your workspace."
        
        await message.answer(
            response_text,
            reply_markup=bot.create_content_keyboard(),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error generating content: {e}", exc_info=True)
        await message.answer(
            "❌ Error generating content. Please try again.",
            reply_markup=bot.create_content_keyboard(),
            parse_mode=ParseMode.HTML
        )


# === Analytics Handlers ===

@router.callback_query(F.data.startswith("analytics_"))
async def callback_analytics(callback: CallbackQuery, bot: "TelegramBot"):
    """Handle analytics requests."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    await bot.send_typing(callback.message.chat.id)
    
    report_type = callback.data.replace("analytics_", "")
    
    try:
        async with bot._session_factory() as session:
            campaign_repo = CampaignRepositoryImpl(session)
            content_repo = ContentRepositoryImpl(session)
            service = AnalyticsService(campaign_repo, content_repo)
            
            if report_type == "overview":
                data = await service.get_overview(ctx.organization_id)
            elif report_type == "campaign":
                data = await service.get_campaign_performance(ctx.organization_id)
            elif report_type == "budget":
                data = await service.get_budget_utilization(ctx.organization_id)
            elif report_type == "roi":
                data = await service.get_roi_analysis(ctx.organization_id)
            elif report_type == "audience":
                data = await service.get_audience_insights(ctx.organization_id)
            elif report_type == "channels":
                data = await service.get_channel_performance(ctx.organization_id)
            else:
                data = {"error": "Unknown report type"}
        
        if "error" in data:
            text = f"❌ {data['error']}"
        else:
            text = format_analytics_report(report_type, data)
        
        await bot.safe_edit_message(
            callback.message,
            text,
            reply_markup=bot.create_analytics_keyboard()
        )
    except Exception as e:
        logger.error(f"Error generating analytics: {e}")
        await bot.safe_edit_message(
            callback.message,
            "❌ Error generating report. Please try again.",
            reply_markup=bot.create_analytics_keyboard()
        )


def format_analytics_report(report_type: str, data: dict) -> str:
    """Format analytics data for display."""
    if report_type == "overview":
        return (
            f"📊 <b>Overview Report</b>\n\n"
            f"📈 Total Campaigns: {data.get('total_campaigns', 0)}\n"
            f"🟢 Active: {data.get('active_campaigns', 0)}\n"
            f"📝 Draft: {data.get('draft_campaigns', 0)}\n"
            f"✅ Completed: {data.get('completed_campaigns', 0)}\n"
            f"📄 Total Content: {data.get('total_content', 0)}\n"
            f"📤 Published: {data.get('published_content', 0)}\n"
            f"💰 Total Budget: ${data.get('total_budget', 0):,.2f}"
        )
    elif report_type == "budget":
        return (
            f"💰 <b>Budget Utilization</b>\n\n"
            f"Total Budget: ${data.get('total_budget', 0):,.2f}\n"
            f"Spent: ${data.get('spent', 0):,.2f}\n"
            f"Remaining: ${data.get('remaining', 0):,.2f}\n"
            f"Utilization: {data.get('utilization_pct', 0):.1f}%"
        )
    elif report_type == "roi":
        return (
            f"🎯 <b>ROI Analysis</b>\n\n"
            f"Total Revenue: ${data.get('total_revenue', 0):,.2f}\n"
            f"Total Cost: ${data.get('total_cost', 0):,.2f}\n"
            f"ROI: {data.get('roi', 0):.1f}%\n"
            f"ROAS: {data.get('roas', 0):.2f}x"
        )
    elif report_type == "campaign":
        campaigns = data.get("campaigns", [])
        text = f"📈 <b>Campaign Performance</b>\n\n"
        for c in campaigns[:5]:
            text += f"• <b>{c.get('name', 'N/A')}</b>: ${c.get('spend', 0):,.2f} spend, {c.get('conversions', 0)} conv\n"
        return text
    elif report_type == "audience":
        return f"👥 <b>Audience Insights</b>\n\n{data.get('summary', 'No data available')}"
    elif report_type == "channels":
        channels = data.get("channels", [])
        text = f"📱 <b>Channel Performance</b>\n\n"
        for ch in channels:
            text += f"• {ch.get('name', 'N/A')}: ${ch.get('spend', 0):,.0f} spend, {ch.get('conversions', 0)} conv\n"
        return text
    return "Report generated."


# === Ads Management Handlers ===

@router.callback_query(F.data.startswith("ads_"))
async def callback_ads(callback: CallbackQuery, bot: "TelegramBot"):
    """Handle ads management callbacks."""
    ctx = bot.get_user_context(callback.from_user.id)
    if not ctx.organization_id:
        await callback.answer("⚠️ Please select an organization first", show_alert=True)
        return
    
    action = callback.data.replace("ads_", "")
    
    if action == "accounts":
        await bot.safe_edit_message(
            callback.message,
            "🔗 <b>Connected Ad Accounts</b>\n\n"
            "• Google Ads: <code>123-456-7890</code> ✅\n"
            "• Meta Ads: <code>act_123456789</code> ✅\n"
            "• LinkedIn Ads: Not connected\n"
            "• TikTok Ads: Not connected\n\n"
            "Use 'Connect Ad Account' to add more.",
            reply_markup=bot.create_ads_keyboard()
        )
    elif action == "connect":
        await bot.safe_edit_message(
            callback.message,
            "🔗 <b>Connect Ad Account</b>\n\n"
            "Select platform to connect:\n\n"
            "1. Google Ads (OAuth)\n"
            "2. Meta Ads (Facebook/Instagram)\n"
            "3. LinkedIn Ads\n"
            "4. TikTok Ads\n\n"
            "<i>Feature coming soon - use web dashboard for now.</i>",
            reply_markup=bot.create_ads_keyboard()
        )
    else:
        await bot.safe_edit_message(
            callback.message,
            f"📢 <b>Ad Management: {action.title()}</b>\n\n"
            f"This feature is coming soon. Please use the web dashboard for full ad management.",
            reply_markup=bot.create_ads_keyboard()
        )


# === Knowledge Base Handlers ===

@router.message(StateFilter(BotStates.QUERYING_KNOWLEDGE))
async def process_knowledge_query(message: Message, state: FSMContext, bot: "TelegramBot"):
    """Process knowledge base query."""
    ctx = bot.get_user_context(message.from_user.id)
    query = message.text.strip()
    
    await bot.send_typing(message.chat.id)
    
    try:
        async with bot._session_factory() as session:
            graph_store = GraphStore()
            service = KnowledgeGraphService(graph_store)
            result = await service.query_knowledge(
                organization_id=ctx.organization_id,
                query=query,
            )
        
        await state.clear()
        
        answer = result.get("answer", "No answer found")
        sources = result.get("sources", [])
        
        text = f"🧠 <b>Knowledge Base Answer</b>\n\n"
        text += f"❓ <b>Question:</b> {query}\n\n"
        text += f"💡 <b>Answer:</b>\n{answer}\n\n"
        
        if sources:
            text += f"📚 <b>Sources:</b>\n"
            for s in sources[:3]:
                text += f"• {s}\n"
        
        await message.answer(
            text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔍 Ask Another", callback_data="menu_knowledge"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        logger.error(f"Error querying knowledge: {e}")
        await message.answer(
            "❌ Error querying knowledge base. Please try again.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔍 Try Again", callback_data="menu_knowledge"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")
            ]]),
            parse_mode=ParseMode.HTML
        )


# === Status Handler ===

@router.message(Command("status"))
async def cmd_status(message: Message, bot: "TelegramBot"):
    """Show current bot status."""
    ctx = bot.get_user_context(message.from_user.id)
    
    status_text = (
        f"📋 <b>Current Status</b>\n\n"
        f"👤 User: {message.from_user.first_name} (ID: {message.from_user.id})\n"
        f"💬 Chat: {message.chat.id}\n"
        f"🏢 Organization: {ctx.organization_name or 'Not selected'}\n"
        f"📊 Campaign: {str(ctx.selected_campaign_id)[:8] + '...' if ctx.selected_campaign_id else 'None'}\n"
        f"🤖 Bot: Running\n"
        f"🔧 Mode: {'Polling' if bot.config.use_polling else 'Webhook'}\n"
    )
    
    await message.answer(status_text, parse_mode=ParseMode.HTML)


# === Admin Handlers ===

@router.message(Command("admin"))
async def cmd_admin(message: Message, bot: "TelegramBot"):
    """Admin panel (admin only)."""
    if not bot.config.admin_user_ids:
        await message.answer("❌ Admin panel not configured.")
        return
    
    admin_ids = [int(uid.strip()) for uid in bot.config.admin_user_ids.split(",") if uid.strip()]
    if message.from_user.id not in admin_ids:
        await message.answer("❌ Unauthorized. Admin access required.")
        return
    
    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\nSelect an action:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="👥 List Users", callback_data="admin_users")],
            [InlineKeyboardButton(text="📋 View Logs", callback_data="admin_logs")],
            [InlineKeyboardButton(text="📊 System Stats", callback_data="admin_stats")],
            [InlineKeyboardButton(text="🔄 Restart Bot", callback_data="admin_restart")],
            [InlineKeyboardButton(text="🏠 Main Menu", callback_data="menu_main")],
        ]),
        parse_mode=ParseMode.HTML
    )


@router.callback_query(F.data.startswith("admin_"))
async def callback_admin(callback: CallbackQuery, bot: "TelegramBot"):
    """Handle admin callbacks."""
    if not bot.config.admin_user_ids:
        await callback.answer("❌ Admin not configured", show_alert=True)
        return
    
    admin_ids = [int(uid.strip()) for uid in bot.config.admin_user_ids.split(",") if uid.strip()]
    if callback.from_user.id not in admin_ids:
        await callback.answer("❌ Unauthorized", show_alert=True)
        return
    
    action = callback.data.replace("admin_", "")
    
    if action == "users":
        await bot.safe_edit_message(
            callback.message,
            "👥 <b>User Management</b>\n\nUser listing feature coming soon.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Back", callback_data="admin")
            ]])
        )
    elif action == "logs":
        await bot.safe_edit_message(
            callback.message,
            "📋 <b>System Logs</b>\n\nLog viewing feature coming soon.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Back", callback_data="admin")
            ]])
        )
    elif action == "stats":
        await bot.safe_edit_message(
            callback.message,
            "📊 <b>System Statistics</b>\n\nStats feature coming soon.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Back", callback_data="admin")
            ]])
        )
    elif action == "restart":
        await bot.safe_edit_message(
            callback.message,
            "🔄 <b>Restart Bot</b>\n\nThis will restart the bot process.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ Confirm", callback_data="admin_restart_confirm"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="admin")
            ]])
        )


def register_handlers(bot: "TelegramBot"):
    """Register all handlers with the bot's dispatcher."""
    if bot.dp:
        bot.dp.include_router(router)
        logger.info("Telegram bot handlers registered")