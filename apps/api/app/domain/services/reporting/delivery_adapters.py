import logging

logger = logging.getLogger(__name__)


class ReportDeliveryAdapter:
    async def deliver(self, recipient: str, content: str,
                      format: str, report_name: str) -> bool:
        raise NotImplementedError


class EmailDeliveryAdapter(ReportDeliveryAdapter):
    async def deliver(self, recipient: str, content: str,
                      format: str, report_name: str) -> bool:
        logger.info("[EmailDelivery] Sending '%s' (%s) to %s", report_name, format, recipient)
        logger.info("[EmailDelivery] Content preview: %s...", content[:200])
        return True


class SlackDeliveryAdapter(ReportDeliveryAdapter):
    async def deliver(self, recipient: str, content: str,
                      format: str, report_name: str) -> bool:
        channel = recipient if recipient.startswith("#") else f"@{recipient}"
        logger.info("[SlackDelivery] Posting '%s' to %s", report_name, channel)
        return True


class WebhookDeliveryAdapter(ReportDeliveryAdapter):
    async def deliver(self, recipient: str, content: str,
                      format: str, report_name: str) -> bool:
        logger.info("[WebhookDelivery] POST '%s' to %s", report_name, recipient)
        return True


def get_delivery_adapter(channel: str) -> ReportDeliveryAdapter:
    adapters = {
        "email": EmailDeliveryAdapter(),
        "slack": SlackDeliveryAdapter(),
        "webhook": WebhookDeliveryAdapter(),
    }
    adapter = adapters.get(channel)
    if adapter is None:
        raise ValueError(f"Unknown delivery channel: {channel}")
    return adapter
