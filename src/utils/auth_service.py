import secrets
import string

import firebase_admin
from firebase_admin import auth, credentials


def generate_temporary_password(length: int = 12) -> str:
    """Gera uma senha temporária segura."""
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for i in range(length))
    return password


class AuthService:
    """Serviço para gerenciamento de usuários no Firebase Authentication."""

    def __init__(self):
        if not firebase_admin._apps:
            # Inicializar o Firebase Admin SDK
            # As credenciais são carregadas a partir de variáveis de ambiente
            # ou de um arquivo de conta de serviço.
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)

    def create_user(
        self, email: str, password: str, display_name: str | None = None
    ) -> auth.UserRecord:
        """Cria um novo usuário no Firebase Authentication."""
        try:
            user = auth.create_user(
                email=email, password=password, display_name=display_name
            )
            return user
        except Exception as e:
            # Adicionar log de erro
            raise e

    def create_user_with_temp_password(
        self, email: str, display_name: str | None = None
    ) -> tuple[auth.UserRecord, str]:
        """Cria um novo usuário no Firebase Authentication com uma senha temporária e retorna o registro do usuário e a senha."""
        temp_password = generate_temporary_password()
        user = auth.create_user(
            email=email, password=temp_password, display_name=display_name
        )
        return user, temp_password

    def update_password(self, uid: str, new_password: str):
        """Atualiza a senha de um usuário no Firebase Authentication."""
        try:
            auth.update_user(uid, password=new_password)
        except Exception as e:
            # Adicionar log de erro
            raise e

    def delete_user(self, uid: str):
        """Exclui um usuário do Firebase Authentication."""
        try:
            auth.delete_user(uid)
        except Exception as e:
            # Adicionar log de erro
            raise e
