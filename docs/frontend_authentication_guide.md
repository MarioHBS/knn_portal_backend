# Guia de Autenticação Frontend - Portal KNN

## Visão Geral

Este guia explica como implementar autenticação no frontend do Portal de Benefícios KNN usando Firebase Auth como provedor de identidade.

## Arquitetura de Autenticação

O sistema utiliza **Firebase Authentication** com as seguintes características:

- **Provedor de Identidade**: Firebase Auth
- **Algoritmo JWT**: RS256 (RSA com SHA-256)
- **Roles**: student, partner, admin, employee
- **Ambiente**: Desenvolvimento local com comunicação segura

## Configuração do Frontend

### 1. Instalação e Configuração Inicial

Instale o Firebase SDK:

```bash
npm install firebase
```

Crie o arquivo `src/config/firebase.js`:

```javascript
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "sua-api-key",
  authDomain: "knn-benefits.firebaseapp.com",
  projectId: "knn-benefits",
  storageBucket: "knn-benefits.appspot.com",
  messagingSenderId: "123456789",
  appId: "sua-app-id"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export default app;
```

### 2. Variáveis de Ambiente

Crie o arquivo `.env.local` no projeto frontend:

```env
# URL da API backend
VITE_API_BASE_URL=http://localhost:8080/v1

# Configurações do Firebase
VITE_FIREBASE_API_KEY=sua-api-key
VITE_FIREBASE_AUTH_DOMAIN=knn-benefits.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=knn-benefits
VITE_FIREBASE_STORAGE_BUCKET=knn-benefits.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=sua-app-id

# Ambiente de desenvolvimento
VITE_ENVIRONMENT=development
```

### 3. Headers de Autenticação

Todas as requisições autenticadas devem incluir o header:

```javascript
const headers = {
  'Authorization': `Bearer ${token}`,
  'Content-Type': 'application/json'
};
```

## Implementação da Autenticação

### 1. Serviço de Autenticação Firebase

```javascript
// src/services/firebase.auth.js
import {
  signInWithEmailAndPassword,
  createUserWithEmailAndPassword,
  signOut,
  onAuthStateChanged,
  getIdToken
} from 'firebase/auth';
import { auth } from '../config/firebase.js';

class FirebaseAuthService {
  constructor() {
    this.currentUser = null;
    this.authStateListeners = new Set();

    // Monitorar mudanças no estado de autenticação
    onAuthStateChanged(auth, (user) => {
      this.currentUser = user;
      this.notifyListeners(user);
    });
  }

  // Login com email e senha
  async signIn(email, password) {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    } catch (error) {
      throw new Error(`Erro no login: ${error.message}`);
    }
  }

  // Registro de novo usuário
  async signUp(email, password) {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      return userCredential.user;
    } catch (error) {
      throw new Error(`Erro no registro: ${error.message}`);
    }
  }

  // Logout
  async signOut() {
    try {
      await signOut(auth);
    } catch (error) {
      throw new Error(`Erro no logout: ${error.message}`);
    }
  }

  // Obter token JWT do Firebase
  async getIdToken(forceRefresh = false) {
    if (!this.currentUser) {
      throw new Error('Usuário não autenticado');
    }

    try {
      return await getIdToken(this.currentUser, forceRefresh);
    } catch (error) {
      throw new Error(`Erro ao obter token: ${error.message}`);
    }
  }

  // Verificar se usuário está autenticado
  isAuthenticated() {
    return !!this.currentUser;
  }

  // Obter usuário atual
  getCurrentUser() {
    return this.currentUser;
  }

  // Sistema de listeners
  addAuthStateListener(callback) {
    this.authStateListeners.add(callback);
    return () => this.authStateListeners.delete(callback);
  }

  notifyListeners(user) {
    this.authStateListeners.forEach(callback => callback(user));
  }
}

export const firebaseAuthService = new FirebaseAuthService();
```

### 2. Integração com Backend

