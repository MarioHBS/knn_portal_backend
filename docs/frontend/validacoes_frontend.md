# Validações Frontend - Portal de Benefícios KNN

## Visão Geral

Este documento contém as validações que devem ser implementadas no Frontend antes de enviar dados para a API.

## Validações por Campo

### 1. Campos Comuns

#### Nome / Nome Comercial

```javascript
function validarNome(nome) {
  if (!nome || nome.trim().length < 2) {
    return 'Nome deve ter pelo menos 2 caracteres';
  }
  if (nome.length > 100) {
    return 'Nome deve ter no máximo 100 caracteres';
  }
  return null;
}
```

#### Email

```javascript
function validarEmail(email) {
  if (!email) return null; // Campo opcional
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return 'Formato de email inválido';
  }
  return null;
}
```

#### Telefone

```javascript
function validarTelefone(telefone) {
  if (!telefone) return null; // Campo opcional
  
  // Remove caracteres não numéricos
  const apenasNumeros = telefone.replace(/\D/g, '');
  
  if (apenasNumeros.length !== 10 && apenasNumeros.length !== 11) {
    return 'Telefone deve ter 10 ou 11 dígitos';
  }
  
  // Formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
  const telefoneRegex = /^\(\d{2}\)\s\d{4,5}-\d{4}$/;
  if (!telefoneRegex.test(telefone)) {
    return 'Formato: (XX) XXXXX-XXXX ou (XX) XXXX-XXXX';
  }
  
  return null;
}
```

#### CEP

```javascript
function validarCEP(cep) {
  if (!cep) {
    return 'CEP é obrigatório';
  }
  
  const cepRegex = /^\d{5}-\d{3}$/;
  if (!cepRegex.test(cep)) {
    return 'CEP deve seguir o formato XXXXX-XXX';
  }
  
  return null;
}
```

#### Data de Nascimento

```javascript
function validarDataNascimento(data) {
  if (!data) {
    return 'Data de nascimento é obrigatória';
  }
  
  const dataObj = new Date(data);
  const hoje = new Date();
  
  if (dataObj > hoje) {
    return 'Data de nascimento não pode ser futura';
  }
  
  const idade = hoje.getFullYear() - dataObj.getFullYear();
  if (idade > 120) {
    return 'Data de nascimento inválida';
  }
  
  return null;
}
```

### 2. Validações Específicas - Estudantes

#### Curso

```javascript
// Lista de cursos como fallback (caso a API não esteja disponível)
const cursosValidosFallback = [
  'KIDS 1',
  'KIDS 2',
  'KIDS 3',
  'SEEDS 1',
  'SEEDS 2',
  'SEEDS 3',
  'TEENS 1',
  'TEENS 2',
  'TEENS 3',
  'TWEENS 1',
  'TWEENS 2',
  'TWEENS 3',
  'KEEP_TALKING 1',
  'KEEP_TALKING 2',
  'KEEP_TALKING 3',
  'ADVANCED 1',
  'ADVANCED 2',
  'KINDER'
];

// Função para buscar cursos da API
async function buscarCursosDisponiveis() {
  try {
    const response = await fetch(`${API_BASE_URL}/utils/courses`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAuthToken()}`
      }
    });
    
    if (response.ok) {
      const cursos = await response.json();
      return cursos;
    } else {
      console.warn('Erro ao buscar cursos da API, usando lista fallback');
      return cursosValidosFallback;
    }
  } catch (error) {
    console.error('Erro ao conectar com a API de cursos:', error);
    return cursosValidosFallback;
  }
}

// Variável global para armazenar cursos (será populada dinamicamente)
let cursosValidos = cursosValidosFallback;

function validarCurso(curso) {
  if (!curso) {
    return 'Curso é obrigatório';
  }
  
  if (!cursosValidos.includes(curso)) {
    return 'Curso não encontrado na lista de cursos válidos';
  }
  
  return null;
}

// Função para inicializar cursos (deve ser chamada no início da aplicação)
async function inicializarCursos() {
  cursosValidos = await buscarCursosDisponiveis();
  console.log('Cursos carregados:', cursosValidos.length);
}
```

#### Nome do Responsável (para menores de idade)
```javascript
function validarNomeResponsavel(nomeResponsavel, dataNascimento) {
  const idade = calcularIdade(dataNascimento);
  
  if (idade < 18) {
    if (!nomeResponsavel || nomeResponsavel.trim().length < 2) {
      return 'Nome do responsável é obrigatório para menores de idade';
    }
    if (nomeResponsavel.length > 100) {
      return 'Nome do responsável deve ter no máximo 100 caracteres';
    }
  }
  
  return null;
}

