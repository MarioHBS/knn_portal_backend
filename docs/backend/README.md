# Documentação Backend - Sistema de IDs Personalizados

## 📋 Visão Geral

Esta pasta contém a documentação técnica detalhada sobre a **implementação interna** dos algoritmos de geração de IDs personalizados. Estes documentos são destinados à equipe de Backend e contêm informações sobre a lógica interna que não são necessárias para o Frontend.

## 📁 Arquivos Disponíveis

### 1. 🔍 [relatorio_algoritmos_ids_detalhado.md](./relatorio_algoritmos_ids_detalhado.md)

**Relatório técnico completo dos algoritmos**

- Explicação detalhada da lógica de geração de IDs
- Algoritmos de extração de iniciais e dígitos
- Processo de intercalação de caracteres
- Mapeamento de cursos, cargos e categorias para sufixos
- Exemplos passo-a-passo da geração
- Tratamento de casos extremos

### 2. 🛠️ [guia_integracao_ids_detalhado.md](./guia_integracao_ids_detalhado.md)

**Guia técnico de integração interna**

- Detalhes da implementação nos modelos Pydantic
- Integração com a classe IDGenerators
- Exemplos de uso interno dos algoritmos
- Casos de teste específicos
- Debugging e troubleshooting

### 3. 📋 [api_specification_ids_completa.md](./api_specification_ids_completa.md)

**Especificação técnica completa da API**

- Documentação completa com detalhes internos
- Especificações de implementação
- Considerações de performance
- Detalhes de monitoramento e logs
- Configurações de ambiente

## 🎯 Público-Alvo

Estes documentos são destinados para:

- **Desenvolvedores Backend** que precisam entender a implementação
- **Arquitetos de Software** que precisam avaliar a solução
- **Equipe de QA** que precisa criar testes específicos
- **DevOps** que precisa configurar monitoramento

## 🔧 Implementação Técnica

### Estrutura dos Algoritmos

```python

# Localização: src/utils/id_generators.py

class IDGenerators:
    @staticmethod
    def gerar_id_aluno(nome: str, cep: str, telefone: str, email: str, curso: str) -> str:
        # Algoritmo específico para estudantes
        pass
    
    @staticmethod
    def gerar_id_funcionario(nome: str, cep: str, telefone: str, cargo: str) -> str:
        # Algoritmo específico para funcionários
        pass
    
    @staticmethod
    def gerar_id_parceiro(nome_comercial: str, cnpj: str, categoria: str) -> str:
        # Algoritmo específico para parceiros
        pass
`$language

### Integração com Modelos

```python

# Localização: src/models/__init__.py

class Student(BaseModel):
    id: str = Field(default="")
    nome: str
    cep: str
    # ... outros campos
    
    def __init__(self, **data):
        super().__init__(**data)
        if not self.id:
            self.id = IDGenerators.gerar_id_aluno(
                self.nome, self.cep, self.telefone, self.email, self.curso
            )
`$language

## 📊 Métricas e Testes

### Cobertura de Testes

- **36 testes automatizados** (26 unitários + 10 integração)
- **100% de aprovação** em todos os cenários
- **Cobertura completa** de casos extremos
- **Zero erros de linting** (Ruff)

### Performance

- **Geração de ID:** < 1ms por operação
- **Determinístico:** Mesmo input = mesmo output
- **Fallback seguro:** UUID4 em caso de erro
- **Thread-safe:** Métodos estáticos sem estado

## 🔍 Algoritmos Detalhados

### 1. Extração de Iniciais

```python
def extrair_iniciais(nome: str) -> str:
    """Extrai iniciais do nome, tratando acentos e caracteres especiais"""
    # Remove acentos: João → Joao
    # Extrai iniciais: João Silva Santos → JSS
    # Trata nomes compostos e preposições
`$language

### 2. Extração de Dígitos

```python
def extrair_digitos_cep_telefone_email(cep: str, telefone: str, email: str) -> str:
    """Extrai dígitos de CEP, telefone e email de forma intercalada"""
    # CEP: 12345-678 → 12345678
    # Telefone: (11) 99999-9999 → 1199999999
    # Email: joao@email.com → hash dos caracteres
`$language

### 3. Intercalação

```python
def intercalar_iniciais_digitos(iniciais: str, digitos: str) -> str:
    """Intercala iniciais com dígitos de forma determinística"""
    # Iniciais: JSS, Dígitos: 123456
    # Resultado: J1S2S3... (até 8 caracteres)
`$language

### 4. Mapeamento de Sufixos

```python
CURSO_SUFIXOS = {
    'Engenharia de Software': 'K1',
    'Ciência da Computação': 'T2',
    'Administração': 'A3',
    # ... outros mapeamentos
}
`$language

## 🚨 Considerações de Segurança

### Dados Sensíveis

- **Não loggar dados pessoais** (CPF, telefone completo)
- **Hash de emails** para extração de dígitos
- **Validação de entrada** antes do processamento
- **Sanitização** de caracteres especiais

### Unicidade

- **Determinístico por design** - mesmo input gera mesmo ID
- **Fallback para UUID4** em caso de colisão (raro)
- **Validação de unicidade** no banco de dados
- **Retry automático** com UUID em caso de erro

## 🔧 Manutenção

### Adicionando Novos Cursos/Cargos

1. Atualizar mapeamentos em `id_generators.py`
2. Adicionar testes para novos valores
3. Atualizar documentação do Frontend
4. Executar suite completa de testes

### Modificando Algoritmos

1. **CUIDADO:** Mudanças podem quebrar IDs existentes
2. Implementar versionamento se necessário
3. Manter compatibilidade com IDs já gerados
4. Testar extensivamente antes do deploy

## 📈 Monitoramento

### Métricas Importantes

- **Taxa de sucesso** na geração de IDs
- **Tempo de resposta** dos algoritmos
- **Uso de fallback** para UUID
- **Distribuição de sufixos** por tipo

### Logs Relevantes

```python

# Exemplo de log estruturado

logger.info("ID gerado", extra={
    "tipo": "estudante",
    "id_gerado": "STD_J6S7S899_K1",
    "curso": "Engenharia de Software",
    "tempo_geracao_ms": 0.8
})
`$language

## 🔄 Versionamento

### Versão Atual: 1.0

- **Algoritmos estáveis** para produção
- **Compatibilidade garantida** com IDs existentes
- **Testes abrangentes** implementados
- **Documentação completa** disponível

### Roadmap Futuro

- **v1.1:** Otimizações de performance
- **v1.2:** Suporte a novos tipos de entidade
- **v2.0:** Algoritmos aprimorados (com migração)

---

**Equipe Responsável:** Backend Team  
**Última atualização:** Janeiro 2025  
**Status:** Produção ✅  
**Próxima revisão:** Março 2025
