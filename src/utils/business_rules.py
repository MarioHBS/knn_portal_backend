"""
Implementação de regras de negócio específicas para o Portal de Benefícios KNN.
"""
import hashlib
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from src.config import CPF_HASH_SALT
from src.utils import logger


class BusinessRules:
    """
    Classe para implementação das regras de negócio do Portal de Benefícios KNN.
    """

    @staticmethod
    def validate_student_active(active_until: str) -> bool:
        """
        Valida se um aluno está com matrícula ativa.

        Args:
            active_until: Data de validade da matrícula (formato ISO)

        Returns:
            bool: True se a matrícula estiver ativa, False caso contrário
        """
        try:
            # Converter para datetime se for string
            if isinstance(active_until, str):
                active_until = datetime.fromisoformat(
                    active_until.replace("Z", "+00:00")
                )

            # Verificar se a data é um objeto date
            if hasattr(active_until, "date"):
                active_until = active_until.date()

            # Comparar com a data atual
            return active_until >= datetime.now().date()
        except Exception as e:
            logger.error(f"Erro ao validar data de matrícula: {str(e)}")
            return False

    @staticmethod
    def generate_validation_code() -> str:
        """
        Gera um código de validação de 6 dígitos.

        Returns:
            str: Código de 6 dígitos
        """
        return str(random.randint(100000, 999999))

    @staticmethod
    def calculate_code_expiration() -> datetime:
        """
        Calcula a data de expiração de um código de validação (3 minutos).

        Returns:
            datetime: Data de expiração
        """
        return datetime.now() + timedelta(minutes=3)

    @staticmethod
    def is_code_expired(expires: str) -> bool:
        """
        Verifica se um código de validação expirou.

        Args:
            expires: Data de expiração (formato ISO)

        Returns:
            bool: True se o código expirou, False caso contrário
        """
        try:
            # Converter para datetime se for string
            if isinstance(expires, str):
                expires = datetime.fromisoformat(expires.replace("Z", "+00:00"))

            # Comparar com a data atual
            return expires < datetime.now()
        except Exception as e:
            logger.error(f"Erro ao verificar expiração de código: {str(e)}")
            return True

    @staticmethod
    def validate_cpf(cpf: str) -> bool:
        """
        Valida um CPF.

        Args:
            cpf: CPF a ser validado

        Returns:
            bool: True se o CPF for válido, False caso contrário
        """
        # Remover caracteres não numéricos
        cpf = re.sub(r"[^0-9]", "", cpf)

        # Verificar se tem 11 dígitos
        if len(cpf) != 11:
            return False

        # Verificar se todos os dígitos são iguais (caso inválido)
        if len(set(cpf)) == 1:
            return False

        # Em uma implementação real, verificaríamos os dígitos verificadores
        # Para simplificar, consideramos válido se não for todos dígitos iguais
        return True

    @staticmethod
    def hash_cpf(cpf: str, salt: Optional[str] = None) -> str:
        """
        Gera um hash SHA-256 do CPF com salt.

        Args:
            cpf: CPF a ser hasheado
            salt: Salt para o hash (opcional)

        Returns:
            str: Hash do CPF
        """
        if not salt:
            salt = CPF_HASH_SALT

        # Remover caracteres não numéricos
        cpf = re.sub(r"[^0-9]", "", cpf)

        # Gerar hash
        return hashlib.sha256(f"{cpf}{salt}".encode()).hexdigest()

    @staticmethod
    def is_promotion_valid(promotion: Dict[str, Any]) -> bool:
        """
        Verifica se uma promoção é válida (ativa e dentro do período).

        Args:
            promotion: Dados da promoção

        Returns:
            bool: True se a promoção for válida, False caso contrário
        """
        try:
            # Verificar se está ativa
            if not promotion.get("active", False):
                return False

            # Obter datas
            valid_from = promotion.get("valid_from")
            valid_to = promotion.get("valid_to")

            if not valid_from or not valid_to:
                return False

            # Converter para datetime se for string
            if isinstance(valid_from, str):
                valid_from = datetime.fromisoformat(valid_from.replace("Z", "+00:00"))

            if isinstance(valid_to, str):
                valid_to = datetime.fromisoformat(valid_to.replace("Z", "+00:00"))

            # Verificar período
            now = datetime.now()
            return valid_from <= now <= valid_to
        except Exception as e:
            logger.error(f"Erro ao validar promoção: {str(e)}")
            return False


# Instância global das regras de negócio
business_rules = BusinessRules()