function calcularIdade(dataNascimento) {
  const hoje = new Date();
  const nascimento = new Date(dataNascimento);
  let idade = hoje.getFullYear() - nascimento.getFullYear();
  const mes = hoje.getMonth() - nascimento.getMonth();
  
  if (mes < 0 || (mes === 0 && hoje.getDate() < nascimento.getDate())) {
    idade--;
  }
  
  return idade;
}
```

### 3. Validações Específicas - Funcionários

#### Cargo
```javascript
const cargosValidos = [
  'Professor',
  'Coordenador',
  'Diretor',
  'Assistente Financeiro',
  'Secretário',
  'Bibliotecário',
  'Técnico em Informática',
  'Auxiliar Administrativo',
  'Gerente',
  'Supervisor'
];

function validarCargo(cargo) {
  if (!cargo) {
    return 'Cargo é obrigatório';
  }
  
  if (!cargosValidos.includes(cargo)) {
    return 'Cargo não encontrado na lista de cargos válidos';
  }
  
  return null;
}
```

### 4. Validações Específicas - Parceiros

#### CNPJ
```javascript
function validarCNPJ(cnpj) {
  if (!cnpj) {
    return 'CNPJ é obrigatório';
  }
  
  // Remove caracteres não numéricos
  const apenasNumeros = cnpj.replace(/\D/g, '');
  
  if (apenasNumeros.length !== 14) {
    return 'CNPJ deve ter 14 dígitos';
  }
  
  // Formato: XX.XXX.XXX/XXXX-XX
  const cnpjRegex = /^\d{2}\.\d{3}\.\d{3}\/\d{4}-\d{2}$/;
  if (!cnpjRegex.test(cnpj)) {
    return 'CNPJ deve seguir o formato XX.XXX.XXX/XXXX-XX';
  }
  
  // Validação dos dígitos verificadores
  if (!validarDigitosCNPJ(apenasNumeros)) {
    return 'CNPJ inválido';
  }
  
  return null;
}

function validarDigitosCNPJ(cnpj) {
  // Implementação da validação dos dígitos verificadores do CNPJ
  const pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  
  let soma1 = 0;
  for (let i = 0; i < 12; i++) {
    soma1 += parseInt(cnpj[i]) * pesos1[i];
  }
  
  let digito1 = soma1 % 11;
  digito1 = digito1 < 2 ? 0 : 11 - digito1;
  
  if (parseInt(cnpj[12]) !== digito1) {
    return false;
  }
  
  let soma2 = 0;
  for (let i = 0; i < 13; i++) {
    soma2 += parseInt(cnpj[i]) * pesos2[i];
  }
  
  let digito2 = soma2 % 11;
  digito2 = digito2 < 2 ? 0 : 11 - digito2;
  
  return parseInt(cnpj[13]) === digito2;
}
```

#### Categoria
```javascript
const categoriasValidas = [
  'Tecnologia',
  'Saúde',
  'Educação',
  'Alimentação',
  'Transporte',
  'Lazer',
  'Esportes',
  'Cultura',
  'Serviços',
  'Comércio'
];

