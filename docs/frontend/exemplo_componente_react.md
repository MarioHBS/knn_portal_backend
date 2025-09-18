# Exemplo de Componente React - Cadastro de Estudante

## Componente Principal

```jsx
import React, { useState, useEffect } from 'react';
import { validarFormularioEstudante, aplicarMascaraTelefone, aplicarMascaraCEP, inicializarCursos, buscarCursosDisponiveis } from './validacoes';
import { criarEstudante } from './api';

const CadastroEstudante = () => {
  const [formData, setFormData] = useState({
    nome: '',
    email: '',
    telefone: '',
    cep: '',
    curso: '',
    data_nascimento: '',
    nome_responsavel: ''
  });

  const [erros, setErros] = useState({});
  const [carregando, setCarregando] = useState(false);
  const [sucesso, setSucesso] = useState(false);
  const [cursosDisponiveis, setCursosDisponiveis] = useState([]);
  const [loadingCursos, setLoadingCursos] = useState(true);

  // Carregar cursos disponíveis ao montar o componente
  useEffect(() => {
    const carregarCursos = async () => {
      try {
        setLoadingCursos(true);
        await inicializarCursos();
        const cursos = await buscarCursosDisponiveis();
        setCursosDisponiveis(cursos);
      } catch (error) {
        console.error('Erro ao carregar cursos:', error);
        // Fallback para lista hardcoded se necessário
        setCursosDisponiveis([
          'Engenharia de Software',
          'Ciência da Computação',
          'Sistemas de Informação',
          'Análise e Desenvolvimento de Sistemas',
          'Tecnologia da Informação',
          'Engenharia da Computação',
          'Administração',
          'Contabilidade',
          'Marketing',
          'Recursos Humanos'
        ]);
      } finally {
        setLoadingCursos(false);
      }
    };
    
    carregarCursos();
  }, []);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    let valorFormatado = value;

    // Aplicar máscaras
    if (name === 'telefone') {
      valorFormatado = aplicarMascaraTelefone(value);
    } else if (name === 'cep') {
      valorFormatado = aplicarMascaraCEP(value);
    }

    setFormData(prev => ({
      ...prev,
      [name]: valorFormatado
    }));

    // Limpar erro do campo quando usuário começar a digitar
    if (erros[name]) {
      setErros(prev => {
        const novosErros = { ...prev };
        delete novosErros[name];
        return novosErros;
      });
    }
  };

  const calcularIdade = (dataNascimento) => {
    const hoje = new Date();
    const nascimento = new Date(dataNascimento);
    let idade = hoje.getFullYear() - nascimento.getFullYear();
    const mes = hoje.getMonth() - nascimento.getMonth();
    
    if (mes < 0 || (mes === 0 && hoje.getDate() < nascimento.getDate())) {
      idade--;
    }
    
    return idade;
  };

  const isMenorIdade = formData.data_nascimento ? calcularIdade(formData.data_nascimento) < 18 : false;

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Validar formulário
    const validacao = validarFormularioEstudante(formData);
    
    if (!validacao.valido) {
      setErros(validacao.erros);
      return;
    }

    setCarregando(true);
    setErros({});

    try {
      const estudanteCriado = await criarEstudante(formData);
      console.log('Estudante criado:', estudanteCriado);
      setSucesso(true);
      
      // Limpar formulário após sucesso
      setTimeout(() => {
        setFormData({
          nome: '',
          email: '',
          telefone: '',
          cep: '',
          curso: '',
          data_nascimento: '',
          nome_responsavel: ''
        });
        setSucesso(false);
      }, 3000);
      
    } catch (error) {
      console.error('Erro ao criar estudante:', error);
      
      if (error.response?.data?.details) {
        // Erros de validação da API
        const errosAPI = {};
        error.response.data.details.forEach(erro => {
          errosAPI[erro.field] = erro.message;
        });
        setErros(errosAPI);
      } else {
        setErros({ geral: 'Erro interno do servidor. Tente novamente.' });
      }
    } finally {
      setCarregando(false);
    }
  };

  return (
    <div className="cadastro-estudante">
      <h2>Cadastro de Estudante</h2>
      
      {sucesso && (
        <div className="alert alert-success">
          ✅ Estudante cadastrado com sucesso!
        </div>
      )}
      
      {erros.geral && (
        <div className="alert alert-error">
          ❌ {erros.geral}
        </div>
      )}

      <form onSubmit={handleSubmit} className="form">
        {/* Nome */}
        <div className="form-group">
          <label htmlFor="nome">Nome Completo *</label>
          <input
            type="text"
            id="nome"
            name="nome"
            value={formData.nome}
            onChange={handleInputChange}
            className={erros.nome ? 'input-error' : ''}
            placeholder="Digite o nome completo"
            maxLength={100}
          />
          {erros.nome && <span className="error-message">{erros.nome}</span>}
        </div>

        {/* Email */}
        <div className="form-group">
          <label htmlFor="email">Email</label>
          <input
            type="email"
            id="email"
            name="email"
            value={formData.email}
            onChange={handleInputChange}
            className={erros.email ? 'input-error' : ''}
            placeholder="exemplo@email.com"
          />
          {erros.email && <span className="error-message">{erros.email}</span>}
        </div>

        {/* Telefone */}
        <div className="form-group">
          <label htmlFor="telefone">Telefone</label>
          <input
            type="text"
            id="telefone"
            name="telefone"
            value={formData.telefone}
            onChange={handleInputChange}
            className={erros.telefone ? 'input-error' : ''}
            placeholder="(11) 99999-9999"
            maxLength={15}
          />
          {erros.telefone && <span className="error-message">{erros.telefone}</span>}
        </div>

        {/* CEP */}
        <div className="form-group">
          <label htmlFor="cep">CEP *</label>
          <input
            type="text"
            id="cep"
            name="cep"
            value={formData.cep}
            onChange={handleInputChange}
            className={erros.cep ? 'input-error' : ''}
            placeholder="12345-678"
            maxLength={9}
          />
          {erros.cep && <span className="error-message">{erros.cep}</span>}
        </div>

        {/* Curso */}
        <div className="form-group">
          <label htmlFor="curso">Curso *</label>
          <select
            id="curso"
            name="curso"
            value={formData.curso}
            onChange={handleInputChange}
            className={erros.curso ? 'input-error' : ''}
            disabled={loadingCursos}
          >
            <option value="">
              {loadingCursos ? 'Carregando cursos...' : 'Selecione um curso'}
            </option>
            {cursosDisponiveis.map(curso => (
              <option key={curso} value={curso}>{curso}</option>
            ))}
          </select>
          {erros.curso && <span className="error-message">{erros.curso}</span>}
        </div>

        {/* Data de Nascimento */}
        <div className="form-group">
          <label htmlFor="data_nascimento">Data de Nascimento *</label>
          <input
            type="date"
            id="data_nascimento"
            name="data_nascimento"
            value={formData.data_nascimento}
            onChange={handleInputChange}
            className={erros.data_nascimento ? 'input-error' : ''}
            max={new Date().toISOString().split('T')[0]}
          />
          {erros.data_nascimento && <span className="error-message">{erros.data_nascimento}</span>}
        </div>

        {/* Nome do Responsável (condicional) */}
        {isMenorIdade && (
          <div className="form-group">
            <label htmlFor="nome_responsavel">Nome do Responsável *</label>
            <input
              type="text"
              id="nome_responsavel"
              name="nome_responsavel"
              value={formData.nome_responsavel}
              onChange={handleInputChange}
              className={erros.nome_responsavel ? 'input-error' : ''}
              placeholder="Nome completo do responsável"
              maxLength={100}
            />
            {erros.nome_responsavel && <span className="error-message">{erros.nome_responsavel}</span>}
            <small className="help-text">Obrigatório para menores de 18 anos</small>
          </div>
        )}

        {/* Botão Submit */}
        <div className="form-actions">
          <button 
            type="submit" 
            disabled={carregando}
            className="btn btn-primary"
          >
            {carregando ? 'Cadastrando...' : 'Cadastrar Estudante'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default CadastroEstudante;
`$language

