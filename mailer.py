import logging
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from config import settings
from typing import List

logger = logging.getLogger(__name__)


def get_mail_config() -> ConnectionConfig:
    return ConnectionConfig(
        MAIL_USERNAME=settings.mail_username,
        MAIL_PASSWORD=settings.mail_password,
        MAIL_FROM=settings.mail_from,
        MAIL_PORT=settings.mail_port,
        MAIL_SERVER=settings.mail_server,
        MAIL_FROM_NAME=settings.mail_from_name,
        MAIL_TLS=settings.mail_tls,
        MAIL_SSL=settings.mail_ssl,
        USE_CREDENTIALS=True,
        VALIDATE_CERTS=True,
    )


async def send_verification_email(email: str, username: str, token: str):
    conf = get_mail_config()
    verification_link = f"{settings.app_url}/verify?token={token}"

    message = MessageSchema(
        subject="Подтверждение регистрации",
        recipients=[email],
        body=f"""
        Здравствуйте, {username}!

        Спасибо за регистрацию в нашем приложении.

        Для подтверждения email перейдите по ссылке:
        {verification_link}

        Или используйте этот код: {token}

        Ссылка действительна 24 часа.

        Если вы не регистрировались, проигнорируйте это письмо.
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_tournament_application_email(
    email: str,
    username: str,
    team_name: str,
    tournament_name: str
):
    """Отправка уведомления о подаче заявки на турнир"""
    conf = get_mail_config()
    dashboard_link = f"{settings.app_url}/tournaments"

    message = MessageSchema(
        subject=f"Заявка на турнир: {tournament_name}",
        recipients=[email],
        body=f"""
        Здравствуйте, {username}!

        Ваша команда "{team_name}" подала заявку на участие в турнире:
        "{tournament_name}"

        Заявка отправлена на рассмотрение администратору.
        Вы получите уведомление о решении.

        Статус заявки можно проверить в личном кабинете:
        {dashboard_link}

        Удачи в турнире! 🏆
        Команда EasyCyberPro
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_tournament_confirmation_email(
    email: str,
    username: str,
    team_name: str,
    tournament_name: str,
    start_date: str
):
    """Отправка уведомления о подтверждении участия в турнире"""
    conf = get_mail_config()

    message = MessageSchema(
        subject=f"✅ Подтверждение участия: {tournament_name}",
        recipients=[email],
        body=f"""
        Здравствуйте, {username}!

        Отличные новости! Ваша команда "{team_name}" подтверждена для участия в турнире:
        "{tournament_name}"

        📅 Дата начала: {start_date}

        Готовьтесь к соревнованиям и удачи в турнире! 🏆

        С уважением,
        Команда EasyCyberPro
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_tournament_rejection_email(
    email: str,
    username: str,
    team_name: str,
    tournament_name: str,
    reason: str = ""
):
    """Отправка уведомления об отказе в участии в турнире"""
    conf = get_mail_config()

    message = MessageSchema(
        subject=f"❌ Заявка на турнир: {tournament_name}",
        recipients=[email],
        body=f"""
        Здравствуйте, {username}!

        К сожалению, ваша команда "{team_name}" не была принята для участия в турнире:
        "{tournament_name}"

        {f"Причина: {reason}" if reason else "Администратор не указал причину отказа."}

        Вы можете подать заявку на другие турниры в любое время.

        С уважением,
        Команда EasyCyberPro
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: str, username: str, token: str):
    """Отправка email для сброса пароля"""
    conf = get_mail_config()
    reset_link = f"{settings.app_url}/reset-password?token={token}"

    message = MessageSchema(
        subject="Сброс пароля - EasyCyberPro",
        recipients=[email],
        body=f"""
        Здравствуйте, {username}!

        Вы запросили сброс пароля для вашего аккаунта.

        Для сброса пароля перейдите по ссылке:
        {reset_link}

        Или используйте этот код: {token}

        Ссылка действительна 1 час.

        Если вы не запрашивали сброс пароля, проигнорируйте это письмо.

        С уважением,
        Команда EasyCyberPro
        """,
        subtype="plain"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
