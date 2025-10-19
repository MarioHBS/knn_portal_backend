import smtplib
from email.mime.text import MIMEText

from src.config import EMAIL_HOST, EMAIL_PASSWORD, EMAIL_PORT, EMAIL_USER


class EmailService:
    """Serviço para envio de e-mails."""

    def send_email(self, to_email: str, subject: str, body: str):
        """Envia um e-mail."""
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_USER
        msg["To"] = to_email

        try:
            with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
                server.starttls()
                server.login(EMAIL_USER, EMAIL_PASSWORD)
                server.sendmail(EMAIL_USER, [to_email], msg.as_string())
        except Exception as e:
            # Adicionar log de erro
            raise e