## Arquivo de API (api.js)

```javascript
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Função para obter token JWT (implementar conforme sua autenticação)
const getAuthToken = () => {
  return localStorage.getItem('authToken');
};

// Função para obter tenant ID
const getTenantId = () => {
  return localStorage.getItem('tenantId');
};

// Configuração padrão para requisições
const getHeaders = () => ({
  'Content-Type': 'application/json',
  'Authorization': `Bearer ${getAuthToken()}`,
  'X-Tenant-ID': getTenantId()
});

// Função para criar estudante
export const criarEstudante = async (dadosEstudante) => {
  const response = await fetch(`${API_BASE_URL}/students`, {
    method: 'POST',
    headers: getHeaders(),
    body: JSON.stringify(dadosEstudante)
  });

  if (!response.ok) {
    const errorData = await response.json();
    const error = new Error('Erro na API');
    error.response = { data: errorData };
    throw error;
  }

  return response.json();
};

// Função para listar estudantes
export const listarEstudantes = async (page = 1, limit = 20, search = '') => {
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    ...(search && { search })
  });

  const response = await fetch(`${API_BASE_URL}/students?${params}`, {
    method: 'GET',
    headers: getHeaders()
  });

  if (!response.ok) {
    throw new Error('Erro ao carregar estudantes');
  }

  return response.json();
};

// Função para buscar estudante por ID
export const buscarEstudantePorId = async (id) => {
  const response = await fetch(`${API_BASE_URL}/students/${id}`, {
    method: 'GET',
    headers: getHeaders()
  });

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Estudante não encontrado');
    }
    throw new Error('Erro ao carregar estudante');
  }

  return response.json();
};
`$language

