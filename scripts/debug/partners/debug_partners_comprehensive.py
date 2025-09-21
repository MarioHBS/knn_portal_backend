#!/usr/bin/env python3
"""
Script Consolidado para Debug de Partners

Este script consolida as funcionalidades de debug relacionadas aos partners:
- debug_partners_firestore.py: Análise detalhada da estrutura dos documentos
- debug_partners_query.py: Teste de consultas com filtros
- debug_partners_raw.py: Acesso direto à coleção sem filtros
- debug_student_partners.py: Simulação do endpoint student/partners

Funcionalidades:
1. Análise da estrutura dos documentos partners
2. Teste de consultas com diferentes filtros
3. Simulação do endpoint student/partners
4. Estatísticas e validações dos dados

Uso:
    python scripts/debug/partners/debug_partners_comprehensive.py [modo]

Modos disponíveis:
    - structure: Análise da estrutura dos documentos
    - query: Teste de consultas com filtros
    - endpoint: Simulação do endpoint student/partners
    - all: Executa todos os modos (padrão)
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.models.partner import Partner
    from src.services.partners_service import PartnersService
    from src.utils.firestore_client import FirestoreClient
    from src.utils.jwt_payload import JWTPayload
except ImportError as e:
    print(f"Erro ao importar módulos do projeto: {e}")
    print("Certifique-se de que está executando do diretório raiz do projeto")
    sys.exit(1)


class PartnersDebugger:
    """Classe principal para debug dos partners."""

    def __init__(self):
        """Inicializa o debugger."""
        self.firestore_client = None
        self.partners_service = None

    async def initialize(self):
        """Inicializa os clientes necessários."""
        try:
            self.firestore_client = FirestoreClient()
            await self.firestore_client.initialize()
            self.partners_service = PartnersService(self.firestore_client)
            print("✅ Clientes inicializados com sucesso")
        except Exception as e:
            print(f"❌ Erro ao inicializar clientes: {e}")
            raise

    async def analyze_structure(self) -> dict[str, Any]:
        """
        Analisa a estrutura dos documentos partners.
        Baseado em debug_partners_firestore.py e debug_partners_raw.py
        """
        print("\n" + "="*60)
        print("🔍 ANÁLISE DA ESTRUTURA DOS DOCUMENTOS PARTNERS")
        print("="*60)

        try:
            # Busca todos os documentos da coleção partners
            partners_ref = self.firestore_client.db.collection('partners')
            docs = partners_ref.stream()

            all_docs = []
            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['_id'] = doc.id
                all_docs.append(doc_data)

            total_docs = len(all_docs)
            print(f"📊 Total de documentos encontrados: {total_docs}")

            if total_docs == 0:
                print("⚠️  Nenhum documento encontrado na coleção 'partners'")
                return {"total_docs": 0, "analysis": "No documents found"}

            # Análise dos campos obrigatórios do modelo Partner
            required_fields = ['name', 'active', 'tenant_id']
            missing_fields_count = {field: 0 for field in required_fields}

            # Estatísticas gerais
            stats = {
                'total_docs': total_docs,
                'empty_fields': {},
                'inactive_partners': 0,
                'partners_without_tenant': 0,
                'tenant_distribution': {},
                'active_field_types': {},
                'model_validation_errors': 0,
                'unique_fields': set()
            }

            # Análise documento por documento
            for _i, doc_data in enumerate(all_docs):
                # Coleta todos os campos únicos
                stats['unique_fields'].update(doc_data.keys())

                # Verifica campos obrigatórios
                for field in required_fields:
                    if field not in doc_data or doc_data[field] is None or doc_data[field] == '':
                        missing_fields_count[field] += 1

                # Análise do campo active
                if 'active' in doc_data:
                    active_value = doc_data['active']
                    active_type = type(active_value).__name__
                    stats['active_field_types'][active_type] = stats['active_field_types'].get(active_type, 0) + 1

                    # Considera inativo se não for True (boolean)
                    if active_value is not True:
                        stats['inactive_partners'] += 1

                # Análise do tenant_id
                if 'tenant_id' not in doc_data or not doc_data['tenant_id']:
                    stats['partners_without_tenant'] += 1
                else:
                    tenant_id = doc_data['tenant_id']
                    stats['tenant_distribution'][tenant_id] = stats['tenant_distribution'].get(tenant_id, 0) + 1

                # Tenta criar instância do modelo Partner
                try:
                    Partner(**doc_data)
                except Exception:
                    stats['model_validation_errors'] += 1

                # Análise de campos vazios
                for key, value in doc_data.items():
                    if value is None or value == '':
                        stats['empty_fields'][key] = stats['empty_fields'].get(key, 0) + 1

            # Relatório final
            print("\n📋 RELATÓRIO DE ESTRUTURA:")
            print(f"   • Total de documentos: {stats['total_docs']}")
            print(f"   • Erros de validação do modelo: {stats['model_validation_errors']}")
            print(f"   • Partners inativos: {stats['inactive_partners']}")
            print(f"   • Partners sem tenant_id: {stats['partners_without_tenant']}")

            print("\n🔍 CAMPOS OBRIGATÓRIOS AUSENTES:")
            for field, count in missing_fields_count.items():
                if count > 0:
                    print(f"   • {field}: {count} documentos")

            print("\n📊 TIPOS DO CAMPO 'active':")
            for type_name, count in stats['active_field_types'].items():
                print(f"   • {type_name}: {count} documentos")

            print("\n🏢 DISTRIBUIÇÃO POR TENANT:")
            for tenant_id, count in sorted(stats['tenant_distribution'].items()):
                print(f"   • {tenant_id}: {count} partners")

            print(f"\n📝 CAMPOS ÚNICOS ENCONTRADOS ({len(stats['unique_fields'])}):")
            for field in sorted(stats['unique_fields']):
                print(f"   • {field}")

            return stats

        except Exception as e:
            print(f"❌ Erro na análise da estrutura: {e}")
            return {"error": str(e)}

    async def test_queries(self, test_tenant_id: str = "tenant_123") -> dict[str, Any]:
        """
        Testa diferentes tipos de consultas.
        Baseado em debug_partners_query.py
        """
        print("\n" + "="*60)
        print("🔍 TESTE DE CONSULTAS COM FILTROS")
        print("="*60)

        results = {}

        try:
            partners_ref = self.firestore_client.db.collection('partners')

            # Teste 1: Consulta sem filtros
            print("\n1️⃣ Consulta sem filtros:")
            docs = partners_ref.stream()
            all_partners = [doc.to_dict() for doc in docs]
            results['no_filter'] = len(all_partners)
            print(f"   Resultado: {results['no_filter']} partners encontrados")

            # Teste 2: Filtro por tenant_id
            print(f"\n2️⃣ Filtro por tenant_id = '{test_tenant_id}':")
            query = partners_ref.where('tenant_id', '==', test_tenant_id)
            docs = query.stream()
            tenant_partners = [doc.to_dict() for doc in docs]
            results['tenant_filter'] = len(tenant_partners)
            print(f"   Resultado: {results['tenant_filter']} partners encontrados")

            # Teste 3: Filtro por active = True
            print("\n3️⃣ Filtro por active = True:")
            query = partners_ref.where('active', '==', True)
            docs = query.stream()
            active_partners = [doc.to_dict() for doc in docs]
            results['active_true'] = len(active_partners)
            print(f"   Resultado: {results['active_true']} partners encontrados")

            # Teste 4: Filtro combinado (tenant_id + active)
            print("\n4️⃣ Filtro combinado (tenant_id + active = True):")
            query = partners_ref.where('tenant_id', '==', test_tenant_id).where('active', '==', True)
            docs = query.stream()
            combined_partners = [doc.to_dict() for doc in docs]
            results['combined_filter'] = len(combined_partners)
            print(f"   Resultado: {results['combined_filter']} partners encontrados")

            # Teste 5: Diferentes valores de active
            print("\n5️⃣ Teste com diferentes valores de 'active':")
            active_values = [True, "true", 1, "1", False, "false", 0, "0"]
            for value in active_values:
                try:
                    query = partners_ref.where('active', '==', value)
                    docs = query.stream()
                    count = len(list(docs))
                    results[f'active_{value}'] = count
                    print(f"   active = {value} ({type(value).__name__}): {count} partners")
                except Exception as e:
                    print(f"   active = {value}: Erro - {e}")

            return results

        except Exception as e:
            print(f"❌ Erro nos testes de consulta: {e}")
            return {"error": str(e)}

    async def simulate_endpoint(self, user_tenant_id: str = "tenant_123") -> dict[str, Any]:
        """
        Simula o endpoint student/partners.
        Baseado em debug_student_partners.py
        """
        print("\n" + "="*60)
        print("🔍 SIMULAÇÃO DO ENDPOINT STUDENT/PARTNERS")
        print("="*60)

        results = {}

        try:
            # Simula dados do usuário estudante
            user_payload = JWTPayload(
                user_id="test_student_123",
                tenant_id=user_tenant_id,
                role="student",
                exp=int(datetime.now().timestamp()) + 3600
            )

            print("👤 Usuário simulado:")
            print(f"   • ID: {user_payload.user_id}")
            print(f"   • Tenant ID: {user_payload.tenant_id}")
            print(f"   • Role: {user_payload.role}")

            # Teste 1: Consulta direta no Firestore (sem filtro active)
            print("\n1️⃣ Consulta direta no Firestore (sem filtro active):")
            try:
                partners_ref = self.firestore_client.db.collection('partners')
                query = partners_ref.where('tenant_id', '==', user_payload.tenant_id)
                docs = query.stream()
                direct_partners = [doc.to_dict() for doc in docs]
                results['direct_query'] = len(direct_partners)
                print(f"   Resultado: {results['direct_query']} partners encontrados")

                # Mostra alguns exemplos
                if direct_partners:
                    print("   Exemplos (primeiros 3):")
                    for i, partner in enumerate(direct_partners[:3]):
                        print(f"     {i+1}. {partner.get('name', 'N/A')} (active: {partner.get('active', 'N/A')})")

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                results['direct_query'] = f"Error: {e}"

            # Teste 2: Consulta com filtro active = True
            print("\n2️⃣ Consulta com filtro active = True:")
            try:
                partners_ref = self.firestore_client.db.collection('partners')
                query = partners_ref.where('tenant_id', '==', user_payload.tenant_id).where('active', '==', True)
                docs = query.stream()
                active_partners = [doc.to_dict() for doc in docs]
                results['active_query'] = len(active_partners)
                print(f"   Resultado: {results['active_query']} partners encontrados")

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                results['active_query'] = f"Error: {e}"

            # Teste 3: Usando PartnersService (simulação do endpoint real)
            print("\n3️⃣ Usando PartnersService (endpoint real):")
            try:
                partners_list = await self.partners_service.list_partners(user_payload)
                results['service_query'] = len(partners_list)
                print(f"   Resultado: {results['service_query']} partners encontrados")

                # Mostra alguns exemplos
                if partners_list:
                    print("   Exemplos (primeiros 3):")
                    for i, partner in enumerate(partners_list[:3]):
                        print(f"     {i+1}. {partner.name} (active: {partner.active})")

            except Exception as e:
                print(f"   ❌ Erro: {e}")
                results['service_query'] = f"Error: {e}"

            # Comparação dos resultados
            print("\n📊 COMPARAÇÃO DOS RESULTADOS:")
            print(f"   • Consulta direta (sem active): {results.get('direct_query', 'N/A')}")
            print(f"   • Consulta com active=True: {results.get('active_query', 'N/A')}")
            print(f"   • PartnersService (endpoint): {results.get('service_query', 'N/A')}")

            return results

        except Exception as e:
            print(f"❌ Erro na simulação do endpoint: {e}")
            return {"error": str(e)}

    async def run_comprehensive_debug(self, mode: str = "all"):
        """Executa o debug completo baseado no modo especificado."""
        print("🚀 Iniciando Debug Consolidado dos Partners")
        print(f"📋 Modo selecionado: {mode}")

        await self.initialize()

        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode
        }

        if mode in ["all", "structure"]:
            results["structure_analysis"] = await self.analyze_structure()

        if mode in ["all", "query"]:
            results["query_tests"] = await self.test_queries()

        if mode in ["all", "endpoint"]:
            results["endpoint_simulation"] = await self.simulate_endpoint()

        print("\n" + "="*60)
        print("✅ DEBUG CONSOLIDADO CONCLUÍDO")
        print("="*60)

        return results


async def main():
    """Função principal."""
    # Determina o modo de execução
    mode = "all"
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ["structure", "query", "endpoint", "all"]:
            print(f"❌ Modo inválido: {mode}")
            print("Modos disponíveis: structure, query, endpoint, all")
            sys.exit(1)

    debugger = PartnersDebugger()

    try:
        results = await debugger.run_comprehensive_debug(mode)

        # Salva os resultados em arquivo JSON
        output_file = f"debug_partners_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False, default=str)

        print(f"\n💾 Resultados salvos em: {output_file}")

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
