#!/usr/bin/env python3
"""
Script para verificar o mapeamento entre usuário e entidade parceiro.
Verifica se o entity_id do usuário corresponde ao documento do parceiro.
"""

import json
import os
import sys
from datetime import datetime
from typing import Any

# Adicionar o diretório raiz ao path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.db.firestore import get_database


class PartnerEntityMappingVerifier:
    """Classe para verificar o mapeamento entre usuário e entidade parceiro."""

    def __init__(self):
        """Inicializa o verificador."""
        self.db = get_database()
        self.target_email = "parceiro.teste@journeyclub.com.br"
        self.expected_partner_id = "PTN_T4L5678_TEC"

    def print_header(self, title: str):
        """Imprime cabeçalho formatado."""
        print(f"\n{'='*80}")
        print(f" {title}")
        print(f"{'='*80}")

    def print_step(self, message: str, status: str = "INFO"):
        """Imprime mensagem de etapa."""
        icons = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️"
        }
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {icons.get(status, 'ℹ️')} {message}")

    def find_user_by_email(self) -> dict[str, Any]:
        """Encontra o usuário pelo email."""
        self.print_step(f"Procurando usuário com email: {self.target_email}")

        try:
            # Buscar na coleção users do tenant padrão
            users_ref = self.db.collection("users")
            users_query = users_ref.where("email", "==", self.target_email).limit(1)
            users_docs = users_query.get()

            if users_docs:
                user_doc = users_docs[0]
                user_data = user_doc.to_dict()
                user_data["uid"] = user_doc.id

                self.print_step(f"Usuário encontrado: {user_doc.id}", "SUCCESS")
                self.print_step(f"Entity ID: {user_data.get('entity_id', 'N/A')}")
                self.print_step(f"Role: {user_data.get('role', 'N/A')}")
                self.print_step(f"Tenant ID: {user_data.get('tenant_id', 'N/A')}")

                return user_data
            else:
                self.print_step("Usuário não encontrado na coleção users", "ERROR")
                return {}

        except Exception as e:
            self.print_step(f"Erro ao buscar usuário: {str(e)}", "ERROR")
            return {}

    def verify_partner_document(self, partner_id: str) -> dict[str, Any]:
        """Verifica se existe documento do parceiro com o ID especificado."""
        self.print_step(f"Verificando documento do parceiro: {partner_id}")

        try:
            # Verificar na coleção benefits (onde estão os parceiros)
            partner_ref = self.db.collection("benefits").document(partner_id)
            partner_doc = partner_ref.get()

            if partner_doc.exists:
                partner_data = partner_doc.to_dict()
                self.print_step("Documento do parceiro encontrado", "SUCCESS")
                self.print_step(f"Título: {partner_data.get('title', 'N/A')}")
                self.print_step(f"Descrição: {partner_data.get('description', 'N/A')}")

                return partner_data
            else:
                self.print_step("Documento do parceiro não encontrado", "ERROR")
                return {}

        except Exception as e:
            self.print_step(f"Erro ao verificar documento do parceiro: {str(e)}", "ERROR")
            return {}

    def search_partner_by_email(self) -> dict[str, Any]:
        """Procura parceiro que contenha o email nos dados."""
        self.print_step(f"Procurando parceiro com email: {self.target_email}")

        try:
            # Buscar em todos os documentos da coleção benefits
            benefits_ref = self.db.collection("benefits")
            all_docs = benefits_ref.get()

            found_partners = []

            for doc in all_docs:
                doc_data = doc.to_dict()
                doc_id = doc.id

                # Verificar se o documento contém o email
                doc_str = json.dumps(doc_data, default=str).lower()
                if self.target_email.lower() in doc_str:
                    found_partners.append({
                        "id": doc_id,
                        "data": doc_data
                    })
                    self.print_step(f"Parceiro encontrado: {doc_id}", "SUCCESS")

            if not found_partners:
                self.print_step("Nenhum parceiro encontrado com esse email", "WARNING")

            return {"found_partners": found_partners}

        except Exception as e:
            self.print_step(f"Erro ao procurar parceiro por email: {str(e)}", "ERROR")
            return {"found_partners": []}

    def update_user_entity_id(self, user_uid: str, new_entity_id: str) -> bool:
        """Atualiza o entity_id do usuário."""
        self.print_step(f"Atualizando entity_id do usuário {user_uid} para {new_entity_id}")

        try:
            user_ref = self.db.collection("users").document(user_uid)
            user_ref.update({"entity_id": new_entity_id})

            self.print_step("Entity ID atualizado com sucesso", "SUCCESS")
            return True

        except Exception as e:
            self.print_step(f"Erro ao atualizar entity_id: {str(e)}", "ERROR")
            return False

    def create_partner_document(self) -> bool:
        """Cria documento do parceiro se não existir."""
        self.print_step(f"Criando documento do parceiro: {self.expected_partner_id}")

        partner_data = {
            "title": "TechSolutions Ltda",
            "description": "Empresa especializada em soluções tecnológicas para educação",
            "system": {
                "tenant_id": "knn-dev-tenant",
                "type": "partner",
                "status": "active",
                "category": "tecnologia",
                "audience": ["student", "employee"]
            },
            "configuration": {
                "value": 15.0,
                "calculation_method": "percentage",
                "terms": "Desconto de 15% em todos os serviços"
            },
            "dates": {
                "created_at": datetime.now().isoformat(),
                "valid_from": datetime.now().isoformat(),
                "valid_to": "2025-12-31T23:59:59"
            },
            "limits": {
                "temporal": {
                    "type": "monthly",
                    "value": 1
                },
                "usage": {
                    "max_uses": 10,
                    "current_uses": 0
                }
            },
            "metadata": {
                "tags": ["tecnologia", "educacao", "software"],
                "contact_email": self.target_email,
                "contact_phone": "(11) 99999-3333"
            }
        }

        try:
            partner_ref = self.db.collection("benefits").document(self.expected_partner_id)
            partner_ref.set(partner_data)

            self.print_step("Documento do parceiro criado com sucesso", "SUCCESS")
            return True

        except Exception as e:
            self.print_step(f"Erro ao criar documento do parceiro: {str(e)}", "ERROR")
            return False

    def run_verification(self) -> dict[str, Any]:
        """Executa a verificação completa."""
        self.print_header("VERIFICAÇÃO DE MAPEAMENTO USUÁRIO-PARCEIRO")

        results = {
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "target_email": self.target_email,
            "expected_partner_id": self.expected_partner_id,
            "user_data": {},
            "partner_document": {},
            "partner_search": {},
            "mapping_correct": False,
            "actions_taken": []
        }

        # 1. Encontrar usuário
        user_data = self.find_user_by_email()
        results["user_data"] = user_data

        if not user_data:
            self.print_step("Não é possível continuar sem dados do usuário", "ERROR")
            return results

        # 2. Verificar documento do parceiro esperado
        partner_document = self.verify_partner_document(self.expected_partner_id)
        results["partner_document"] = partner_document

        # 3. Procurar parceiro por email
        partner_search = self.search_partner_by_email()
        results["partner_search"] = partner_search

        # 4. Verificar se o mapeamento está correto
        current_entity_id = user_data.get("entity_id")
        if current_entity_id == self.expected_partner_id:
            self.print_step("Mapeamento está correto!", "SUCCESS")
            results["mapping_correct"] = True
        else:
            self.print_step(f"Mapeamento incorreto. Atual: {current_entity_id}, Esperado: {self.expected_partner_id}", "WARNING")

            # 5. Corrigir mapeamento se necessário
            if not partner_document:
                self.print_step("Criando documento do parceiro...", "INFO")
                if self.create_partner_document():
                    results["actions_taken"].append("created_partner_document")

            if current_entity_id != self.expected_partner_id:
                self.print_step("Atualizando entity_id do usuário...", "INFO")
                if self.update_user_entity_id(user_data["uid"], self.expected_partner_id):
                    results["actions_taken"].append("updated_user_entity_id")
                    results["mapping_correct"] = True

        # Salvar resultados
        filename = f"partner_entity_mapping_verification_{results['timestamp']}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        self.print_step(f"Resultados salvos em: {filename}", "INFO")

        return results


def main():
    """Função principal."""
    try:
        verifier = PartnerEntityMappingVerifier()
        results = verifier.run_verification()

        if results["mapping_correct"]:
            print("\n✅ Verificação concluída com sucesso!")
            print(f"   Usuário: {results['target_email']}")
            print(f"   Entity ID: {results['expected_partner_id']}")
        else:
            print("\n❌ Problemas encontrados no mapeamento")
            print("   Verifique o arquivo de resultados para mais detalhes")

    except Exception as e:
        print(f"\n❌ Erro durante a verificação: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