```javascript
// src/services/backend.auth.js
import { firebaseAuthService } from './firebase.auth.js';

class BackendAuthService {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL;
    this.userProfile = null;
  }

  // Autenticar com o backend usando token do Firebase
  async authenticateWithBackend() {
    try {
      const firebaseToken = await firebaseAuthService.getIdToken();

      // Enviar token para o backend para validação e obtenção do perfil
      const response = await fetch(`${this.baseURL}/utils/authenticate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${firebaseToken}`
        }
      });

      if (!response.ok) {
        throw new Error(`Erro de autenticação: ${response.status}`);
      }

      const data = await response.json();
      this.userProfile = data.user;

      return {
        token: firebaseToken,
        user: data.user
      };
    } catch (error) {
      throw new Error(`Falha na autenticação com backend: ${error.message}`);
    }
  }

  // Obter perfil do usuário
  getUserProfile() {
    return this.userProfile;
  }

  // Limpar dados de autenticação
  clearAuth() {
    this.userProfile = null;
  }
}

export const backendAuthService = new BackendAuthService();
```

### 3. Gerenciamento de Tokens

#### 3.1. Estrutura do Token Firebase

O token JWT do Firebase contém informações padrão:

```javascript
{
  "iss": "https://securetoken.google.com/knn-benefits",
  "aud": "knn-benefits",
  "auth_time": 1234567890,
  "user_id": "firebase_user_id",
  "sub": "firebase_user_id",
  "iat": 1234567890,
  "exp": 1234567890,
  "email": "user@example.com",
  "email_verified": true,
  "firebase": {
    "identities": {
      "email": ["user@example.com"]
    },
    "sign_in_provider": "password"
  }
}
```

#### 3.2. Perfil do Usuário

O backend retorna informações adicionais após validação:

```javascript
{
  "id": "STD_123456",          // ID interno do sistema
  "firebase_uid": "firebase_user_id",
  "email": "user@example.com",
  "role": "student",           // Role: student, partner, admin, employee
  "tenant": "tenant_id",       // ID do tenant
  "entity_id": "entity_123",   // ID da entidade
  "first_access": true,        // Primeiro acesso
  "active": true               // Status ativo
}
```

#### 3.3. Renovação Automática de Tokens

```javascript
// src/services/token.manager.js
class TokenManager {
  constructor() {
    this.refreshInterval = null;
    this.TOKEN_REFRESH_INTERVAL = 50 * 60 * 1000; // 50 minutos
  }

  // Iniciar renovação automática
  startAutoRefresh() {
    this.refreshInterval = setInterval(async () => {
      try {
        if (firebaseAuthService.isAuthenticated()) {
          await firebaseAuthService.getIdToken(true); // Force refresh
          console.log('Token renovado automaticamente');
        }
      } catch (error) {
        console.error('Erro na renovação automática:', error);
        this.stopAutoRefresh();
      }
    }, this.TOKEN_REFRESH_INTERVAL);
  }

  // Parar renovação automática
  stopAutoRefresh() {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
      this.refreshInterval = null;
    }
  }
}

export const tokenManager = new TokenManager();
```

## Serviço de Autenticação Unificado

