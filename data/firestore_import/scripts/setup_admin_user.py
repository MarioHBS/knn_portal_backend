#!/usr/bin/env python3
"""
Script para configurar o usuário administrador com as custom claims necessárias.
"""

import os
import firebase_admin
from firebase_admin import auth, credentials

# Configurações
FIREBASE_CREDENTIALS_PATH = "data/firestore_import/default-service-account-key.json"
ADMIN_EMAIL = "developer.mario.santos@gmail.com"
ADMIN_PASSWORD = "Mh654321"

def setup_admin_user():
    """Configura o usuário administrador com custom claims."""
    
    try:
        # Inicializar Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred)
        
        print(f"🔍 Verificando usuário: {ADMIN_EMAIL}")
        
        # Verificar se usuário existe
        try:
            user = auth.get_user_by_email(ADMIN_EMAIL)
            print(f"✅ Usuário encontrado: {user.uid}")
            
        except auth.UserNotFoundError:
            print(f"❌ Usuário {ADMIN_EMAIL} não encontrado. Criando...")
            
            # Criar usuário
            user = auth.create_user(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                email_verified=True,
                display_name="Mario Santos (Admin)"
            )
            print(f"✅ Usuário criado: {user.uid}")
        
        # Configurar custom claims para administrador
        custom_claims = {
            'role': 'admin',
            'tenant': 'knn-dev-tenant',
            'permissions': [
                'read:all',
                'write:all',
                'admin:partners',
                'admin:students', 
                'admin:employees',
                'admin:metrics',
                'admin:reports'
            ],
            'created_by': 'admin_setup_script',
            'is_admin': True
        }
        
        print(f"🔧 Configurando custom claims...")
        auth.set_custom_user_claims(user.uid, custom_claims)
        
        # Verificar se as claims foram definidas
        updated_user = auth.get_user(user.uid)
        actual_claims = updated_user.custom_claims or {}
        
        print(f"✅ Custom claims configuradas:")
        for key, value in actual_claims.items():
            print(f"   {key}: {value}")
        
        # Gerar token personalizado para teste
        print(f"\n🎫 Gerando token personalizado...")
        custom_token = auth.create_custom_token(user.uid, custom_claims)
        
        print(f"✅ Token personalizado gerado (primeiros 50 chars): {custom_token.decode()[:50]}...")
        
        # Salvar informações em arquivo
        admin_info = {
            "uid": user.uid,
            "email": ADMIN_EMAIL,
            "custom_claims": actual_claims,
            "token_preview": custom_token.decode()[:100] + "...",
            "full_token": custom_token.decode()
        }
        
        import json
        with open("admin_user_info.json", "w", encoding="utf-8") as f:
            json.dump(admin_info, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 Informações salvas em: admin_user_info.json")
        print(f"\n🎯 Usuário administrador configurado com sucesso!")
        print(f"   Email: {ADMIN_EMAIL}")
        print(f"   UID: {user.uid}")
        print(f"   Role: {actual_claims.get('role', 'N/A')}")
        print(f"   Tenant: {actual_claims.get('tenant', 'N/A')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao configurar usuário administrador: {str(e)}")
        return False

def main():
    """Função principal."""
    print("🚀 Configurando usuário administrador...\n")
    
    if not os.path.exists(FIREBASE_CREDENTIALS_PATH):
        print(f"❌ Arquivo de credenciais não encontrado: {FIREBASE_CREDENTIALS_PATH}")
        return
    
    success = setup_admin_user()
    
    if success:
        print("\n✅ Configuração concluída com sucesso!")
        print("\n📋 Próximos passos:")
        print("   1. Execute testes de funcionalidades administrativas")
        print("   2. Verifique se os endpoints da API funcionam corretamente")
        print("   3. Teste operações de CRUD administrativas")
    else:
        print("\n❌ Falha na configuração do usuário administrador.")

if __name__ == "__main__":
    main()