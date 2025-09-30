#!/usr/bin/env python3
"""
Script de debug para investigar problemas na busca de benefícios do parceiro.

Este script verifica detalhadamente onde o parceiro PTN_T4L5678_TEC
deveria estar armazenado e por que não está sendo encontrado.

Autor: Sistema de Debug KNN
Data: 2025-01-06
"""

import json
import os
import sys
from datetime import datetime

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from src.db.firestore import get_database
except ImportError:
    # Fallback para importação direta
    import os
    import sys
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
    sys.path.insert(0, root_dir)
    from src.db.firestore import get_database


class PartnerBenefitsDebugger:
    """Classe para debug da busca de benefícios do parceiro."""

    def __init__(self):
        """Inicializa o debugger."""
        self.db = get_database()
        self.partner_id = "PTN_T4L5678_TEC"
        self.partner_email = "parceiro.teste@journeyclub.com.br"
        self.tenant_id = "knn-dev-tenant"

    def print_step(self, message: str, status: str = "INFO") -> None:
        """Imprime uma etapa do processo."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "DEBUG": "🔍"
        }.get(status, "ℹ️")
        print(f"[{timestamp}] {status_icon} {message}")

    def check_direct_document_access(self) -> dict:
        """Verifica acesso direto ao documento do parceiro."""
        self.print_step("=== VERIFICAÇÃO DE ACESSO DIRETO ===", "DEBUG")

        results = {
            "benefits_collection": None,
            "partner_benefits_index": None,
            "document_exists": False,
            "document_data": None
        }

        # 1. Tentar acessar diretamente na coleção 'benefits'
        try:
            self.print_step(f"Buscando documento na coleção 'benefits' com ID: {self.partner_id}", "DEBUG")
            doc_ref = self.db.collection("benefits").document(self.partner_id)
            doc = doc_ref.get()

            if doc.exists:
                results["benefits_collection"] = True
                results["document_exists"] = True
                results["document_data"] = doc.to_dict()
                self.print_step("✅ Documento encontrado na coleção 'benefits'", "SUCCESS")
                self.print_step(f"Dados: {list(results['document_data'].keys())}", "INFO")
            else:
                results["benefits_collection"] = False
                self.print_step("❌ Documento NÃO encontrado na coleção 'benefits'", "ERROR")

        except Exception as e:
            self.print_step(f"Erro ao acessar coleção 'benefits': {str(e)}", "ERROR")
            results["benefits_collection"] = f"Erro: {str(e)}"

        # 2. Tentar acessar na coleção 'partner_benefits_index'
        try:
            self.print_step(f"Buscando documento na coleção 'partner_benefits_index' com ID: {self.partner_id}", "DEBUG")
            doc_ref = self.db.collection("partner_benefits_index").document(self.partner_id)
            doc = doc_ref.get()

            if doc.exists:
                results["partner_benefits_index"] = True
                if not results["document_exists"]:
                    results["document_exists"] = True
                    results["document_data"] = doc.to_dict()
                self.print_step("✅ Documento encontrado na coleção 'partner_benefits_index'", "SUCCESS")
            else:
                results["partner_benefits_index"] = False
                self.print_step("❌ Documento NÃO encontrado na coleção 'partner_benefits_index'", "ERROR")

        except Exception as e:
            self.print_step(f"Erro ao acessar coleção 'partner_benefits_index': {str(e)}", "ERROR")
            results["partner_benefits_index"] = f"Erro: {str(e)}"

        return results

    def search_by_email(self) -> dict:
        """Busca o parceiro pelo email em diferentes coleções."""
        self.print_step("=== BUSCA POR EMAIL ===", "DEBUG")

        results = {
            "benefits_by_email": [],
            "partner_benefits_index_by_email": []
        }

        # 1. Buscar na coleção 'benefits' por email
        try:
            self.print_step(f"Buscando por email na coleção 'benefits': {self.partner_email}", "DEBUG")
            query = self.db.collection("benefits").where("partner_email", "==", self.partner_email)
            docs = query.get()

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["document_id"] = doc.id
                results["benefits_by_email"].append(doc_data)

            if results["benefits_by_email"]:
                self.print_step(f"✅ Encontrados {len(results['benefits_by_email'])} documentos por email na coleção 'benefits'", "SUCCESS")
                for doc in results["benefits_by_email"]:
                    self.print_step(f"  - ID: {doc['document_id']}", "INFO")
            else:
                self.print_step("❌ Nenhum documento encontrado por email na coleção 'benefits'", "ERROR")

        except Exception as e:
            self.print_step(f"Erro ao buscar por email na coleção 'benefits': {str(e)}", "ERROR")

        # 2. Buscar na coleção 'partner_benefits_index' por email
        try:
            self.print_step(f"Buscando por email na coleção 'partner_benefits_index': {self.partner_email}", "DEBUG")
            query = self.db.collection("partner_benefits_index").where("partner_email", "==", self.partner_email)
            docs = query.get()

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data["document_id"] = doc.id
                results["partner_benefits_index_by_email"].append(doc_data)

            if results["partner_benefits_index_by_email"]:
                self.print_step(f"✅ Encontrados {len(results['partner_benefits_index_by_email'])} documentos por email na coleção 'partner_benefits_index'", "SUCCESS")
                for doc in results["partner_benefits_index_by_email"]:
                    self.print_step(f"  - ID: {doc['document_id']}", "INFO")
            else:
                self.print_step("❌ Nenhum documento encontrado por email na coleção 'partner_benefits_index'", "ERROR")

        except Exception as e:
            self.print_step(f"Erro ao buscar por email na coleção 'partner_benefits_index': {str(e)}", "ERROR")

        return results

    def list_all_documents(self) -> dict:
        """Lista todos os documentos nas coleções relevantes."""
        self.print_step("=== LISTAGEM DE TODOS OS DOCUMENTOS ===", "DEBUG")

        results = {
            "benefits_all": [],
            "partner_benefits_index_all": []
        }

        # 1. Listar todos os documentos na coleção 'benefits'
        try:
            self.print_step("Listando todos os documentos na coleção 'benefits'", "DEBUG")
            docs = self.db.collection("benefits").get()

            for doc in docs:
                doc_data = {
                    "document_id": doc.id,
                    "has_partner_email": "partner_email" in doc.to_dict(),
                    "partner_email": doc.to_dict().get("partner_email", "N/A"),
                    "data_keys": list(doc.to_dict().keys())
                }
                results["benefits_all"].append(doc_data)

            self.print_step(f"✅ Encontrados {len(results['benefits_all'])} documentos na coleção 'benefits'", "SUCCESS")
            for doc in results["benefits_all"]:
                self.print_step(f"  - ID: {doc['document_id']}, Email: {doc['partner_email']}", "INFO")

        except Exception as e:
            self.print_step(f"Erro ao listar documentos da coleção 'benefits': {str(e)}", "ERROR")

        # 2. Listar todos os documentos na coleção 'partner_benefits_index'
        try:
            self.print_step("Listando todos os documentos na coleção 'partner_benefits_index'", "DEBUG")
            docs = self.db.collection("partner_benefits_index").get()

            for doc in docs:
                doc_data = {
                    "document_id": doc.id,
                    "has_partner_email": "partner_email" in doc.to_dict(),
                    "partner_email": doc.to_dict().get("partner_email", "N/A"),
                    "data_keys": list(doc.to_dict().keys())
                }
                results["partner_benefits_index_all"].append(doc_data)

            self.print_step(f"✅ Encontrados {len(results['partner_benefits_index_all'])} documentos na coleção 'partner_benefits_index'", "SUCCESS")
            for doc in results["partner_benefits_index_all"]:
                self.print_step(f"  - ID: {doc['document_id']}, Email: {doc['partner_email']}", "INFO")

        except Exception as e:
            self.print_step(f"Erro ao listar documentos da coleção 'partner_benefits_index': {str(e)}", "ERROR")

        return results

    def check_api_logic_simulation(self) -> dict:
        """Simula a lógica da API para buscar benefícios."""
        self.print_step("=== SIMULAÇÃO DA LÓGICA DA API ===", "DEBUG")

        results = {
            "entity_id": self.partner_id,
            "tenant_id": self.tenant_id,
            "firestore_document": None,
            "benefits_found": [],
            "api_would_return": []
        }

        try:
            # Simular a busca que a API faz
            self.print_step(f"Simulando busca da API: get_document('benefits', '{self.partner_id}', tenant_id='{self.tenant_id}')", "DEBUG")

            # Buscar documento diretamente como a API faz
            doc_ref = self.db.collection("benefits").document(self.partner_id)
            doc = doc_ref.get()

            if doc.exists:
                doc_data = doc.to_dict()
                results["firestore_document"] = doc_data
                self.print_step("✅ Documento encontrado pela simulação da API", "SUCCESS")

                # Extrair benefícios como a API faz
                benefits_data = doc_data.get("data", {})
                self.print_step(f"Campo 'data' encontrado: {bool(benefits_data)}", "INFO")

                if benefits_data:
                    self.print_step(f"Chaves no campo 'data': {list(benefits_data.keys())}", "INFO")

                    # Filtrar benefícios que começam com BNF_
                    for key, value in benefits_data.items():
                        if key.startswith("BNF_") and isinstance(value, dict):
                            results["benefits_found"].append({
                                "key": key,
                                "data": value
                            })
                            results["api_would_return"].append(value)

                    self.print_step(f"Benefícios que começam com 'BNF_': {len(results['benefits_found'])}", "INFO")
                    for benefit in results["benefits_found"]:
                        self.print_step(f"  - {benefit['key']}: {list(benefit['data'].keys())}", "INFO")
                else:
                    self.print_step("❌ Campo 'data' não encontrado ou vazio", "ERROR")
            else:
                self.print_step("❌ Documento não encontrado pela simulação da API", "ERROR")

        except Exception as e:
            self.print_step(f"Erro na simulação da API: {str(e)}", "ERROR")

        return results

    def run_complete_debug(self) -> dict:
        """Executa o debug completo."""
        print("="*80)
        print(" DEBUG COMPLETO - BUSCA DE BENEFÍCIOS DO PARCEIRO")
        print("="*80)
        print(f" Parceiro ID: {self.partner_id}")
        print(f" Email: {self.partner_email}")
        print(f" Tenant: {self.tenant_id}")
        print("="*80)

        results = {
            "partner_id": self.partner_id,
            "partner_email": self.partner_email,
            "tenant_id": self.tenant_id,
            "direct_access": {},
            "email_search": {},
            "all_documents": {},
            "api_simulation": {},
            "timestamp": datetime.now().isoformat()
        }

        # 1. Verificação de acesso direto
        results["direct_access"] = self.check_direct_document_access()

        # 2. Busca por email
        results["email_search"] = self.search_by_email()

        # 3. Listagem de todos os documentos
        results["all_documents"] = self.list_all_documents()

        # 4. Simulação da lógica da API
        results["api_simulation"] = self.check_api_logic_simulation()

        return results

    def save_results(self, results: dict) -> str:
        """Salva os resultados em um arquivo JSON."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"partner_benefits_debug_{timestamp}.json"
        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)

            self.print_step(f"Resultados salvos em: {filepath}", "SUCCESS")
            return filepath
        except Exception as e:
            self.print_step(f"Erro ao salvar resultados: {str(e)}", "ERROR")
            return ""


def main():
    """Função principal."""
    debugger = PartnerBenefitsDebugger()
    results = debugger.run_complete_debug()
    debugger.save_results(results)

    # Resumo final
    print("\n" + "="*80)
    print(" RESUMO DO DEBUG")
    print("="*80)

    if results["direct_access"]["document_exists"]:
        print("✅ Documento do parceiro ENCONTRADO")
        if results["api_simulation"]["benefits_found"]:
            print(f"✅ {len(results['api_simulation']['benefits_found'])} benefícios encontrados")
        else:
            print("⚠️ Documento encontrado mas SEM benefícios válidos")
    else:
        print("❌ Documento do parceiro NÃO ENCONTRADO")

    if results["email_search"]["benefits_by_email"] or results["email_search"]["partner_benefits_index_by_email"]:
        print("✅ Parceiro encontrado por email em alguma coleção")
    else:
        print("❌ Parceiro NÃO encontrado por email")

    return 0 if results["direct_access"]["document_exists"] else 1


if __name__ == "__main__":
    sys.exit(main())
