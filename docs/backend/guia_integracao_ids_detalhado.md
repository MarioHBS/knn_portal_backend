# Guia Prático de Integração - IDs Personalizados Frontend

## Casos de Uso Práticos

### 1. Formulário de Cadastro de Aluno

```html
<!-- Exemplo de formulário HTML -->
<form id="studentForm">
  <div class="form-group">
    <label for="nome_aluno">Nome do Aluno *</label>
    <input type="text" id="nome_aluno" name="nome_aluno" required>
    <small class="form-text">Ex: João Silva Santos</small>
  </div>
  
  <div class="form-group">
    <label for="curso">Curso *</label>
    <select id="curso" name="curso" required>
      <option value="">Selecione um curso</option>
      <option value="KIDS 1">KIDS 1</option>
      <option value="KIDS 2">KIDS 2</option>
      <option value="KIDS 3">KIDS 3</option>
      <option value="TEENS 1">TEENS 1</option>
      <option value="TEENS 2">TEENS 2</option>
      <option value="TEENS 3">TEENS 3</option>
      <option value="ADVANCED 1">ADVANCED 1</option>
      <option value="ADVANCED 2">ADVANCED 2</option>
      <option value="ADVANCED 3">ADVANCED 3</option>
      <option value="CONVERSATION">CONVERSATION</option>
      <option value="BUSINESS">BUSINESS</option>
    </select>
  </div>
  
  <div class="form-group">
    <label for="cep">CEP</label>
    <input type="text" id="cep" name="cep" placeholder="12345-678" maxlength="9">
  </div>
  
  <div class="form-group">
    <label for="celular">Celular</label>
    <input type="text" id="celular" name="celular" placeholder="(11) 99999-9999">
  </div>
  
  <div class="form-group">
    <label for="email">Email</label>
    <input type="email" id="email" name="email" placeholder="aluno@email.com">
  </div>
  
  <button type="submit">Cadastrar Aluno</button>
</form>
`$language

```javascript
// Validação e submissão do formulário
class StudentFormHandler {
  constructor() {
    this.form = document.getElementById('studentForm');
    this.setupEventListeners();
  }
  
  setupEventListeners() {
    this.form.addEventListener('submit', this.handleSubmit.bind(this));
    
    // Máscara para CEP
    document.getElementById('cep').addEventListener('input', this.formatCEP);
    
    // Máscara para celular
    document.getElementById('celular').addEventListener('input', this.formatPhone);
  }
  
  formatCEP(event) {
    let value = event.target.value.replace(/\D/g, '');
    if (value.length > 5) {
      value = value.replace(/(\d{5})(\d)/, '$1-$2');
    }
    event.target.value = value;
  }
  
  formatPhone(event) {
    let value = event.target.value.replace(/\D/g, '');
    if (value.length > 0) {
      value = value.replace(/(\d{2})(\d)/, '($1) $2');
      if (value.length > 9) {
        value = value.replace(/(\d{4,5})(\d{4})$/, '$1-$2');
      }
    }
    event.target.value = value;
  }
  
  validateForm(formData) {
    const errors = [];
    
    if (!formData.nome_aluno.trim()) {
      errors.push('Nome do aluno é obrigatório');
    }
    
    if (!formData.curso) {
      errors.push('Curso é obrigatório');
    }
    
    if (formData.cep && !/^\d{5}-\d{3}$/.test(formData.cep)) {
      errors.push('CEP deve estar no formato 12345-678');
    }
    
    if (formData.celular && !/^\(\d{2}\)\s\d{4,5}-\d{4}$/.test(formData.celular)) {
      errors.push('Celular deve estar no formato (11) 99999-9999');
    }
    
    return errors;
  }
  
  async handleSubmit(event) {
    event.preventDefault();
    
    const formData = new FormData(this.form);
    const studentData = Object.fromEntries(formData.entries());
    
    // Validação
    const errors = this.validateForm(studentData);
    if (errors.length > 0) {
      this.showErrors(errors);
      return;
    }
    
    try {
      const response = await fetch('/api/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        body: JSON.stringify({
          ...studentData,
          tenant_id: this.getCurrentTenant(),
          cpf_hash: this.generateCPFHash(studentData.cpf)
        })
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      this.showSuccess(`Aluno cadastrado com sucesso! ID: ${result.id}`);
      this.form.reset();
      
    } catch (error) {
      this.showError(`Erro ao cadastrar aluno: ${error.message}`);
    }
  }
  
  showSuccess(message) {
    // Implementar notificação de sucesso
    console.log('Sucesso:', message);
  }
  
  showError(message) {
    // Implementar notificação de erro
    console.error('Erro:', message);
  }
  
  showErrors(errors) {
    // Implementar exibição de erros de validação
    console.error('Erros de validação:', errors);
  }
  
  getAuthToken() {
    // Implementar obtenção do token de autenticação
    return localStorage.getItem('authToken');
  }
  
  getCurrentTenant() {
    // Implementar obtenção do tenant atual
    return localStorage.getItem('currentTenant');
  }
  
  generateCPFHash(cpf) {
    // Implementar geração de hash do CPF
    return btoa(cpf || '');
  }
}

// Inicializar o handler do formulário
document.addEventListener('DOMContentLoaded', () => {
  new StudentFormHandler();
});
`$language