## Arquivo de Validações (validacoes.js)

```javascript
// Funções de validação (usar o conteúdo do arquivo validacoes_frontend.md)

export function validarNome(nome) {
  if (!nome || nome.trim().length < 2) {
    return 'Nome deve ter pelo menos 2 caracteres';
  }
  if (nome.length > 100) {
    return 'Nome deve ter no máximo 100 caracteres';
  }
  return null;
}

export function validarEmail(email) {
  if (!email) return null;
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(email)) {
    return 'Formato de email inválido';
  }
  return null;
}

export function aplicarMascaraTelefone(valor) {
  const apenasNumeros = valor.replace(/\D/g, '');
  
  if (apenasNumeros.length <= 10) {
    return apenasNumeros.replace(/(\d{2})(\d{4})(\d{4})/, '($1) $2-$3');
  } else {
    return apenasNumeros.replace(/(\d{2})(\d{5})(\d{4})/, '($1) $2-$3');
  }
}

export function aplicarMascaraCEP(valor) {
  const apenasNumeros = valor.replace(/\D/g, '');
  return apenasNumeros.replace(/(\d{5})(\d{3})/, '$1-$2');
}

// ... outras funções de validação

export function validarFormularioEstudante(dados) {
  const erros = {};
  
  const erroNome = validarNome(dados.nome);
  if (erroNome) erros.nome = erroNome;
  
  const erroEmail = validarEmail(dados.email);
  if (erroEmail) erros.email = erroEmail;
  
  // ... outras validações
  
  return {
    valido: Object.keys(erros).length === 0,
    erros
  };
}
`$language

## Estilos CSS (cadastro-estudante.css)

```css
.cadastro-estudante {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.cadastro-estudante h2 {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.alert {
  padding: 12px;
  border-radius: 4px;
  margin-bottom: 20px;
  font-weight: 500;
}

.alert-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.alert-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  font-weight: 600;
  margin-bottom: 4px;
  color: #333;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.input-error {
  border-color: #dc3545 !important;
  box-shadow: 0 0 0 2px rgba(220, 53, 69, 0.25) !important;
}

.error-message {
  color: #dc3545;
  font-size: 12px;
  margin-top: 4px;
}

.help-text {
  color: #6c757d;
  font-size: 12px;
  margin-top: 4px;
}

.form-actions {
  margin-top: 20px;
}

.btn {
  padding: 12px 24px;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsividade */
@media (max-width: 768px) {
  .cadastro-estudante {
    margin: 10px;
    padding: 15px;
  }
}
`$language

## Como Usar

1. **Instalar dependências:**

```bash
npm install
`$language

2. **Configurar variáveis de ambiente (.env):**

`$language
REACT_APP_API_URL=http://localhost:8000/api/v1
`$language

3. **Importar e usar o componente:**

```jsx
import CadastroEstudante from './components/CadastroEstudante';
import './components/cadastro-estudante.css';

function App() {
  return (
    <div className="App">
      <CadastroEstudante />
    </div>
  );
}
`$language

## Funcionalidades Implementadas

- ✅ **Validação em tempo real** dos campos
- ✅ **Máscaras automáticas** para telefone e CEP
- ✅ **Campo condicional** para responsável (menores de idade)
- ✅ **Tratamento de erros** da API
- ✅ **Feedback visual** de sucesso e erro
- ✅ **Loading state** durante requisições
- ✅ **Responsividade** para dispositivos móveis
- ✅ **Acessibilidade** com labels e IDs apropriados

## Próximos Passos

1. Implementar componentes similares para Funcionários e Parceiros
2. Adicionar testes unitários com Jest/React Testing Library
3. Implementar sistema de notificações toast
4. Adicionar upload de foto do estudante
5. Implementar busca de CEP automática via API
