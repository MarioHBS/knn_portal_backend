#!/usr/bin/env python3
"""
Script para gerar automaticamente a documentação OpenAPI.

Este script extrai a documentação OpenAPI diretamente da aplicação FastAPI,
garantindo que esteja sempre sincronizada com a implementação atual.

Uso:
    python scripts/development/generate_openapi_docs.py
"""

import json
import sys
from pathlib import Path

import yaml

# Adicionar o diretório raiz ao path para importar a aplicação
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.main import app


def generate_openapi_json() -> dict:
    """
    Gera a documentação OpenAPI em formato JSON.

    Returns:
        Dicionário com a documentação OpenAPI
    """
    print("🔍 Extraindo documentação OpenAPI da aplicação FastAPI...")

    # Obter o schema OpenAPI da aplicação
    openapi_schema = app.openapi()

    print("✅ Documentação extraída com sucesso!")
    print(f"📊 Título: {openapi_schema.get('info', {}).get('title', 'N/A')}")
    print(f"📊 Versão: {openapi_schema.get('info', {}).get('version', 'N/A')}")
    print(f"📊 Endpoints encontrados: {len(openapi_schema.get('paths', {}))}")

    return openapi_schema


def save_openapi_json(schema: dict, output_path: Path) -> None:
    """
    Salva a documentação OpenAPI em formato JSON.

    Args:
        schema: Dicionário com a documentação OpenAPI
        output_path: Caminho para salvar o arquivo JSON
    """
    print(f"💾 Salvando documentação JSON em: {output_path}")

    # Criar diretório se não existir
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Salvar com formatação bonita
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)

    print("✅ Arquivo JSON salvo com sucesso!")


def save_openapi_yaml(schema: dict, output_path: Path) -> None:
    """
    Salva a documentação OpenAPI em formato YAML.

    Args:
        schema: Dicionário com a documentação OpenAPI
        output_path: Caminho para salvar o arquivo YAML
    """
    print(f"💾 Salvando documentação YAML em: {output_path}")

    # Criar diretório se não existir
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Salvar em formato YAML
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(schema, f, default_flow_style=False, allow_unicode=True, indent=2)

    print("✅ Arquivo YAML salvo com sucesso!")


def print_endpoints_summary(schema: dict) -> None:
    """
    Imprime um resumo dos endpoints encontrados.

    Args:
        schema: Dicionário com a documentação OpenAPI
    """
    print("\n📋 RESUMO DOS ENDPOINTS ENCONTRADOS:")
    print("=" * 50)

    paths = schema.get('paths', {})

    # Agrupar por tags
    endpoints_by_tag = {}

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                tags = details.get('tags', ['Sem categoria'])
                tag = tags[0] if tags else 'Sem categoria'

                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []

                endpoints_by_tag[tag].append({
                    'method': method.upper(),
                    'path': path,
                    'summary': details.get('summary', 'Sem descrição')
                })

    # Imprimir por categoria
    for tag, endpoints in sorted(endpoints_by_tag.items()):
        print(f"\n🏷️  {tag}:")
        for endpoint in sorted(endpoints, key=lambda x: x['path']):
            method_color = {
                'GET': '🟢',
                'POST': '🔵',
                'PUT': '🟡',
                'DELETE': '🔴',
                'PATCH': '🟠'
            }.get(endpoint['method'], '⚪')

            print(f"  {method_color} {endpoint['method']:<6} {endpoint['path']:<30} - {endpoint['summary']}")

    print(f"\n📊 Total de endpoints: {sum(len(endpoints) for endpoints in endpoints_by_tag.values())}")


def main():
    """Função principal do script."""
    print("🚀 GERADOR DE DOCUMENTAÇÃO OPENAPI")
    print("=" * 50)

    try:
        # Gerar documentação
        openapi_schema = generate_openapi_json()

        # Definir caminhos de saída
        project_root = Path(__file__).parent.parent.parent
        docs_dir = project_root / "docs" / "endpoints"

        json_path = docs_dir / "openapi_generated.json"
        yaml_path = docs_dir / "openapi_generated.yaml"

        # Salvar em ambos os formatos
        save_openapi_json(openapi_schema, json_path)
        save_openapi_yaml(openapi_schema, yaml_path)

        # Imprimir resumo
        print_endpoints_summary(openapi_schema)

        print("\n🎉 DOCUMENTAÇÃO GERADA COM SUCESSO!")
        print(f"📁 Arquivos salvos em: {docs_dir}")
        print(f"   • JSON: {json_path.name}")
        print(f"   • YAML: {yaml_path.name}")

        print("\n💡 PRÓXIMOS PASSOS:")
        print("   1. Revisar a documentação gerada")
        print("   2. Substituir o arquivo openapi.yaml atual se necessário")
        print("   3. Verificar se todos os endpoints estão documentados corretamente")

    except Exception as e:
        print(f"❌ Erro ao gerar documentação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
