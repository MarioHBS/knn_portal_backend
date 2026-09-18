#!/usr/bin/env python3
"""
Script para testar diretamente a conexão com o Firestore.
Verifica se existem dados de parceiros e se a conexão está funcionando.
"""

import json
import os
import sys
from pathlib import Path

try:
    from google.cloud import firestore
    from dotenv import load_dotenv
except ImportError as e:
    print(f"Erro de importação: {e}")
    print("Execute: pip install google-cloud-firestore python-dotenv")
    sys.exit(1)


class FirestoreDirectTest:
    """Classe para testar diretamente o Firestore."""
    
    def __init__(self):
        """Inicializar o teste."""
        self.db = None
        
    def print_info(self, message: str) -> None:
        """Imprimir mensagem informativa."""
        print(f"ℹ️  {message}")
        
    def print_success(self, message: str) -> None:
        """Imprimir mensagem de sucesso."""
        print(f"✅ {message}")
        
    def print_error(self, message: str) -> None:
        """Imprimir mensagem de erro."""
        print(f"❌ {message}")
        
    def print_warning(self, message: str) -> None:
        """Imprimir mensagem de aviso."""
        print(f"⚠️  {message}")
    
    def setup_firestore(self) -> bool:
        """Configurar conexão com Firestore."""
        try:
            # Carregar .env
            env_file = Path(__file__).parent.parent.parent / ".env"
            if env_file.exists():
                load_dotenv(env_file)
                self.print_success("Arquivo .env carregado")
            else:
                self.print_warning("Arquivo .env não encontrado")
            
            # Configurar credenciais
            credentials_path = Path(__file__).parent.parent.parent / "credentials" / "default-service-account-key.json"
            if credentials_path.exists():
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(credentials_path)
                self.print_success(f"Credenciais configuradas: {credentials_path}")
            else:
                self.print_warning("Arquivo de credenciais não encontrado")
            
            # Inicializar Firestore
            project_id = os.getenv("FIREBASE_PROJECT_ID", "knn-benefits")
            self.print_info(f"Conectando ao projeto: {project_id}")
            
            self.db = firestore.Client(project=project_id)
            self.print_success("Conexão com Firestore estabelecida")
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro ao configurar Firestore: {str(e)}")
            return False
    
    def test_firestore_connection(self) -> bool:
        """Testar conexão básica com Firestore."""
        try:
            self.print_info("Testando conexão básica...")
            
            # Tentar listar coleções
            collections = list(self.db.collections())
            collection_names = [col.id for col in collections]
            
            self.print_success(f"Conexão OK! Encontradas {len(collections)} coleções:")
            for name in collection_names:
                self.print_info(f"  - {name}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro na conexão: {str(e)}")
            return False
    
    def check_partners_collection(self) -> bool:
        """Verificar a coleção de parceiros."""
        try:
            self.print_info("Verificando coleção 'partners'...")
            
            partners_ref = self.db.collection("partners")
            
            # Contar documentos
            partners_docs = list(partners_ref.limit(10).stream())
            
            if not partners_docs:
                self.print_warning("Nenhum parceiro encontrado na coleção 'partners'")
                
                # Verificar outras possíveis coleções
                possible_collections = ["Partners", "partner", "Partner", "parceiros", "Parceiros"]
                for col_name in possible_collections:
                    try:
                        col_ref = self.db.collection(col_name)
                        docs = list(col_ref.limit(1).stream())
                        if docs:
                            self.print_info(f"Encontrados dados na coleção '{col_name}'")
                            return self.analyze_collection(col_name)
                    except:
                        continue
                
                return False
            
            self.print_success(f"Encontrados {len(partners_docs)} parceiros")
            
            # Analisar alguns documentos
            for i, doc in enumerate(partners_docs[:3]):
                doc_data = doc.to_dict()
                partner_name = doc_data.get("name", doc_data.get("nome", "Nome não disponível"))
                self.print_info(f"  Parceiro {i+1}: {partner_name} (ID: {doc.id})")
            
            # Salvar dados para debug
            debug_data = []
            for doc in partners_docs:
                debug_data.append({
                    "id": doc.id,
                    "data": doc.to_dict()
                })
            
            debug_file = Path(__file__).parent / "debug_firestore_partners.json"
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.print_info(f"Dados salvos em: {debug_file}")
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro ao verificar parceiros: {str(e)}")
            return False
    
    def analyze_collection(self, collection_name: str) -> bool:
        """Analisar uma coleção específica."""
        try:
            self.print_info(f"Analisando coleção '{collection_name}'...")
            
            col_ref = self.db.collection(collection_name)
            docs = list(col_ref.limit(5).stream())
            
            self.print_success(f"Encontrados {len(docs)} documentos em '{collection_name}'")
            
            for i, doc in enumerate(docs):
                doc_data = doc.to_dict()
                self.print_info(f"  Documento {i+1} (ID: {doc.id}):")
                
                # Mostrar alguns campos principais
                for key in ["name", "nome", "title", "titulo", "id"]:
                    if key in doc_data:
                        self.print_info(f"    {key}: {doc_data[key]}")
                        break
            
            return True
            
        except Exception as e:
            self.print_error(f"Erro ao analisar coleção '{collection_name}': {str(e)}")
            return False
    
    def run_test(self) -> bool:
        """Executar o teste completo."""
        print("🚀 Testando conexão direta com Firestore...")
        print()
        
        # 1. Configurar Firestore
        if not self.setup_firestore():
            return False
        print()
        
        # 2. Testar conexão
        if not self.test_firestore_connection():
            return False
        print()
        
        # 3. Verificar parceiros
        success = self.check_partners_collection()
        print()
        
        if success:
            self.print_success("✨ Teste concluído com sucesso!")
        else:
            self.print_error("❌ Problemas encontrados no Firestore!")
            
        return success


def main():
    """Função principal."""
    tester = FirestoreDirectTest()
    success = tester.run_test()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()