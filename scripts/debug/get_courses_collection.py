#!/usr/bin/env python3
"""
Script para investigar a estrutura da coleção 'courses' no Firestore.
Analisa todos os documentos para verificar a presença e o formato dos campos
esperados, como 'code', 'book', 'idiom' e 'sequence_order'.
"""

import sys
from pathlib import Path

from google.cloud import firestore

# Adicionar o diretório raiz do projeto ao Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.utils import logger  # noqa: E402


def investigate_courses_collection():
    """Investiga a estrutura da coleção 'courses'."""
    try:
        logger.info("🔍 Investigando a estrutura da coleção 'courses'...")

        # Inicializar cliente Firestore diretamente
        db = firestore.Client()

        # Acessar a coleção 'courses'
        courses_ref = db.collection("courses")

        # Listar todos os documentos na coleção
        docs = courses_ref.stream()
        doc_count = 0
        courses_data = {}
        idiom_count: dict[str, int] = {}
        problems: dict[str, list[str]] = {}

        logger.info("📋 Analisando todos os documentos da coleção 'courses'...")

        for doc in docs:
            doc_count += 1
            doc_data = doc.to_dict()
            doc_id = doc.id
            issues = []

            logger.info(f"\n📄 Documento #{doc_count}: {doc_id}")

            # Extrair informações dos campos esperados
            code = doc_data.get("code")
            book = doc_data.get("book")
            idiom = doc_data.get("idiom")
            sequence_order = doc_data.get("sequence_order")

            # Verificar campos e seus tipos
            if not code or not isinstance(code, str):
                issues.append(f"Campo 'code' ausente ou inválido (valor: {code})")
            if not book or not isinstance(book, str):
                issues.append(f"Campo 'book' ausente ou inválido (valor: {book})")
            if not idiom or not isinstance(idiom, str):
                issues.append(f"Campo 'idiom' ausente ou inválido (valor: {idiom})")
            else:
                # Contar cursos por idioma
                idiom_count[idiom] = idiom_count.get(idiom, 0) + 1

            if sequence_order is None or not isinstance(sequence_order, int):
                issues.append(
                    f"Campo 'sequence_order' ausente ou não é um inteiro (valor: {sequence_order})"
                )

            logger.info(f"   📚 Livro: {book or 'N/A'}")
            logger.info(f"   🏷️ Código: {code or 'N/A'}")
            logger.info(f"   🗣️ Idioma: {idiom or 'N/A'}")
            logger.info(
                f"   🔢 Ordem: {sequence_order if sequence_order is not None else 'N/A'}"
            )

            # Armazenar dados e problemas encontrados
            courses_data[doc_id] = {
                "code": code,
                "book": book,
                "idiom": idiom,
                "sequence_order": sequence_order,
                "all_fields": list(doc_data.keys()),
            }

            if issues:
                problems[doc_id] = issues
                logger.warning(f"   ⚠️ Problemas encontrados: {', '.join(issues)}")
            else:
                logger.info("   ✅ Documento parece estar em conformidade.")

        # Resumo final
        logger.info("\n📊 RESUMO DA INVESTIGAÇÃO:")
        logger.info(f"   📄 Total de documentos (cursos) analisados: {doc_count}")

        logger.info("\n🗣️ ANÁLISE POR IDIOMA:")
        if idiom_count:
            for lang, count in idiom_count.items():
                logger.info(f"   - {lang}: {count} cursos")
        else:
            logger.info("   - Nenhum idioma encontrado.")

        logger.info("\n🔍 VERIFICAÇÃO DE PROBLEMAS:")
        if problems:
            logger.warning(
                f"   🚨 Encontrados problemas em {len(problems)} documento(s):"
            )
            for doc_id, issues in problems.items():
                logger.warning(f"      - {doc_id}: {', '.join(issues)}")
        else:
            logger.info("   ✅ Nenhum problema estrutural detectado nos cursos!")

        logger.info("🏁 Investigação da coleção 'courses' concluída!")

        return {
            "total_documents": doc_count,
            "idiom_count": idiom_count,
            "problems": problems,
            "courses_data": courses_data,
        }

    except Exception as e:
        logger.error(f"❌ Erro durante a investigação da coleção 'courses': {str(e)}")
        raise


if __name__ == "__main__":
    results = investigate_courses_collection()
    print("\n🎯 RESULTADO FINAL DA ANÁLISE:")
    print(f"Total de cursos: {results['total_documents']}")
    print("Contagem por Idioma:")
    for lang, count in results["idiom_count"].items():
        print(f"  - {lang}: {count}")

    if results["problems"]:
        print(f"\nProblemas encontrados em {len(results['problems'])} cursos.")
    else:
        print("\nNenhum problema estrutural encontrado.")