### 2. Lista de Entidades com IDs Personalizados

```javascript
// Componente para exibir lista de estudantes
class StudentList {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.students = [];
    this.loadStudents();
  }
  
  async loadStudents() {
    try {
      const response = await fetch('/api/students', {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      this.students = await response.json();
      this.render();
      
    } catch (error) {
      console.error('Erro ao carregar estudantes:', error);
      this.showError('Erro ao carregar lista de estudantes');
    }
  }
  
  render() {
    const html = `
      <div class="student-list">
        <h3>Lista de Estudantes</h3>
        <div class="student-grid">
          ${this.students.map(student => this.renderStudentCard(student)).join('')}
        </div>
      </div>
    `;
    
    this.container.innerHTML = html;
  }
  
  renderStudentCard(student) {
    const idInfo = this.parseStudentId(student.id);
    
    return `
      <div class="student-card" data-id="${student.id}">
        <div class="student-header">
          <h4>${student.nome_aluno}</h4>
          <span class="student-id" title="ID: ${student.id}">
            ${idInfo.displayId}
          </span>
        </div>
        <div class="student-info">
          <p><strong>Curso:</strong> ${student.curso}</p>
          <p><strong>Tipo:</strong> ${idInfo.courseType}</p>
          <p><strong>Email:</strong> ${student.email || 'Não informado'}</p>
        </div>
        <div class="student-actions">
          <button onclick="editStudent('${student.id}')">Editar</button>
          <button onclick="viewStudent('${student.id}')">Visualizar</button>
        </div>
      </div>
    `;
  }
  
  parseStudentId(id) {
    // Extrai informações do ID personalizado
    const match = id.match(/^STD_([A-Z0-9]+)_([A-Z0-9]+)$/);
    
    if (!match) {
      return {
        displayId: id,
        courseType: 'Desconhecido'
      };
    }
    
    const [, code, suffix] = match;
    const courseTypes = {
      'K1': 'Kids Nível 1', 'K2': 'Kids Nível 2', 'K3': 'Kids Nível 3',
      'T1': 'Teens Nível 1', 'T2': 'Teens Nível 2', 'T3': 'Teens Nível 3',
      'A1': 'Advanced Nível 1', 'A2': 'Advanced Nível 2', 'A3': 'Advanced Nível 3',
      'CV': 'Conversation', 'BZ': 'Business', 'OT': 'Outros'
    };
    
    return {
      displayId: `STD-${code}-${suffix}`,
      courseType: courseTypes[suffix] || 'Desconhecido'
    };
  }
  
  getAuthToken() {
    return localStorage.getItem('authToken');
  }
  
  showError(message) {
    this.container.innerHTML = `<div class="error-message">${message}</div>`;
  }
}
`$language

### 3. Busca e Filtros por Tipo de ID

