"""
Script para iniciar o servidor FastAPI para testes locais.
"""

import os
import sys
from pathlib import Path

import uvicorn

# Adicionar o diretório raiz do projeto ao PYTHONPATH
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("Iniciando servidor FastAPI para o Portal de Benefícios KNN...")
    print("Acesse a documentação em: http://localhost:8080/v1/docs")

    # Carregar configurações do .env
    try:
        from dotenv import load_dotenv

        env_path = project_root / ".env"
        if env_path.exists():
            load_dotenv(env_path)
            print(f"Carregadas variáveis de ambiente de: {env_path}")
    except ImportError:
        print("python-dotenv não encontrado, usando variáveis de ambiente do sistema")

    # Obter porta das variáveis de ambiente
    port = int(os.getenv("PORT", "8080"))

    uvicorn.run("src.main:app", host="0.0.0.0", port=port, reload=True)
