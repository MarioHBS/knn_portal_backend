import argparse
import os
import sys

from src.config import (
    EMAIL_HOST,
    EMAIL_PORT,
    EMAIL_SERVICE_ENABLED,
    EMAIL_USER,
)
from src.utils.auth_service import generate_temporary_password
from src.utils.email_service import EmailService

# Adicionar o diretório raiz do projeto ao sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

def print_colored(message: str, color: str = "white") -> None:
    """Imprime mensagem colorida no terminal."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "white": "\033[0m",
        "cyan": "\033[96m",
    }
    color_code = colors.get(color, colors["white"])
    reset_code = "\033[0m"
    print(f"{color_code}{message}{reset_code}")

def print_header(title: str) -> None:
    print_colored("\n" + "=" * 50, "cyan")
    print_colored(title.center(50), "cyan")
    print_colored("=" * 50, "cyan")

def simulate_user_creation_and_send_email(entity_type: str):
    """
    Simula a criação de um usuário e envia um e-mail de boas-vindas.
    """
    print_header(
        f"Simulando Criação e Envio de E-mail para: {entity_type.capitalize()}"
    )

    # 1. Simulação de contexto autenticado
    print_colored("Simulando contexto de administrador autenticado.", "green")

    # 2. Definir dados da entidade de teste
    entity_data = {
        "student": {
            "entity_id": "test_student_id",
            "entity_name": "Aluno Teste",
            "entity_email": "marioh90.compras@gmail.com",
            "tenant_id": "test_tenant",
        },
        "employee": {
            "entity_id": "test_employee_id",
            "entity_name": "Funcionário Teste",
            "entity_email": "marioh90@gmail.com",
            "tenant_id": "test_tenant",
        },
        "partner": {
            "entity_id": "test_partner_id",
            "entity_name": "Parceiro Teste",
            "entity_email": "marioh90.compras@gmail.com",
            "tenant_id": "test_tenant",
        },
    }

    data = entity_data.get(entity_type)
    if not data:
        print_colored(f"Tipo de entidade '{entity_type}' inválido.", "red")
        return

    entity_id = data["entity_id"]
    entity_name = data["entity_name"]
    entity_email = data["entity_email"]
    tenant_id = data["tenant_id"]

    print_colored(f"Dados da Entidade ({entity_type}):", "blue")
    for key, value in data.items():
        print_colored(f"  {key}: {value}", "blue")

    # 3. Gerar senha temporária
    temporary_password = generate_temporary_password()
    print_colored(f"Senha temporária gerada: {temporary_password}", "green")

    # 4. Simular envio de e-mail de boas-vindas
    if not EMAIL_SERVICE_ENABLED:
        print_colored(
            "O serviço de e-mail está desabilitado (EMAIL_SERVICE_ENABLED=false).",
            "yellow",
        )
        print_colored("   Nenhum e-mail será enviado.", "yellow")
        return

    print_colored("Tentando enviar e-mail de boas-vindas...", "blue")
    email_service = EmailService()

    subject = f"Bem-vindo(a) ao KNN Portal Journey Club, {entity_name}!"
    body_html = f"""
    <p>Olá {entity_name},</p>
    <p>Seja bem-vindo(a) ao KNN Portal Journey Club!</p>
    <p>Seu acesso foi criado com sucesso. Abaixo estão suas credenciais temporárias:</p>
    <p><b>E-mail:</b> {entity_email}</p>
    <p><b>Senha Temporária:</b> {temporary_password}</p>
    <p>Recomendamos que você altere sua senha no primeiro acesso.</p>
    <p>Atenciosamente,</p>
    <p>Equipe KNN Portal Journey Club</p>
    """
    body_text = f"""
    Olá {entity_name},
    Seja bem-vindo(a) ao KNN Portal Journey Club!
    Seu acesso foi criado com sucesso. Abaixo estão suas credenciais temporárias:
    E-mail: {entity_email}
    Senha Temporária: {temporary_password}
    Recomendamos que você altere sua senha no primeiro acesso.
    Atenciosamente,
    Equipe KNN Portal Journey Club
    """

    try:
        email_service.send_email(
            to_email=entity_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
        )
        print_colored("E-mail de boas-vindas enviado com sucesso!", "green")
    except Exception as e:
        print_colored(f"Falha ao enviar e-mail de boas-vindas: {e}", "red")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Simula a criação de um usuário e envia um e-mail de boas-vindas."
    )
    parser.add_argument(
        "--entity",
        type=str,
        required=True,
        choices=["student", "employee", "partner"],
        help="Tipo de entidade a ser criada (student, employee, partner)",
    )
    args = parser.parse_args()
    simulate_user_creation_and_send_email(args.entity)