function validarCategoria(categoria) {
  if (!categoria) {
    return 'Categoria é obrigatória';
  }
  
  if (!categoriasValidas.includes(categoria)) {
    return 'Categoria não encontrada na lista de categorias válidas';
  }
  
  return null;
}
```

## Máscaras de Entrada

### Telefone
```javascript
function aplicarMascaraTelefone(valor) {
  const apenasNumeros = valor.replace(/\D/g, '');
  
  if (apenasNumeros.length <= 10) {
    return apenasNumeros.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  } else {
    return apenasNumeros.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
}
```

### CEP
```javascript
function aplicarMascaraCEP(valor) {
  const apenasNumeros = valor.replace(/\D/g, '');
  return apenasNumeros.replace(/(\d{5})(\d{3})/, '$1-$2');
}
```

### CNPJ
```javascript
function aplicarMascaraCNPJ(valor) {
  const apenasNumeros = valor.replace(/\D/g, '');
  return apenasNumeros.replace(/(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})/, '$1.$2.$3/$4-$5');
}
```

## Validação Completa do Formulário

### Estudante
```javascript
function validarFormularioEstudante(dados) {
  const erros = {};
  
  const erroNome = validarNome(dados.nome);
  if (erroNome) erros.nome = erroNome;
  
  const erroEmail = validarEmail(dados.email);
  if (erroEmail) erros.email = erroEmail;
  
  const erroTelefone = validarTelefone(dados.telefone);
  if (erroTelefone) erros.telefone = erroTelefone;
  
  const erroCEP = validarCEP(dados.cep);
  if (erroCEP) erros.cep = erroCEP;
  
  const erroCurso = validarCurso(dados.curso);
  if (erroCurso) erros.curso = erroCurso;
  
  const erroDataNascimento = validarDataNascimento(dados.data_nascimento);
  if (erroDataNascimento) erros.data_nascimento = erroDataNascimento;
  
  const erroResponsavel = validarNomeResponsavel(dados.nome_responsavel, dados.data_nascimento);
  if (erroResponsavel) erros.nome_responsavel = erroResponsavel;
  
  return {
    valido: Object.keys(erros).length === 0,
    erros
  };
}
```

### Funcionário
```javascript
function validarFormularioFuncionario(dados) {
  const erros = {};
  
  const erroNome = validarNome(dados.nome);
  if (erroNome) erros.nome = erroNome;
  
  const erroEmail = validarEmail(dados.email);
  if (erroEmail) erros.email = erroEmail;
  
  const erroTelefone = validarTelefone(dados.telefone);
  if (erroTelefone) erros.telefone = erroTelefone;
  
  const erroCEP = validarCEP(dados.cep);
  if (erroCEP) erros.cep = erroCEP;
  
  const erroCargo = validarCargo(dados.cargo);
  if (erroCargo) erros.cargo = erroCargo;
  
  const erroDataNascimento = validarDataNascimento(dados.data_nascimento);
  if (erroDataNascimento) erros.data_nascimento = erroDataNascimento;
  
  return {
    valido: Object.keys(erros).length === 0,
    erros
  };
}
```

### Parceiro
```javascript
function validarFormularioParceiro(dados) {
  const erros = {};
  
  const erroNome = validarNome(dados.nome_comercial);
  if (erroNome) erros.nome_comercial = erroNome;
  
  const erroCNPJ = validarCNPJ(dados.cnpj);
  if (erroCNPJ) erros.cnpj = erroCNPJ;
  
  const erroCategoria = validarCategoria(dados.categoria);
  if (erroCategoria) erros.categoria = erroCategoria;
  
  const erroEmail = validarEmail(dados.email);
  if (erroEmail) erros.email = erroEmail;
  
  const erroTelefone = validarTelefone(dados.telefone);
  if (erroTelefone) erros.telefone = erroTelefone;
  
  return {
    valido: Object.keys(erros).length === 0,
    erros
  };
}
```

## Exemplo de Uso

```javascript
// Exemplo de validação antes de enviar para API
function enviarFormularioEstudante(dadosFormulario) {
  const validacao = validarFormularioEstudante(dadosFormulario);
  
  if (!validacao.valido) {
    // Exibir erros na interface
    exibirErrosValidacao(validacao.erros);
    return;
  }
  
  // Enviar para API
  fetch('/api/v1/students', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      'X-Tenant-ID': schoolId
    },
    body: JSON.stringify(dadosFormulario)
  })
  .then(response => {
    if (!response.ok) {
      throw new Error('Erro na API');
    }
    return response.json();
  })
  .then(data => {
    console.log('Estudante criado:', data);
    // Redirecionar ou exibir sucesso
  })
  .catch(error => {
    console.error('Erro:', error);
    // Tratar erro da API
  });
}
```

## Observações Importantes

1. **Valide sempre no Frontend** antes de enviar para a API
2. **Use máscaras de entrada** para melhorar a experiência do usuário
3. **Exiba mensagens de erro claras** para cada campo
4. **Trate erros da API** adequadamente
5. **Mantenha as listas de valores válidos** atualizadas
6. **Teste todas as validações** com dados diversos