```javascript
// src/services/auth.service.js
import { firebaseAuthService } from './firebase.auth.js';
import { backendAuthService } from './backend.auth.js';
import { tokenManager } from './token.manager.js';

class AuthService {
  constructor() {
    this.isInitialized = false;
    this.authStateListeners = new Set();
    this.currentToken = null;
    this.userProfile = null;
  }

  // Inicializar serviço de autenticação
  async initialize() {
    if (this.isInitialized) return;

    // Monitorar mudanças no Firebase Auth
    firebaseAuthService.addAuthStateListener(async (user) => {
      if (user) {
        try {
          // Autenticar com backend quando usuário faz login no Firebase
          const authData = await backendAuthService.authenticateWithBackend();
          this.currentToken = authData.token;
          this.userProfile = authData.user;

          // Iniciar renovação automática
          tokenManager.startAutoRefresh();

          this.notifyListeners({ authenticated: true, user: authData.user });
        } catch (error) {
          console.error('Erro na autenticação com backend:', error);
          this.handleAuthError(error);
        }
      } else {
        // Usuário deslogado
        this.clearAuthData();
        this.notifyListeners({ authenticated: false, user: null });
      }
    });

    this.isInitialized = true;
  }

  // Login com email e senha
  async signIn(email, password) {
    try {
      await firebaseAuthService.signIn(email, password);
      // O resto do fluxo é tratado pelo listener
    } catch (error) {
      throw new Error(`Falha no login: ${error.message}`);
    }
  }

  // Registro de novo usuário
  async signUp(email, password) {
    try {
      await firebaseAuthService.signUp(email, password);
      // O resto do fluxo é tratado pelo listener
    } catch (error) {
      throw new Error(`Falha no registro: ${error.message}`);
    }
  }

  // Logout
  async signOut() {
    try {
      await firebaseAuthService.signOut();
      // O resto da limpeza é tratado pelo listener
    } catch (error) {
      console.error('Erro no logout:', error);
      // Forçar limpeza mesmo com erro
      this.clearAuthData();
    }
  }

  // Verificar se usuário está autenticado
  isAuthenticated() {
    return firebaseAuthService.isAuthenticated() && !!this.userProfile;
  }

  // Obter perfil do usuário
  getUserProfile() {
    return this.userProfile;
  }

  // Obter token atual
  async getCurrentToken() {
    if (!this.isAuthenticated()) {
      throw new Error('Usuário não autenticado');
    }

    try {
      // Sempre obter token fresco do Firebase
      this.currentToken = await firebaseAuthService.getIdToken();
      return this.currentToken;
    } catch (error) {
      throw new Error(`Erro ao obter token: ${error.message}`);
    }
  }

  // Obter headers para requisições
  async getAuthHeaders() {
    try {
      const token = await this.getCurrentToken();
      return {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      };
    } catch (error) {
      return {
        'Content-Type': 'application/json'
      };
    }
  }

  // Limpar dados de autenticação
  clearAuthData() {
    this.currentToken = null;
    this.userProfile = null;
    tokenManager.stopAutoRefresh();
    backendAuthService.clearAuth();
  }

  // Tratar erros de autenticação
  handleAuthError(error) {
    console.error('Erro de autenticação:', error);
    this.clearAuthData();

    // Redirecionar para login se necessário
    if (window.location.pathname !== '/login') {
      window.location.href = '/login';
    }
  }

  // Sistema de listeners
  addAuthStateListener(callback) {
    this.authStateListeners.add(callback);
    return () => this.authStateListeners.delete(callback);
  }

  notifyListeners(authState) {
    this.authStateListeners.forEach(callback => callback(authState));
  }
}

export const authService = new AuthService();
```

## Cliente HTTP com Tratamento de Erros

```javascript
// src/services/api.client.js
import { authService } from './auth.service.js';

class ApiClient {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL;
    this.requestQueue = [];
    this.isRefreshing = false;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    try {
      const headers = await authService.getAuthHeaders();

      const config = {
        ...options,
        headers: {
          ...headers,
          ...options.headers
        }
      };

      const response = await fetch(url, config);

      // Tratar diferentes códigos de status
      if (response.status === 401) {
        return await this.handleUnauthorized(endpoint, options);
      }

      if (response.status === 403) {
        throw new Error('Você não tem permissão para acessar este recurso.');
      }

      if (response.status === 429) {
        throw new Error('Muitas requisições. Tente novamente em alguns segundos.');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const message = errorData.error?.msg || `Erro HTTP ${response.status}`;
        throw new Error(message);
      }

      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Tratar erro 401 com retry
  async handleUnauthorized(endpoint, options) {
    if (this.isRefreshing) {
      // Se já está renovando, adicionar à fila
      return new Promise((resolve, reject) => {
        this.requestQueue.push({ resolve, reject, endpoint, options });
      });
    }

    this.isRefreshing = true;

    try {
      // Tentar renovar token
      await authService.getCurrentToken();

      // Processar fila de requisições
      this.processRequestQueue();

      // Tentar novamente a requisição original
      return await this.request(endpoint, options);
    } catch (error) {
      // Falha na renovação - fazer logout
      this.processRequestQueue(error);
      await authService.signOut();
      throw new Error('Sessão expirada. Faça login novamente.');
    } finally {
      this.isRefreshing = false;
    }
  }

  // Processar fila de requisições
  processRequestQueue(error = null) {
    this.requestQueue.forEach(({ resolve, reject, endpoint, options }) => {
      if (error) {
        reject(error);
      } else {
        resolve(this.request(endpoint, options));
      }
    });
    this.requestQueue = [];
  }

  // Métodos de conveniência
  get(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'GET' });
  }

  post(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  put(endpoint, data, options = {}) {
    return this.request(endpoint, {
      ...options,
      method: 'PUT',
      body: JSON.stringify(data)
    });
  }

  delete(endpoint, options = {}) {
    return this.request(endpoint, { ...options, method: 'DELETE' });
  }
}

export const apiClient = new ApiClient();
```

