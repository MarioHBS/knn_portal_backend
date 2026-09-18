#!/usr/bin/env python3
"""
Script para inspecionar a estrutura atual dos cursos no Firestore
e compará-la com o COURSES_MAP definido no código.
"""

import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

# Adicionar o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from models import COURSES_MAP  # noqa: E402


def inspect_courses_structure():
    """Inspeciona a estrutura dos cursos no Firestore."""
    try:
        # Inicializar Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": "knn-benefits"})

        db = firestore.client()
        print("✅ Firestore inicializado com sucesso")

        print("\n🔍 Inspecionando estrutura dos cursos no Firestore...")

        # Buscar todos os cursos
        courses_ref = db.collection("courses")
        courses = courses_ref.stream()

        courses_data = []
        for course in courses:
            course_data = course.to_dict()
            course_data["firestore_id"] = course.id
            courses_data.append(course_data)

        if not courses_data:
            print("❌ Nenhum curso encontrado no Firestore")
            return

        print(f"✅ Encontrados {len(courses_data)} cursos no Firestore")

        # Analisar estrutura
        print("\n📋 Estrutura atual dos cursos no Firestore:")
        for i, course in enumerate(courses_data[:3]):  # Mostrar apenas os primeiros 3
            print(f"\n   Curso {i+1}:")
            for key, value in course.items():
                print(f"     {key}: {value}")

        # Verificar campos presentes
        all_fields = set()
        for course in courses_data:
            all_fields.update(course.keys())

        print(f"\n🔍 Campos encontrados nos cursos: {sorted(all_fields)}")

        # Comparar com COURSES_MAP
        print("\n📊 Comparação com COURSES_MAP:")
        print(f"   COURSES_MAP tem {len(COURSES_MAP)} cursos")
        print(f"   Firestore tem {len(courses_data)} cursos")

        # Verificar se os cursos do COURSES_MAP estão no Firestore
        firestore_names = {course.get("name") for course in courses_data}
        courses_map_names = set(COURSES_MAP.keys())

        missing_in_firestore = courses_map_names - firestore_names
        extra_in_firestore = firestore_names - courses_map_names

        if missing_in_firestore:
            print(
                f"   ⚠️  Cursos no COURSES_MAP mas não no Firestore: {missing_in_firestore}"
            )

        if extra_in_firestore:
            print(
                f"   ⚠️  Cursos no Firestore mas não no COURSES_MAP: {extra_in_firestore}"
            )

        if not missing_in_firestore and not extra_in_firestore:
            print("   ✅ Todos os cursos estão sincronizados")

        # Verificar estrutura esperada
        expected_fields = {"code", "name"}
        print(f"\n🎯 Campos esperados: {expected_fields}")

        extra_fields = all_fields - expected_fields - {"firestore_id"}
        if extra_fields:
            print(f"   ⚠️  Campos extras encontrados: {extra_fields}")
            return extra_fields
        else:
            print("   ✅ Estrutura dos cursos está correta")
            return None

    except Exception as e:
        print(f"❌ Erro ao inspecionar cursos: {e}")
        raise


if __name__ == "__main__":
    extra_fields = inspect_courses_structure()
    if extra_fields:
        print(f"\n🔧 Campos extras que precisam ser removidos: {extra_fields}")
