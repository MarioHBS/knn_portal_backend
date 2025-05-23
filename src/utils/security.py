"""
Utilitários de segurança para o Portal de Benefícios KNN.
"""
import hashlib
import re
from typing import Optional

from src.config import CPF_HASH_SALT

def validate_cpf(cpf: str) -> bool:
    """
    Valida um CPF.
    
    Implementação simplificada para fins de demonstração.
    Em produção, deve-se implementar a validação completa com dígitos verificadores.
    """
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Verificar se tem 11 dígitos
    if len(cpf) != 11:
        return False
    
    # Verificar se todos os dígitos são iguais (caso inválido)
    if len(set(cpf)) == 1:
        return False
    
    # Em uma implementação real, verificaríamos os dígitos verificadores
    # Para simplificar, consideramos válido se não for todos dígitos iguais
    return True

def hash_cpf(cpf: str, salt: Optional[str] = None) -> str:
    """
    Gera um hash SHA-256 do CPF com salt.
    """
    if not salt:
        salt = CPF_HASH_SALT
    
    # Remover caracteres não numéricos
    cpf = re.sub(r'[^0-9]', '', cpf)
    
    # Gerar hash
    return hashlib.sha256(f"{cpf}{salt}".encode()).hexdigest()
