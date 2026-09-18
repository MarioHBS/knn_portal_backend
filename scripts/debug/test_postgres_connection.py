#!/usr/bin/env python3
"""
Script para testar conexão com PostgreSQL.
"""

import asyncio
import asyncpg


async def test_postgres_connection():
    """Testar conexão com PostgreSQL."""
    try:
        print("🔧 Testando conexão com PostgreSQL...")
        
        conn = await asyncpg.connect(
            "postgresql://postgres:postgres@localhost:5432/knn_portal"
        )
        
        print("✅ Conexão PostgreSQL estabelecida com sucesso!")
        
        # Testar uma consulta simples
        result = await conn.fetchval("SELECT version()")
        print(f"📄 Versão do PostgreSQL: {result}")
        
        await conn.close()
        print("✅ Conexão fechada com sucesso!")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão PostgreSQL: {str(e)}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_postgres_connection())
    if not success:
        exit(1)