## Tratamento de Erros

### 1. Tipos de Erros

```javascript
// src/utils/error.handler.js
export class AuthError extends Error {
  constructor(message, code = 'AUTH_ERROR') {
    super(message);
    this.name = 'AuthError';
    this.code = code;
  }
}

export class NetworkError extends Error {
  constructor(message, status = 0) {
    super(message);
    this.name = 'NetworkError';
    this.status = status;
  }
}

export class ValidationError extends Error {
  constructor(message, field = null) {
    super(message);
    this.name = 'ValidationError';
    this.field = field;
  }
}

// Mapeamento de erros do Firebase
export const firebaseErrorMap = {
  'auth/user-not-found': 'Usuário não encontrado.',
  'auth/wrong-password': 'Senha incorreta.',
  'auth/email-already-in-use': 'Este email já está em uso.',
  'auth/weak-password': 'A senha deve ter pelo menos 6 caracteres.',
  'auth/invalid-email': 'Email inválido.',
  'auth/too-many-requests': 'Muitas tentativas. Tente novamente mais tarde.',
  'auth/network-request-failed': 'Erro de conexão. Verifique sua internet.'
};

export function getFirebaseErrorMessage(errorCode) {
  return firebaseErrorMap[errorCode] || 'Erro desconhecido. Tente novamente.';
}
```

### 2. Hook de Tratamento de Erros

```javascript
// src/hooks/useErrorHandler.js
import { useState, useCallback } from 'react';
import { getFirebaseErrorMessage } from '../utils/error.handler.js';

export function useErrorHandler() {
  const [error, setError] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleAsync = useCallback(async (asyncFunction) => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await asyncFunction();
      return result;
    } catch (err) {
      let errorMessage = 'Erro desconhecido';

      if (err.code && err.code.startsWith('auth/')) {
        errorMessage = getFirebaseErrorMessage(err.code);
      } else if (err.message) {
        errorMessage = err.message;
      }

      setError(errorMessage);
      console.error('Error handled:', err);
      throw err;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  return {
    error,
    isLoading,
    handleAsync,
    clearError
  };
}
```

### 3. Componente de Notificação de Erros

```javascript
// src/components/ErrorNotification.jsx
import React from 'react';

export function ErrorNotification({ error, onClose }) {
  if (!error) return null;

  return (
    <div className="error-notification">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <span className="error-message">{error}</span>
        <button className="error-close" onClick={onClose}>
          ✕
        </button>
      </div>
    </div>
  );
}
```

## Exemplos Práticos de Uso

### 1. Página de Login

```javascript
// src/pages/LoginPage.jsx
import React, { useState } from 'react';
import { authService } from '../services/auth.service.js';
import { useErrorHandler } from '../hooks/useErrorHandler.js';
import { ErrorNotification } from '../components/ErrorNotification.jsx';

export function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { error, isLoading, handleAsync, clearError } = useErrorHandler();

  const handleLogin = async (e) => {
    e.preventDefault();

    await handleAsync(async () => {
      await authService.signIn(email, password);
      // Redirecionamento será tratado pelo AuthProvider
    });
  };

  return (
    <div className="login-page">
      <form onSubmit={handleLogin} className="login-form">
        <h2>Login</h2>

        <ErrorNotification error={error} onClose={clearError} />

        <div className="form-group">
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <input
            type="password"
            placeholder="Senha"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </div>

        <button type="submit" disabled={isLoading}>
          {isLoading ? 'Entrando...' : 'Entrar'}
        </button>
      </form>
    </div>
  );
}
```

### 2. Hook de Autenticação

