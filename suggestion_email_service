# services/email_service.py
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

EMAIL_REMETENTE = os.getenv('EMAIL_REMETENTE')
EMAIL_SENHA_APP = os.getenv('EMAIL_SENHA_APP')
SMTP_HOST = os.getenv('EMAIL_SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', 465))


def enviar_email_senha_temporaria(destinatario: str, nome: str, senha: str) -> bool:
    """
    Envia email com senha temporária via Gmail SMTP

    Args:
        destinatario: Email do destinatário
        nome: Nome do usuário
        senha: Senha temporária gerada

    Returns:
        bool: True se enviou com sucesso, False caso contrário
    """
    try:
        # Cria mensagem
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Bem-vindo ao KNN Benefits - Seus dados de acesso'
        msg['From'] = f'KNN Benefits <{EMAIL_REMETENTE}>'
        msg['To'] = destinatario

        # Corpo em texto simples (fallback)
        texto = f"""
Bem-vindo ao KNN Benefits!

Olá, {nome}!

Uma conta foi criada para você no sistema KNN Benefits.

Seus dados de acesso:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📧 Email: {destinatario}
🔑 Senha Temporária: {senha}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ IMPORTANTE: Por segurança, recomendamos FORTEMENTE que você altere esta senha no primeiro acesso!

Acesse o sistema em: https://seu-app.com/login

═══════════════════════════════════════════
Se você não solicitou esta conta, ignore este email ou entre em contato conosco.

Atenciosamente,
Equipe KNN Benefits
        """

        # Corpo em HTML (visual melhor)
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f5f5f5;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f5f5f5; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: white; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden;">
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 20px; text-align: center;">
                            <h1 style="color: white; margin: 0; font-size: 28px;">🎉 Bem-vindo ao KNN Benefits!</h1>
                        </td>
                    </tr>

                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="font-size: 16px; color: #333; margin: 0 0 20px 0;">
                                Olá, <strong>{nome}</strong>!
                            </p>

                            <p style="font-size: 16px; color: #555; line-height: 1.6; margin: 0 0 30px 0;">
                                Uma conta foi criada para você no sistema <strong>KNN Benefits</strong>.
                                Use os dados abaixo para fazer seu primeiro acesso:
                            </p>

                            <!-- Box de Credenciais -->
                            <table width="100%" cellpadding="20" cellspacing="0" style="background-color: #f8f9ff; border-left: 4px solid #667eea; border-radius: 5px; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #555;">
                                            <strong>📧 Email:</strong>
                                        </p>
                                        <p style="margin: 0 0 20px 0; font-size: 16px; color: #333;">
                                            {destinatario}
                                        </p>

                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #555;">
                                            <strong>🔑 Senha Temporária:</strong>
                                        </p>
                                        <p style="margin: 0; font-size: 20px; font-family: 'Courier New', monospace; background-color: white; padding: 15px; border-radius: 5px; color: #d63031; font-weight: bold; letter-spacing: 2px;">
                                            {senha}
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Alerta de Segurança -->
                            <table width="100%" cellpadding="15" cellspacing="0" style="background-color: #fff3cd; border-left: 4px solid #ffc107; border-radius: 5px; margin-bottom: 30px;">
                                <tr>
                                    <td>
                                        <p style="margin: 0; font-size: 14px; color: #856404;">
                                            <strong>⚠️ IMPORTANTE:</strong> Por segurança, recomendamos <strong>fortemente</strong>
                                            que você altere esta senha no primeiro acesso!
                                        </p>
                                    </td>
                                </tr>
                            </table>

                            <!-- Botão de Ação -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="https://seu-app.com/login"
                                           style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                                  color: white;
                                                  padding: 15px 50px;
                                                  text-decoration: none;
                                                  border-radius: 5px;
                                                  font-weight: bold;
                                                  font-size: 16px;
                                                  display: inline-block;
                                                  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">
                                            Acessar o Sistema →
                                        </a>
                                    </td>
                                </tr>
                            </table>

                            <!-- Dicas de Segurança -->
                            <table width="100%" cellpadding="15" cellspacing="0" style="background-color: #e8f5e9; border-left: 4px solid #4caf50; border-radius: 5px; margin-top: 30px;">
                                <tr>
                                    <td>
                                        <p style="margin: 0 0 10px 0; font-size: 14px; color: #2e7d32; font-weight: bold;">
                                            💡 Dicas para uma senha segura:
                                        </p>
                                        <ul style="margin: 0; padding-left: 20px; color: #2e7d32; font-size: 13px;">
                                            <li>Use no mínimo 8 caracteres</li>
                                            <li>Combine letras maiúsculas e minúsculas</li>
                                            <li>Inclua números e símbolos</li>
                                            <li>Evite informações pessoais óbvias</li>
                                        </ul>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0 0 10px 0; font-size: 12px; color: #666;">
                                Se você não solicitou esta conta, ignore este email ou entre em contato conosco.
                            </p>
                            <p style="margin: 0; font-size: 12px; color: #999;">
                                © 2025 KNN Benefits. Todos os direitos reservados.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
        """

        # Anexa ambas as versões
        part1 = MIMEText(texto, 'plain', 'utf-8')
        part2 = MIMEText(html, 'html', 'utf-8')
        msg.attach(part1)
        msg.attach(part2)

        # Envia via Gmail SMTP
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.send_message(msg)

        print(f"✅ Email enviado com sucesso para {destinatario}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("❌ Erro de autenticação. Verifique EMAIL_REMETENTE e EMAIL_SENHA_APP")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ Erro SMTP: {e}")
        return False
    except Exception as e:
        print(f"❌ Erro ao enviar email: {e}")
        return False


def enviar_email_simples(destinatario: str, assunto: str, mensagem: str) -> bool:
    """
    Envia email simples (texto puro)
    """
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg['Subject'] = assunto
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = destinatario

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(EMAIL_REMETENTE, EMAIL_SENHA_APP)
            server.send_message(msg)

        return True
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
        return False
