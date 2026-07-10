import random

from app.domain.common import now
from app.domain.services.email.base_sender import EmailSender


class SendGridSender(EmailSender):
    def provider_type(self) -> str:
        return "sendgrid"

    async def send(self, to: list[str], subject: str, body: str,
                   from_email: str, from_name: str = "",
                   metadata: dict | None = None) -> dict:
        message_id = f"sg_{now().strftime('%Y%m%d%H%M%S')}_{random.randint(10000,99999)}"
        return {
            "message_id": message_id,
            "provider": "sendgrid",
            "sent_count": len(to),
            "status": "sent",
        }


class SESEmailSender(EmailSender):
    def provider_type(self) -> str:
        return "ses"

    async def send(self, to: list[str], subject: str, body: str,
                   from_email: str, from_name: str = "",
                   metadata: dict | None = None) -> dict:
        message_id = f"ses_{now().strftime('%Y%m%d%H%M%S')}_{random.randint(10000,99999)}"
        return {
            "message_id": message_id,
            "provider": "ses",
            "sent_count": len(to),
            "status": "sent",
        }


class SMTPEmailSender(EmailSender):
    def provider_type(self) -> str:
        return "smtp"

    async def send(self, to: list[str], subject: str, body: str,
                   from_email: str, from_name: str = "",
                   metadata: dict | None = None) -> dict:
        message_id = f"smtp_{now().strftime('%Y%m%d%H%M%S')}_{random.randint(10000,99999)}"
        return {
            "message_id": message_id,
            "provider": "smtp",
            "sent_count": len(to),
            "status": "sent",
        }


SENDER_REGISTRY: dict[str, EmailSender] = {
    "sendgrid": SendGridSender(),
    "ses": SESEmailSender(),
    "smtp": SMTPEmailSender(),
}


def get_sender(provider_type: str) -> EmailSender | None:
    return SENDER_REGISTRY.get(provider_type)