```javascript
// src/hooks/useAuth.js
import { useState, useEffect } from 'react';
import { authService } from '../services/auth.service.js';

export function useAuth() {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Inicializar serviço de autenticação
    authService.initialize();

    // Escutar mudanças no estado de autenticação
    const unsubscribe = authService.addAuthStateListener((authState) => {
      setUser(authState.user);
      setIsAuthenticated(authState.authenticated);
      setIsLoading(false);
    });

    return unsubscribe;
  }, []);

  const signIn = async (email, password) => {
    await authService.signIn(email, password);
  };

  const signUp = async (email, password) => {
    await authService.signUp(email, password);
  };

  const signOut = async () => {
    await authService.signOut();
  };

  return {
    user,
    isAuthenticated,
    isLoading,
    signIn,
    signUp,
    signOut
  };
}
```

## Endpoints Disponíveis por Role

### Student (Aluno)
- `GET /v1/student/partners` - Listar parceiros
- `GET /v1/student/partners/{partner_id}` - Detalhes do parceiro
- `POST /v1/student/partners/{partner_id}/favorite` - Favoritar parceiro
- `DELETE /v1/student/partners/{partner_id}/favorite` - Desfavoritar
- `GET /v1/student/favorites` - Listar favoritos
- `GET /v1/student/history` - Histórico de resgates

### Partner (Parceiro)
- `POST /v1/partner/redeem` - Validar código de resgate
- `GET /v1/partner/profile` - Perfil do parceiro
- `PUT /v1/partner/profile` - Atualizar perfil

### Employee (Funcionário)
- `GET /v1/employee/partners` - Gerenciar parceiros
- `POST /v1/employee/partners` - Criar parceiro
- `PUT /v1/employee/partners/{partner_id}` - Atualizar parceiro
- `GET /v1/employee/students` - Gerenciar alunos

### Admin (Administrador)
- Todos os endpoints acima
- `GET /v1/admin/analytics` - Relatórios e analytics
- `GET /v1/admin/users` - Gerenciar usuários

## Exemplos de Uso

### 1. Listar Parceiros (Student)

```javascript
// Verificar se usuário é student
const userInfo = authService.getUserInfo();
if (userInfo?.role !== 'student') {
  throw new Error('Acesso negado');
}

// Fazer requisição
const partners = await apiClient.get('/student/partners?cat=Alimentação&limit=10');
console.log(partners.data);
```

### 2. Validar Código de Resgate (Partner)

```javascript
// Verificar se usuário é partner
const userInfo = authService.getUserInfo();
if (userInfo?.role !== 'partner') {
  throw new Error('Acesso negado');
}

// Validar código
const result = await apiClient.post('/partner/redeem', {
  validation_code: 'ABC123'
});
console.log(result.msg); // "Código validado com sucesso"
```

## Tratamento de Erros

### Códigos de Erro Comuns

- **401 Unauthorized**: Token inválido ou expirado
- **403 Forbidden**: Usuário não tem permissão para o recurso
- **404 Not Found**: Recurso não encontrado
- **429 Too Many Requests**: Rate limit excedido
- **500 Internal Server Error**: Erro interno do servidor

### Exemplo de Tratamento

```javascript
try {
  const data = await apiClient.get('/student/partners');
  // Processar dados
} catch (error) {
  if (error.message === 'Não autorizado') {
    // Redirecionar para login
    window.location.href = '/login';
  } else {
    // Mostrar erro para usuário
    alert(`Erro: ${error.message}`);
  }
}
```

## Configuração de Desenvolvimento Local

### 1. Configuração do Frontend

#### Arquivo .env.local
```bash
# Frontend - .env.local
VITE_API_BASE_URL=http://localhost:8000
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=knn-benefits.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=knn-benefits
VITE_FIREBASE_STORAGE_BUCKET=knn-benefits.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123456

# Desenvolvimento
VITE_DEBUG=true
VITE_TEST_MODE=false
```

#### Iniciar Frontend
```bash
cd frontend
npm install
npm run dev
```

### 2. Verificação de Conectividade

```javascript
// src/utils/health.check.js
export async function checkBackendHealth() {
  try {
    const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/health`);
    const data = await response.json();
    console.log('Backend status:', data);
    return data.status === 'healthy';
  } catch (error) {
    console.error('Backend não está disponível:', error);
    return false;
  }
}

// Usar no App.jsx
import { checkBackendHealth } from './utils/health.check.js';

