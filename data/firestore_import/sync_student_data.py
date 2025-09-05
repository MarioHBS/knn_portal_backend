#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para sincronizar dados de alunos removendo registros extras do firestore_export.json
"""

import json
import re
from pathlib import Path

def load_dados_alunos_ids(dados_path):
    """Carrega IDs válidos do dados_alunos.json"""
    with open(dados_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return set(data['students'].keys())

def sync_firestore_data(firestore_path, valid_ids):
    """Remove alunos extras do firestore_export.json"""
    with open(firestore_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Encontra todos os blocos de alunos
    pattern = r'"__collection__/students/(STD_[^"]+)":\s*\{[^}]*"data":\s*\{(?:[^{}]*\{[^}]*\})*[^}]*\}[^}]*\}'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    print(f"Encontrados {len(matches)} blocos de alunos no firestore_export.json")
    
    # Lista para armazenar os blocos que devem ser removidos
    blocks_to_remove = []
    
    for match in matches:
        student_id = match.group(1)
        if student_id not in valid_ids:
            blocks_to_remove.append((match.start(), match.end(), student_id))
    
    print(f"Identificados {len(blocks_to_remove)} alunos para remoção")
    
    # Remove os blocos em ordem reversa para não afetar os índices
    new_content = content
    for start, end, student_id in reversed(blocks_to_remove):
        print(f"Removendo aluno: {student_id}")
        # Remove o bloco e a vírgula anterior se existir
        before = new_content[:start].rstrip()
        after = new_content[end:]
        
        # Se há uma vírgula antes do bloco, remove ela
        if before.endswith(','):
            before = before[:-1]
        
        # Se o próximo caractere é uma vírgula, remove ela
        if after.lstrip().startswith(','):
            after = after.lstrip()[1:]
        
        new_content = before + after
    
    return new_content, len(blocks_to_remove)

def main():
    # Caminhos dos arquivos
    firestore_path = Path("P:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/data/firestore_export.json")
    dados_path = Path("P:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/sources/dados_alunos.json")
    backup_path = Path("P:/ProjectsWEB/PRODUCAO/KNN PROJECT/knn_portal_journey_club_backend/data/firestore_export_backup.json")
    
    print("Carregando IDs válidos do dados_alunos.json...")
    valid_ids = load_dados_alunos_ids(dados_path)
    print(f"Total de IDs válidos: {len(valid_ids)}")
    
    print("\nCriando backup do firestore_export.json...")
    with open(firestore_path, 'r', encoding='utf-8') as f:
        original_content = f.read()
    
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    print(f"Backup criado: {backup_path}")
    
    print("\nSincronizando dados...")
    new_content, removed_count = sync_firestore_data(firestore_path, valid_ids)
    
    print("\nSalvando arquivo sincronizado...")
    with open(firestore_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"\n✅ Sincronização concluída!")
    print(f"Alunos removidos: {removed_count}")
    print(f"Backup salvo em: {backup_path}")
    
    # Verificação final
    print("\nVerificação final...")
    with open(firestore_path, 'r', encoding='utf-8') as f:
        final_content = f.read()
    
    final_pattern = r'"__collection__/students/(STD_[^"]+)"'
    final_matches = re.findall(final_pattern, final_content)
    print(f"Alunos restantes no firestore_export.json: {len(final_matches)}")
    
    if len(final_matches) == len(valid_ids):
        print("✅ Sincronização bem-sucedida!")
    else:
        print("❌ Erro na sincronização. Verifique o arquivo.")

if __name__ == "__main__":
    main()