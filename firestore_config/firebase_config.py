#!/usr/bin/env python3
"""
Configuração do Firebase para o Portal de Benefícios KNN.

Este arquivo contém as configurações necessárias para conectar com o Firebase.
As credenciais devem ser definidas no arquivo .env ou como variáveis de ambiente.
"""

import os
from pathlib import Path

# Carregar variáveis do arquivo .env se existir
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    # python-dotenv não está instalado, continuar sem carregar .env
    pass

# Configurações do Firebase
FIREBASE_CONFIG = {
    "apiKey": os.getenv("FB_API_KEY", "your-api-key-here"),
    "authDomain": os.getenv("FB_AUTH_DOMAIN", "your-project.firebaseapp.com"),
    "projectId": os.getenv("FIRESTORE_PROJECT", "knn-benefits"),
    "storageBucket": os.getenv("FB_STORAGE_BUCKET", "your-project.appspot.com"),
    "messagingSenderId": os.getenv("FB_MESSAGING_SENDER_ID", "123456789"),
    "appId": os.getenv("FB_APP_ID", "your-app-id"),
    "measurementId": os.getenv("FB_MEASUREMENT_ID", "your-measurement-id"),
}


# Validar se as configurações foram definidas
def validate_firebase_config():
    """
    Valida se todas as configurações necessárias do Firebase foram definidas.

    Returns:
        tuple: (is_valid, missing_configs)
    """
    missing_configs = []

    for key, value in FIREBASE_CONFIG.items():
        if value.startswith("your-") or value in ["123456789"]:
            missing_configs.append(key)

    is_valid = len(missing_configs) == 0
    return is_valid, missing_configs


def get_firebase_config():
    """
    Retorna a configuração do Firebase.

    Returns:
        dict: Configuração do Firebase
    """
    return FIREBASE_CONFIG.copy()


def print_firebase_status():
    """
    Imprime o status da configuração do Firebase.
    """
    print("=== Status da Configuração Firebase ===")
    print(f"Project ID: {FIREBASE_CONFIG['projectId']}")
    print(f"Auth Domain: {FIREBASE_CONFIG['authDomain']}")
    print(f"Storage Bucket: {FIREBASE_CONFIG['storageBucket']}")

    is_valid, missing = validate_firebase_config()

    if is_valid:
        print("✅ Todas as configurações do Firebase estão definidas")
    else:
        print("⚠️  Configurações pendentes:")
        for config in missing:
            print(f"   - {config}")
        print("\n💡 Atualize o arquivo .env com as credenciais corretas do Firebase")


if __name__ == "__main__":
    print_firebase_status()