useEffect(() => {
  checkBackendHealth().then(isHealthy => {
    if (!isHealthy) {
      console.warn('Backend não está rodando. Verifique a URL da API.');
    }
  });
}, []);
```

## Boas Práticas de Segurança

1. **Nunca expor credenciais** no código fonte
2. **Usar variáveis de ambiente** para configurações sensíveis
3. **Validar tokens** no backend sempre
4. **Implementar rate limiting** para prevenir ataques
5. **Usar HTTPS** em produção
6. **Implementar CSP headers** para prevenir XSS
7. **Validar entrada** do usuário sempre
8. **Logs de segurança** para auditoria

### Exemplo de Proteção de Rotas

```javascript
// route.guard.js
export function requireAuth(allowedRoles = []) {
  return (to, from, next) => {
    if (!authService.isAuthenticated()) {
      next('/login');
      return;
    }

    const userInfo = authService.getUserInfo();
    if (allowedRoles.length > 0 && !allowedRoles.includes(userInfo.role)) {
      next('/unauthorized');
      return;
    }

    next();
  };
}

// Uso no Vue Router
const routes = [
  {
    path: '/student/partners',
    component: PartnersPage,
    beforeEnter: requireAuth(['student'])
  },
  {
    path: '/partner/redeem',
    component: RedeemPage,
    beforeEnter: requireAuth(['partner'])
  }
];
```

## Troubleshooting

### Problemas Comuns

#### 1. Token Inválido
```javascript
// Verificar se o Firebase está configurado corretamente
console.log('Firebase config:', firebaseConfig);

// Verificar se o usuário está autenticado
console.log('User authenticated:', firebaseAuthService.isAuthenticated());
```

#### 2. Backend Não Responde
```javascript
// Verificar se a URL da API está correta
console.log('API URL:', import.meta.env.VITE_API_BASE_URL);

// Testar conectividade
fetch(`${import.meta.env.VITE_API_BASE_URL}/health`)
  .then(response => console.log('Backend status:', response.status))
  .catch(error => console.error('Backend error:', error));
```

#### 3. Problemas de Rede
```javascript
// Implementar retry com backoff
const retryRequest = async (fn, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * Math.pow(2, i)));
    }
  }
};
```

### Debug Avançado

```javascript
// Habilitar logs detalhados
localStorage.setItem('debug', 'auth:*');

// Verificar token atual
const token = await authService.getCurrentToken();
console.log('Current token:', token);

// Decodificar token JWT
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('Token payload:', payload);

// Verificar informações do usuário
console.log('User profile:', authService.getUserProfile());

// Verificar configurações do Firebase
console.log('Firebase Config:', {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY,
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN,
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID
});
```

## Health Check

Verifique se a API está funcionando:

```javascript
// Endpoint público (não requer autenticação)
const health = await fetch(`${import.meta.env.VITE_API_BASE_URL}/health`);
const status = await health.json();
console.log(status); // { "status": "ok", "mode": "normal" }
```

## Checklist de Implementação

### Frontend
- [ ] Instalar Firebase SDK (`npm install firebase`)
- [ ] Configurar Firebase no arquivo `src/config/firebase.js`
- [ ] Criar arquivo `.env.local` com variáveis do Firebase
- [ ] Implementar serviços de autenticação
- [ ] Criar componentes de login/registro
- [ ] Implementar rotas protegidas
- [ ] Configurar tratamento de erros
- [ ] Testar fluxo completo de autenticação

### Testes
- [ ] Testar login com credenciais válidas
- [ ] Testar login com credenciais inválidas
- [ ] Testar registro de novo usuário
- [ ] Testar logout
- [ ] Testar renovação automática de token
- [ ] Testar acesso a rotas protegidas
- [ ] Testar tratamento de erros de rede
- [ ] Verificar logs no console do navegador

## Conclusão

Este guia fornece uma implementação completa de autenticação entre frontend e backend usando Firebase como provedor de identidade. A arquitetura proposta oferece:

- **Segurança robusta** com validação de tokens JWT
- **Experiência de usuário fluida** com renovação automática de tokens
- **Tratamento abrangente de erros** com mensagens amigáveis
- **Flexibilidade de roles** para diferentes tipos de usuários
- **Facilidade de desenvolvimento** com configuração local clara

Para suporte adicional ou dúvidas sobre a implementação, consulte a documentação do Firebase Auth e os logs do backend para debugging detalhado.
