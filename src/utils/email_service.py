import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.config import (
    EMAIL_HOST,
    EMAIL_PASSWORD,
    EMAIL_PORT,
    EMAIL_USER,
)


class EmailService:
    """Serviço para envio de e-mails utilizando SMTP_SSL."""

    def send_email(
        self, to_email: str, subject: str, body_html: str, body_text: str | None = None
    ):
        """
        Envia um e-mail com conteúdo HTML e, opcionalmente, texto plano.

        Args:
            to_email: O e-mail do destinatário.
            subject: O assunto do e-mail.
            body_html: O corpo do e-mail em formato HTML.
            body_text: O corpo do e-mail em texto plano (fallback).
        """
        if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USER, EMAIL_PASSWORD]):
            raise ValueError("As variáveis de ambiente do e-mail não estão configuradas.")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"KNN Benefits <{EMAIL_USER}>"
        msg["To"] = to_email

        # Anexa o corpo em texto plano, se fornecido
        if body_text:
            msg.attach(MIMEText(body_text, "plain", "utf-8"))

        # Anexa o corpo em HTML
        msg.attach(MIMEText(body_html, "html", "utf-8"))

        try:
            with smtplib.SMTP_SSL(EMAIL_HOST, int(EMAIL_PORT)) as server:
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.send_message(msg)
        except smtplib.SMTPAuthenticationError as e:
            # Idealmente, logar o erro com um sistema de logging
            print(f"Erro de autenticação SMTP: {e}")
            raise ConnectionRefusedError("Credenciais de e-mail inválidas.") from e
        except Exception as e:
            print(f"Erro ao enviar e-mail: {e}")
            raise ConnectionError("Não foi possível conectar ao servidor de e-mail.") from e
