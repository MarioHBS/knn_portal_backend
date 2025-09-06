# Scripts de Manipulação de Imagens

Esta pasta contém todos os scripts relacionados ao processamento e gerenciamento de imagens de parceiros.

## Scripts Disponíveis

### analyze_partner_images.py

- **Função**: Analisa as imagens de parceiros na pasta `partners_images`
- **Verifica**: Dimensões, formato, transparência e outras especificações
- **Saída**: Relatório detalhado das imagens encontradas

### process_partner_images.py

- **Função**: Processa imagens de parceiros aplicando padronizações
- **Operações**:
  - Redimensiona para 200x200px mantendo proporção
  - Adiciona fundo transparente
  - Converte para PNG com transparência
  - Preserva qualidade da imagem
- **Entrada**: `data/firestore_export/partners_images/`
- **Saída**: `statics/logos/processed/`

### upload_partner_images.py

- **Função**: Faz upload das imagens processadas para Firebase Storage
- **Operações**:
  - Upload para bucket Firebase
  - Atualização das URLs no Firestore
  - Geração de relatórios de upload
- **Dependências**: Firebase Admin SDK configurado

### test_image_references.py

- **Função**: Testa se as referências de imagem estão funcionando
- **Verifica**:
  - Acessibilidade das URLs das imagens
  - Dados atualizados no Firestore
  - Integridade das referências

## Fluxo de Trabalho

1. **Análise**: Execute `analyze_partner_images.py` para verificar as imagens originais
2. **Processamento**: Execute `process_partner_images.py` para padronizar as imagens
3. **Upload**: Execute `upload_partner_images.py` para enviar ao Firebase Storage
4. **Validação**: Execute `test_image_references.py` para verificar se tudo está funcionando

## Configuração

Certifique-se de que:

- Firebase Admin SDK está configurado
- Credenciais do Firebase estão no arquivo `.env`
- Pasta de imagens originais existe: `data/firestore_export/partners_images/`
- Pasta de saída existe: `statics/logos/processed/`

## Relatórios

Todos os scripts geram relatórios detalhados salvos na pasta `docs/` com timestamp para controle de versão.
