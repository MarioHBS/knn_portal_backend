#!/usr/bin/env python3
"""
Script para remover campos extras dos cursos no Firestore,
mantendo apenas 'code' e 'name' conforme definido no COURSES_MAP.
"""

import sys
from pathlib import Path

import firebase_admin
from firebase_admin import credentials, firestore

# Adicionar o diretório src ao path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


def clean_courses_fields():
    """Remove campos extras dos cursos no Firestore."""
    try:
        # Inicializar Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred, {"projectId": "knn-benefits"})

        db = firestore.client()
        print("✅ Firestore inicializado com sucesso")

        print("\n🧹 Limpando campos extras dos cursos no Firestore...")

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

        print(f"📋 Encontrados {len(courses_data)} cursos para limpar")

        # Campos que devem ser mantidos
        allowed_fields = {"code", "name"}

        # Processar cada curso
        updated_count = 0
        for course in courses_data:
            firestore_id = course["firestore_id"]

            # Criar nova estrutura apenas com campos permitidos
            clean_course = {}
            for field in allowed_fields:
                if field in course:
                    clean_course[field] = course[field]

            # Verificar se há campos para remover
            current_fields = set(course.keys()) - {"firestore_id"}
            fields_to_remove = current_fields - allowed_fields

            if fields_to_remove:
                print(f"   🔧 Limpando curso {course.get('name', firestore_id)}:")
                print(f"      Removendo campos: {sorted(fields_to_remove)}")
                print(f"      Mantendo campos: {sorted(clean_course.keys())}")

                # Atualizar documento no Firestore
                course_doc_ref = courses_ref.document(firestore_id)
                course_doc_ref.set(clean_course)

                updated_count += 1
                print("      ✅ Curso atualizado")
            else:
                print(f"   ✅ Curso {course.get('name', firestore_id)} já está limpo")

        print(f"\n🎉 Limpeza concluída: {updated_count} cursos atualizados")

        # Verificar resultado final
        print("\n🔍 Verificando resultado final...")
        courses = courses_ref.stream()

        final_fields = set()
        for course in courses:
            course_data = course.to_dict()
            final_fields.update(course_data.keys())

        print(f"📊 Campos finais nos cursos: {sorted(final_fields)}")

        if final_fields == allowed_fields:
            print("✅ Todos os cursos agora têm apenas os campos esperados!")
        else:
            extra_fields = final_fields - allowed_fields
            if extra_fields:
                print(f"⚠️  Ainda existem campos extras: {extra_fields}")

    except Exception as e:
        print(f"❌ Erro ao limpar cursos: {e}")
        raise


if __name__ == "__main__":
    clean_courses_fields()