```javascript
// Sistema de busca avançada
class EntitySearch {
  constructor() {
    this.setupFilters();
  }
  
  setupFilters() {
    const searchInput = document.getElementById('searchInput');
    const entityTypeFilter = document.getElementById('entityTypeFilter');
    const categoryFilter = document.getElementById('categoryFilter');
    
    searchInput.addEventListener('input', this.handleSearch.bind(this));
    entityTypeFilter.addEventListener('change', this.handleFilter.bind(this));
    categoryFilter.addEventListener('change', this.handleFilter.bind(this));
  }
  
  handleSearch(event) {
    const query = event.target.value.toLowerCase();
    const entityType = document.getElementById('entityTypeFilter').value;
    
    this.performSearch(query, entityType);
  }
  
  handleFilter(event) {
    const query = document.getElementById('searchInput').value.toLowerCase();
    const entityType = document.getElementById('entityTypeFilter').value;
    
    this.performSearch(query, entityType);
  }
  
  async performSearch(query, entityType) {
    try {
      let endpoint = '/api/search';
      const params = new URLSearchParams();
      
      if (query) params.append('q', query);
      if (entityType) params.append('type', entityType);
      
      if (params.toString()) {
        endpoint += '?' + params.toString();
      }
      
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${this.getAuthToken()}`
        }
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      const results = await response.json();
      this.displayResults(results);
      
    } catch (error) {
      console.error('Erro na busca:', error);
    }
  }
  
  displayResults(results) {
    const container = document.getElementById('searchResults');
    
    if (results.length === 0) {
      container.innerHTML = '<p>Nenhum resultado encontrado.</p>';
      return;
    }
    
    const html = results.map(item => {
      const entityInfo = this.parseEntityId(item.id);
      
      return `
        <div class="search-result-item">
          <div class="entity-badge ${entityInfo.type.toLowerCase()}">
            ${entityInfo.type}
          </div>
          <div class="entity-info">
            <h4>${item.name || item.nome_aluno || item.trade_name}</h4>
            <p class="entity-id">ID: ${item.id}</p>
            <p class="entity-category">${entityInfo.category}</p>
          </div>
          <div class="entity-actions">
            <button onclick="viewEntity('${item.id}', '${entityInfo.type}')">Ver Detalhes</button>
          </div>
        </div>
      `;
    }).join('');
    
    container.innerHTML = html;
  }
  
  parseEntityId(id) {
    if (id.startsWith('STD_')) {
      return { type: 'Student', category: this.getStudentCategory(id) };
    } else if (id.startsWith('EMP_')) {
      return { type: 'Employee', category: this.getEmployeeCategory(id) };
    } else if (id.startsWith('PTN_')) {
      return { type: 'Partner', category: this.getPartnerCategory(id) };
    }
    
    return { type: 'Unknown', category: 'Desconhecido' };
  }
  
  getStudentCategory(id) {
    const suffixMatch = id.match(/_([A-Z0-9]+)$/);
    if (!suffixMatch) return 'Desconhecido';
    
    const categories = {
      'K1': 'Kids 1', 'K2': 'Kids 2', 'K3': 'Kids 3',
      'T1': 'Teens 1', 'T2': 'Teens 2', 'T3': 'Teens 3',
      'A1': 'Advanced 1', 'A2': 'Advanced 2', 'A3': 'Advanced 3',
      'CV': 'Conversation', 'BZ': 'Business'
    };
    
    return categories[suffixMatch[1]] || 'Outros';
  }
  
  getEmployeeCategory(id) {
    const suffixMatch = id.match(/_([A-Z]+)$/);
    if (!suffixMatch) return 'Desconhecido';
    
    const categories = {
      'PR': 'Professor(a)', 'CDA': 'CDA', 'AF': 'Adm. Financeiro',
      'CO': 'Coordenador(a)'
    };
    
    return categories[suffixMatch[1]] || 'Outros';
  }
  
  getPartnerCategory(id) {
    const suffixMatch = id.match(/_([A-Z]+)$/);
    if (!suffixMatch) return 'Desconhecido';
    
    const categories = {
      'TEC': 'Tecnologia', 'SAU': 'Saúde', 'EDU': 'Educação',
      'ALI': 'Alimentação', 'VAR': 'Varejo', 'SER': 'Serviços'
    };
    
    return categories[suffixMatch[1]] || 'Outros';
  }
  
  getAuthToken() {
    return localStorage.getItem('authToken');
  }
}
`$language

### 4. Componente React para Integração

```jsx
// Componente React para formulário de estudante
import React, { useState } from 'react';

