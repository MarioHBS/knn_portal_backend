#!/usr/bin/env python3
"""
Script Consolidado para Debug do Firestore

Este script consolida as funcionalidades de debug relacionadas ao Firestore:
- debug_firestore_collections.py: Lista e analisa coleções disponíveis
- debug_firestore_connection.py: Testa conectividade e configuração
- debug_firestore_raw_access.py: Acesso direto às coleções sem filtros

Funcionalidades:
1. Teste de conectividade com o Firestore
2. Listagem e análise de coleções disponíveis
3. Acesso direto a coleções específicas
4. Análise de estrutura de documentos
5. Estatísticas gerais do banco de dados

Uso:
    python scripts/debug/firestore/debug_firestore_raw.py [modo] [coleção]

Modos disponíveis:
    - connection: Testa conectividade
    - collections: Lista coleções disponíveis
    - analyze: Analisa coleção específica (requer parâmetro coleção)
    - all: Executa todos os modos (padrão)

Exemplos:
    python scripts/debug/firestore/debug_firestore_raw.py connection
    python scripts/debug/firestore/debug_firestore_raw.py analyze partners
    python scripts/debug/firestore/debug_firestore_raw.py all
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from google.cloud import firestore

# Adiciona o diretório raiz do projeto ao path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.utils.firestore_client import FirestoreClient
except ImportError as e:
    print(f"Erro ao importar FirestoreClient: {e}")
    print("Tentando inicializar Firestore diretamente...")


class FirestoreDebugger:
    """Classe principal para debug do Firestore."""

    def __init__(self):
        """Inicializa o debugger."""
        self.firestore_client = None
        self.db = None

    async def initialize(self):
        """Inicializa a conexão com o Firestore."""
        try:
            # Tenta usar o FirestoreClient do projeto
            try:
                self.firestore_client = FirestoreClient()
                await self.firestore_client.initialize()
                self.db = self.firestore_client.db
                print("✅ FirestoreClient do projeto inicializado com sucesso")
            except Exception as e:
                print(f"⚠️  Erro ao usar FirestoreClient do projeto: {e}")
                print("Tentando inicializar Firestore diretamente...")

                # Fallback: inicialização direta
                self.db = firestore.Client()
                print("✅ Cliente Firestore direto inicializado com sucesso")

        except Exception as e:
            print(f"❌ Erro ao inicializar Firestore: {e}")
            raise

    async def test_connection(self) -> dict[str, Any]:
        """
        Testa a conectividade com o Firestore.
        Baseado em debug_firestore_connection.py
        """
        print("\n" + "="*60)
        print("🔍 TESTE DE CONECTIVIDADE COM FIRESTORE")
        print("="*60)

        results = {
            "connection_status": "unknown",
            "project_id": None,
            "credentials_info": {},
            "test_operations": {}
        }

        try:
            # Informações do projeto
            if hasattr(self.db, '_project'):
                results["project_id"] = self.db._project
                print(f"📋 Project ID: {results['project_id']}")

            # Informações das credenciais
            try:
                # Verifica variáveis de ambiente relacionadas ao Firebase/Firestore
                env_vars = [
                    'GOOGLE_APPLICATION_CREDENTIALS',
                    'FIREBASE_PROJECT_ID',
                    'FIRESTORE_EMULATOR_HOST'
                ]

                for var in env_vars:
                    value = os.getenv(var)
                    results["credentials_info"][var] = value if value else "Not set"
                    print(f"🔑 {var}: {results['credentials_info'][var]}")

            except Exception as e:
                results["credentials_info"]["error"] = str(e)
                print(f"⚠️  Erro ao verificar credenciais: {e}")

            # Teste 1: Listar coleções
            print("\n1️⃣ Teste: Listar coleções")
            try:
                collections = self.db.collections()
                collection_names = [col.id for col in collections]
                results["test_operations"]["list_collections"] = {
                    "status": "success",
                    "count": len(collection_names),
                    "collections": collection_names
                }
                print(f"   ✅ Sucesso: {len(collection_names)} coleções encontradas")

            except Exception as e:
                results["test_operations"]["list_collections"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"   ❌ Erro: {e}")

            # Teste 2: Criar documento de teste
            print("\n2️⃣ Teste: Criar documento de teste")
            try:
                test_doc_ref = self.db.collection('debug_test').document('connection_test')
                test_data = {
                    'timestamp': datetime.now(),
                    'test': True,
                    'message': 'Connection test successful'
                }
                test_doc_ref.set(test_data)

                results["test_operations"]["create_document"] = {
                    "status": "success",
                    "document_id": "connection_test"
                }
                print("   ✅ Sucesso: Documento de teste criado")

            except Exception as e:
                results["test_operations"]["create_document"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"   ❌ Erro: {e}")

            # Teste 3: Ler documento de teste
            print("\n3️⃣ Teste: Ler documento de teste")
            try:
                test_doc_ref = self.db.collection('debug_test').document('connection_test')
                doc = test_doc_ref.get()

                if doc.exists:
                    results["test_operations"]["read_document"] = {
                        "status": "success",
                        "data": doc.to_dict()
                    }
                    print("   ✅ Sucesso: Documento lido com sucesso")
                else:
                    results["test_operations"]["read_document"] = {
                        "status": "not_found",
                        "message": "Document does not exist"
                    }
                    print("   ⚠️  Documento não encontrado")

            except Exception as e:
                results["test_operations"]["read_document"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"   ❌ Erro: {e}")

            # Teste 4: Deletar documento de teste
            print("\n4️⃣ Teste: Deletar documento de teste")
            try:
                test_doc_ref = self.db.collection('debug_test').document('connection_test')
                test_doc_ref.delete()

                results["test_operations"]["delete_document"] = {
                    "status": "success"
                }
                print("   ✅ Sucesso: Documento de teste removido")

            except Exception as e:
                results["test_operations"]["delete_document"] = {
                    "status": "error",
                    "error": str(e)
                }
                print(f"   ❌ Erro: {e}")

            # Determina status geral da conexão
            successful_tests = sum(1 for test in results["test_operations"].values()
                                 if test.get("status") == "success")
            total_tests = len(results["test_operations"])

            if successful_tests == total_tests:
                results["connection_status"] = "excellent"
                print(f"\n✅ Status da conexão: EXCELENTE ({successful_tests}/{total_tests} testes passaram)")
            elif successful_tests >= total_tests * 0.75:
                results["connection_status"] = "good"
                print(f"\n✅ Status da conexão: BOM ({successful_tests}/{total_tests} testes passaram)")
            elif successful_tests > 0:
                results["connection_status"] = "partial"
                print(f"\n⚠️  Status da conexão: PARCIAL ({successful_tests}/{total_tests} testes passaram)")
            else:
                results["connection_status"] = "failed"
                print(f"\n❌ Status da conexão: FALHOU ({successful_tests}/{total_tests} testes passaram)")

            return results

        except Exception as e:
            results["connection_status"] = "error"
            results["error"] = str(e)
            print(f"❌ Erro geral no teste de conexão: {e}")
            return results

    async def list_collections(self) -> dict[str, Any]:
        """
        Lista e analisa as coleções disponíveis.
        Baseado em debug_firestore_collections.py
        """
        print("\n" + "="*60)
        print("🔍 ANÁLISE DAS COLEÇÕES FIRESTORE")
        print("="*60)

        results = {
            "collections": {},
            "summary": {}
        }

        try:
            # Lista todas as coleções
            collections = self.db.collections()
            collection_names = []

            for collection in collections:
                collection_names.append(collection.id)

            print(f"📊 Total de coleções encontradas: {len(collection_names)}")

            if not collection_names:
                print("⚠️  Nenhuma coleção encontrada no banco de dados")
                results["summary"]["total_collections"] = 0
                return results

            # Analisa cada coleção
            total_documents = 0

            for collection_name in sorted(collection_names):
                print(f"\n📁 Analisando coleção: {collection_name}")

                try:
                    collection_ref = self.db.collection(collection_name)

                    # Conta documentos na coleção
                    docs = collection_ref.stream()
                    doc_count = 0
                    sample_fields = set()

                    for doc in docs:
                        doc_count += 1
                        doc_data = doc.to_dict()
                        if doc_data:
                            sample_fields.update(doc_data.keys())

                        # Limita a análise para performance
                        if doc_count >= 100:
                            break

                    total_documents += doc_count

                    results["collections"][collection_name] = {
                        "document_count": doc_count,
                        "sample_fields": list(sample_fields),
                        "field_count": len(sample_fields)
                    }

                    print(f"   • Documentos: {doc_count}")
                    print(f"   • Campos únicos (amostra): {len(sample_fields)}")
                    if sample_fields:
                        print(f"   • Exemplos de campos: {', '.join(list(sample_fields)[:5])}")

                except Exception as e:
                    results["collections"][collection_name] = {
                        "error": str(e)
                    }
                    print(f"   ❌ Erro ao analisar: {e}")

            # Resumo geral
            results["summary"] = {
                "total_collections": len(collection_names),
                "total_documents": total_documents,
                "collection_names": sorted(collection_names)
            }

            print("\n📋 RESUMO GERAL:")
            print(f"   • Total de coleções: {results['summary']['total_collections']}")
            print(f"   • Total de documentos: {results['summary']['total_documents']}")
            print(f"   • Coleções: {', '.join(results['summary']['collection_names'])}")

            return results

        except Exception as e:
            print(f"❌ Erro ao listar coleções: {e}")
            results["error"] = str(e)
            return results

    async def analyze_collection(self, collection_name: str) -> dict[str, Any]:
        """
        Analisa uma coleção específica em detalhes.
        Baseado em debug_firestore_raw_access.py
        """
        print("\n" + "="*60)
        print(f"🔍 ANÁLISE DETALHADA DA COLEÇÃO: {collection_name}")
        print("="*60)

        results = {
            "collection_name": collection_name,
            "analysis": {}
        }

        try:
            collection_ref = self.db.collection(collection_name)

            # Busca todos os documentos
            docs = collection_ref.stream()
            all_docs = []

            for doc in docs:
                doc_data = doc.to_dict()
                doc_data['_id'] = doc.id
                all_docs.append(doc_data)

            total_docs = len(all_docs)
            print(f"📊 Total de documentos: {total_docs}")

            if total_docs == 0:
                print(f"⚠️  Nenhum documento encontrado na coleção '{collection_name}'")
                results["analysis"]["total_documents"] = 0
                return results

            # Análise da estrutura
            all_fields = set()
            field_types = {}
            field_frequency = {}
            null_fields = {}
            empty_fields = {}

            for doc_data in all_docs:
                for field, value in doc_data.items():
                    all_fields.add(field)

                    # Frequência do campo
                    field_frequency[field] = field_frequency.get(field, 0) + 1

                    # Tipos de dados
                    value_type = type(value).__name__
                    if field not in field_types:
                        field_types[field] = {}
                    field_types[field][value_type] = field_types[field].get(value_type, 0) + 1

                    # Valores nulos ou vazios
                    if value is None:
                        null_fields[field] = null_fields.get(field, 0) + 1
                    elif value == '' or value == []:
                        empty_fields[field] = empty_fields.get(field, 0) + 1

            # Estatísticas dos campos
            results["analysis"] = {
                "total_documents": total_docs,
                "total_unique_fields": len(all_fields),
                "field_statistics": {},
                "data_quality": {
                    "null_fields": null_fields,
                    "empty_fields": empty_fields
                }
            }

            # Análise por campo
            for field in sorted(all_fields):
                frequency = field_frequency.get(field, 0)
                coverage = (frequency / total_docs) * 100

                results["analysis"]["field_statistics"][field] = {
                    "frequency": frequency,
                    "coverage_percentage": round(coverage, 2),
                    "data_types": field_types.get(field, {}),
                    "null_count": null_fields.get(field, 0),
                    "empty_count": empty_fields.get(field, 0)
                }

            # Relatório detalhado
            print("\n📋 ESTATÍSTICAS DOS CAMPOS:")
            print(f"   • Total de campos únicos: {len(all_fields)}")

            print("\n📊 COBERTURA DOS CAMPOS (Top 10):")
            sorted_fields = sorted(
                results["analysis"]["field_statistics"].items(),
                key=lambda x: x[1]["coverage_percentage"],
                reverse=True
            )

            for field, stats in sorted_fields[:10]:
                print(f"   • {field}: {stats['coverage_percentage']}% ({stats['frequency']}/{total_docs})")

            print("\n🔍 TIPOS DE DADOS (Campos principais):")
            for field, stats in sorted_fields[:5]:
                types_str = ", ".join([f"{t}({c})" for t, c in stats["data_types"].items()])
                print(f"   • {field}: {types_str}")

            # Problemas de qualidade de dados
            quality_issues = []

            for field, count in null_fields.items():
                if count > 0:
                    percentage = (count / total_docs) * 100
                    quality_issues.append(f"{field}: {count} nulos ({percentage:.1f}%)")

            for field, count in empty_fields.items():
                if count > 0:
                    percentage = (count / total_docs) * 100
                    quality_issues.append(f"{field}: {count} vazios ({percentage:.1f}%)")

            if quality_issues:
                print("\n⚠️  PROBLEMAS DE QUALIDADE DE DADOS:")
                for issue in quality_issues[:10]:  # Mostra apenas os primeiros 10
                    print(f"   • {issue}")
            else:
                print("\n✅ Nenhum problema de qualidade de dados detectado")

            # Amostra de documentos
            print("\n📄 AMOSTRA DE DOCUMENTOS (primeiros 3):")
            for i, doc in enumerate(all_docs[:3]):
                print(f"   {i+1}. ID: {doc.get('_id', 'N/A')}")
                # Mostra apenas alguns campos para não poluir a saída
                sample_fields = list(doc.keys())[:5]
                for field in sample_fields:
                    if field != '_id':
                        value = doc[field]
                        if isinstance(value, str) and len(value) > 50:
                            value = value[:50] + "..."
                        print(f"      {field}: {value}")
                print()

            return results

        except Exception as e:
            print(f"❌ Erro ao analisar coleção '{collection_name}': {e}")
            results["error"] = str(e)
            return results

    async def run_comprehensive_debug(self, mode: str = "all", collection: str | None = None):
        """Executa o debug completo baseado no modo especificado."""
        print("🚀 Iniciando Debug Consolidado do Firestore")
        print(f"📋 Modo selecionado: {mode}")
        if collection:
            print(f"📁 Coleção específica: {collection}")

        await self.initialize()

        results = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "collection": collection
        }

        if mode in ["all", "connection"]:
            results["connection_test"] = await self.test_connection()

        if mode in ["all", "collections"]:
            results["collections_analysis"] = await self.list_collections()

        if mode in ["all", "analyze"] and collection:
            results["collection_analysis"] = await self.analyze_collection(collection)
        elif mode == "analyze" and not collection:
            print("❌ Modo 'analyze' requer especificar uma coleção")
            print("Uso: python script.py analyze <nome_da_coleção>")
            return None

        print("\n" + "="*60)
        print("✅ DEBUG CONSOLIDADO DO FIRESTORE CONCLUÍDO")
        print("="*60)

        return results


async def main():
    """Função principal."""
    # Determina o modo de execução
    mode = "all"
    collection = None

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode not in ["connection", "collections", "analyze", "all"]:
            print(f"❌ Modo inválido: {mode}")
            print("Modos disponíveis: connection, collections, analyze, all")
            sys.exit(1)

    if len(sys.argv) > 2:
        collection = sys.argv[2]

    debugger = FirestoreDebugger()

    try:
        results = await debugger.run_comprehensive_debug(mode, collection)

        if results:
            # Salva os resultados em arquivo JSON
            output_file = f"debug_firestore_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n💾 Resultados salvos em: {output_file}")

    except Exception as e:
        print(f"❌ Erro durante a execução: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
