# Gestão de Imagens - KNN Portal Journey Club

## 📋 Visão Geral

Este documento descreve a estrutura e processo implementado para gestão de imagens de parceiros no projeto KNN Portal Journey Club, incluindo organização local e preparação para integração com Firebase Storage.

## 🗂️ Estrutura de Pastas

```text
knn_portal_journey_club_backend/
├── statics/                    # Recursos estáticos para desenvolvimento
│   └── logos/                  # Imagens de logotipos dos parceiros
│       ├── index.html         # Página de visualização dos logos
│       ├── PTN_A1E3018_AUT.png
│       ├── PTN_C0P4799_LIV.png
│       ├── PTN_C5C7628_TEC.png
│       ├── PTN_C8A3367_EDU.png
│       ├── PTN_E211033_EDU.png
│       └── PTN_M365611_EDU.png
├── src/
│   ├── config/
│   │   └── firebase_storage_config.py  # Configurações do Firebase Storage
│   └── utils/
│       └── image_utils.py              # Utilitários para processamento de imagens
├── scripts/temp/
│   └── analyze_and_organize_images.py  # Script de organização de imagens
├── storage.rules                       # Regras de segurança do Firebase Storage
└── firebase.json                       # Configuração do Firebase (atualizada)
```

## 🏷️ Padrão de Nomenclatura

As imagens seguem o padrão:
```
PTN_{ID_PARCEIRO}_{CATEGORIA}_{TIPO}.{EXTENSAO}
```

**Exemplo:** `PTN_A1E3018_AUT.png`
- `PTN`: Prefixo para Partner
- `A1E3018`: ID único do parceiro
- `AUT`: Categoria (AUT=Automotivo, EDU=Educação, TEC=Tecnologia, LIV=Livraria)
- `logo`: Tipo da imagem (logo, faixada, etc.)
- `png`: Extensão (preferencialmente PNG para transparência)

## 🔧 Configurações Implementadas

### Firebase Storage

#### Regras de Segurança (`storage.rules`)
- **Leitura**: Permitida para usuários autenticados
- **Escrita**: Apenas administradores
- **Validações**: Formato de imagem e tamanho máximo (5MB)
- **Estrutura de pastas**:
  - `/partners/{imageType}/{imageId}` - Imagens de parceiros
  - `/temp/` - Uploads temporários (24h)
  - `/public/` - Recursos públicos
  - `/backup/` - Backups (somente leitura)

#### Configuração do Firebase (`firebase.json`)
```json
{
  "storage": {
    "rules": "storage.rules"
  },
  "hosting": {
    "public": "statics",
    "headers": [
      {
        "source": "**/*.@(png|jpg|jpeg|webp|svg)",
        "headers": [{
          "key": "Cache-Control",
          "value": "public, max-age=31536000"
        }]
      }
    ]
  }
}
```

### Utilitários Python

#### `firebase_storage_config.py`
- Configurações centralizadas do Firebase Storage
- Definição de caminhos e regras
- Metadados padrão para uploads
- Funções auxiliares para URLs e categorização

#### `image_utils.py`
- Classe `ImageProcessor` para processamento de imagens
- Classe `FirebaseImageManager` para integração com Storage
- Validação de formatos e dimensões
- Upload com metadados automáticos
- Sincronização bidirecional
- Geração de relatórios

## 📊 Relatório de Organização

### Imagens Processadas
- **Total analisado**: 10 imagens
- **Logos organizados**: 6 imagens
- **Faixadas identificadas**: 4 imagens

### Categorias Identificadas
- **Educação (EDU)**: 3 logos
- **Automotivo (AUT)**: 1 logo
- **Tecnologia (TEC)**: 1 logo
- **Livraria/Papelaria (LIV)**: 1 logo

### Tamanhos das Imagens
- Variação entre 15KB e 891KB
- Formatos: PNG (recomendado para transparência)
- Dimensões variadas (necessário padronização futura)

## 🚀 Próximos Passos

### Implementação Imediata
1. **Padronização de Dimensões**
   - Instalar Pillow: `pip install Pillow`
   - Executar script de redimensionamento
   - Manter transparência em PNGs

2. **Integração Firebase**
   - Configurar credenciais do Firebase
   - Testar upload de imagens
   - Implementar sincronização automática

### Melhorias Futuras
1. **Processamento Automático**
   - Redimensionamento automático no upload
   - Otimização de tamanho de arquivo
   - Geração de múltiplas resoluções

2. **Interface de Gestão**
   - Dashboard para upload de imagens
   - Visualização de estatísticas
   - Gestão de metadados

3. **Otimizações**
   - Cache de imagens
   - CDN para distribuição
   - Compressão automática

## 🔍 Visualização Local

Para visualizar os logos organizados:
1. Abra `statics/logos/index.html` no navegador
2. Ou execute um servidor local:
   ```bash
   cd statics
   python -m http.server 8000
   ```
3. Acesse: `http://localhost:8000/logos/`

## 📝 Comandos Úteis

### Análise de Imagens
```bash
# Executar script de organização
python scripts/temp/analyze_and_organize_images.py

# Listar imagens por tamanho
Get-ChildItem "statics\logos" -File | Sort-Object Length -Descending

# Verificar dimensões (requer Pillow)
python -c "from PIL import Image; img=Image.open('statics/logos/PTN_A1E3018_AUT.png'); print(f'{img.size[0]}x{img.size[1]}')"
```

### Firebase
```bash
# Deploy das regras do Storage
firebase deploy --only storage

# Deploy do hosting
firebase deploy --only hosting

# Deploy completo
firebase deploy
```

## ⚠️ Considerações Importantes

1. **Segurança**
   - Credenciais do Firebase devem estar em `/credentials/`
   - Nunca commitar chaves de API
   - Usar variáveis de ambiente em produção

2. **Performance**
   - Imagens grandes impactam carregamento
   - Considerar WebP para melhor compressão
   - Implementar lazy loading

3. **Backup**
   - Manter backup local das imagens originais
   - Sincronização regular com Firebase
   - Versionamento de imagens importantes

## 📞 Suporte

Para dúvidas sobre a gestão de imagens:
- Consulte a documentação do Firebase Storage
- Verifique logs em `docs/relatorio_organizacao_imagens_*.md`
- Execute scripts de diagnóstico em `scripts/temp/`

---

**Última atualização**: 06/09/2025
**Versão**: 1.0
**Responsável**: Sistema de Gestão de Imagens KNN