const StudentForm = ({ onSubmit, onCancel }) => {
  const [formData, setFormData] = useState({
    nome_aluno: '',
    curso: '',
    cep: '',
    celular: '',
    email: ''
  });
  
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  
  const courseOptions = [
    { value: 'KIDS 1', label: 'KIDS 1' },
    { value: 'KIDS 2', label: 'KIDS 2' },
    { value: 'KIDS 3', label: 'KIDS 3' },
    { value: 'TEENS 1', label: 'TEENS 1' },
    { value: 'TEENS 2', label: 'TEENS 2' },
    { value: 'TEENS 3', label: 'TEENS 3' },
    { value: 'ADVANCED 1', label: 'ADVANCED 1' },
    { value: 'ADVANCED 2', label: 'ADVANCED 2' },
    { value: 'ADVANCED 3', label: 'ADVANCED 3' },
    { value: 'CONVERSATION', label: 'CONVERSATION' },
    { value: 'BUSINESS', label: 'BUSINESS' }
  ];
  
  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.nome_aluno.trim()) {
      newErrors.nome_aluno = 'Nome é obrigatório';
    }
    
    if (!formData.curso) {
      newErrors.curso = 'Curso é obrigatório';
    }
    
    if (formData.cep && !/^\d{5}-\d{3}$/.test(formData.cep)) {
      newErrors.cep = 'CEP deve estar no formato 12345-678';
    }
    
    if (formData.celular && !/^\(\d{2}\)\s\d{4,5}-\d{4}$/.test(formData.celular)) {
      newErrors.celular = 'Celular deve estar no formato (11) 99999-9999';
    }
    
    if (formData.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Email deve ter um formato válido';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    
    try {
      const response = await fetch('/api/students', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('authToken')}`
        },
        body: JSON.stringify({
          ...formData,
          tenant_id: localStorage.getItem('currentTenant')
        })
      });
      
      if (!response.ok) {
        throw new Error(`Erro ${response.status}: ${response.statusText}`);
      }
      
      const result = await response.json();
      onSubmit(result);
      
    } catch (error) {
      console.error('Erro ao cadastrar estudante:', error);
      setErrors({ submit: error.message });
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Limpar erro do campo quando o usuário começar a digitar
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  };
  
  const formatCEP = (value) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length > 5) {
      return numbers.replace(/(\d{5})(\d)/, '$1-$2');
    }
    return numbers;
  };
  
  const formatPhone = (value) => {
    const numbers = value.replace(/\D/g, '');
    if (numbers.length > 0) {
      let formatted = numbers.replace(/(\d{2})(\d)/, '($1) $2');
      if (numbers.length > 6) {
        formatted = formatted.replace(/(\d{4,5})(\d{4})$/, '$1-$2');
      }
      return formatted;
    }
    return value;
  };
  
  return (
    <form onSubmit={handleSubmit} className="student-form">
      <div className="form-group">
        <label htmlFor="nome_aluno">Nome do Aluno *</label>
        <input
          type="text"
          id="nome_aluno"
          value={formData.nome_aluno}
          onChange={(e) => handleInputChange('nome_aluno', e.target.value)}
          className={errors.nome_aluno ? 'error' : ''}
          required
        />
        {errors.nome_aluno && <span className="error-text">{errors.nome_aluno}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="curso">Curso *</label>
        <select
          id="curso"
          value={formData.curso}
          onChange={(e) => handleInputChange('curso', e.target.value)}
          className={errors.curso ? 'error' : ''}
          required
        >
          <option value="">Selecione um curso</option>
          {courseOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {errors.curso && <span className="error-text">{errors.curso}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="cep">CEP</label>
        <input
          type="text"
          id="cep"
          value={formData.cep}
          onChange={(e) => handleInputChange('cep', formatCEP(e.target.value))}
          placeholder="12345-678"
          maxLength="9"
          className={errors.cep ? 'error' : ''}
        />
        {errors.cep && <span className="error-text">{errors.cep}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="celular">Celular</label>
        <input
          type="text"
          id="celular"
          value={formData.celular}
          onChange={(e) => handleInputChange('celular', formatPhone(e.target.value))}
          placeholder="(11) 99999-9999"
          className={errors.celular ? 'error' : ''}
        />
        {errors.celular && <span className="error-text">{errors.celular}</span>}
      </div>
      
      <div className="form-group">
        <label htmlFor="email">Email</label>
        <input
          type="email"
          id="email"
          value={formData.email}
          onChange={(e) => handleInputChange('email', e.target.value)}
          placeholder="aluno@email.com"
          className={errors.email ? 'error' : ''}
        />
        {errors.email && <span className="error-text">{errors.email}</span>}
      </div>
      
      {errors.submit && (
        <div className="error-message">
          {errors.submit}
        </div>
      )}
      
      <div className="form-actions">
        <button type="button" onClick={onCancel} disabled={isSubmitting}>
          Cancelar
        </button>
        <button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Cadastrando...' : 'Cadastrar Aluno'}
        </button>
      </div>
    </form>
  );
};

export default StudentForm;
`$language

## Resumo de Implementação

1. **Validação de Entrada**: Sempre valide formatos antes de enviar
2. **Máscaras de Input**: Use máscaras para CEP, telefone e CNPJ
3. **Tratamento de Erros**: Implemente feedback adequado para o usuário
4. **Parsing de IDs**: Extraia informações úteis dos IDs gerados
5. **Busca e Filtros**: Utilize os prefixos para categorização
6. **Componentes Reutilizáveis**: Crie componentes modulares para diferentes entidades

Este guia fornece exemplos práticos para integração completa com o sistema de IDs personalizados do backend.
