# Exemplo Prático: Implementação React com Autenticação

Este documento fornece um exemplo completo de como implementar autenticação em uma aplicação React integrada com o backend do Portal de Benefícios KNN.

## Estrutura do Projeto React

```text
src/
├── components/
│   ├── ProtectedRoute.jsx
│   ├── LoginButton.jsx
│   └── UserProfile.jsx
├── services/
│   ├── auth.service.js
│   ├── api.client.js
│   └── student.service.js
├── hooks/
│   ├── useAuth.js
│   └── useApi.js
├── pages/
│   ├── LoginPage.jsx
│   ├── StudentDashboard.jsx
│   └── PartnersList.jsx
└── App.jsx
```

## 1. Configuração Inicial

### .env
```env
VITE_API_BASE_URL=http://localhost:8080/v1
VITE_AUTH_URL=https://auth.knnidiomas.com.br
```

### package.json (dependências relevantes)

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.8.0",
    "@tanstack/react-query": "^4.24.0"
  }
}
```

## 2. Serviços de Autenticação

### src/services/auth.service.js

```javascript
class AuthService {
  constructor() {
    this.TOKEN_KEY = 'knn_auth_token';
    this.listeners = new Set();
  }

  // Obter token do localStorage
  getToken() {
    return localStorage.getItem(this.TOKEN_KEY);
  }

  // Armazenar token
  setToken(token) {
    localStorage.setItem(this.TOKEN_KEY, token);
    this.notifyListeners();
  }

  // Remover token
  removeToken() {
    localStorage.removeItem(this.TOKEN_KEY);
    this.notifyListeners();
  }

  // Verificar se está autenticado
  isAuthenticated() {
    const token = this.getToken();
    if (!token) return false;

    try {
      const payload = this.decodeToken(token);
      return payload.exp > Date.now() / 1000;
    } catch {
      return false;
    }
  }

  // Decodificar token JWT
  decodeToken(token) {
    const base64Url = token.split('.')[1];
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split('')
        .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
        .join('')
    );
    return JSON.parse(jsonPayload);
  }

  // Obter informações do usuário
  getUserInfo() {
    const token = this.getToken();
    if (!token) return null;

    try {
      const payload = this.decodeToken(token);
      return {
        id: payload.sub,
        role: payload.role,
        tenant: payload.tenant,
        exp: payload.exp,
        iat: payload.iat
      };
    } catch {
      return null;
    }
  }

  // Fazer login (redirecionar para serviço de auth)
  login() {
    const redirectUri = encodeURIComponent(window.location.origin + '/auth/callback');
    const loginUrl = `${import.meta.env.VITE_AUTH_URL}/login?redirect_uri=${redirectUri}`;
    window.location.href = loginUrl;
  }

  // Fazer logout
  logout() {
    this.removeToken();
    window.location.href = '/login';
  }

  // Processar callback de autenticação
  handleAuthCallback() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('token');
    const error = urlParams.get('error');

    if (error) {
      throw new Error(`Erro de autenticação: ${error}`);
    }

    if (token) {
      this.setToken(token);
      // Limpar URL
      window.history.replaceState({}, document.title, window.location.pathname);
      return true;
    }

    return false;
  }

  // Sistema de listeners para mudanças de autenticação
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  notifyListeners() {
    this.listeners.forEach(callback => callback());
  }

  // Obter headers para requisições
  getAuthHeaders() {
    const token = this.getToken();
    return token ? {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    } : {
      'Content-Type': 'application/json'
    };
  }
}

export const authService = new AuthService();
```

### src/services/api.client.js

```javascript
import { authService } from './auth.service.js';

class ApiClient {
  constructor() {
    this.baseURL = import.meta.env.VITE_API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;

    const config = {
      ...options,
      headers: {
        ...authService.getAuthHeaders(),
        ...options.headers
      }
    };

    try {
      const response = await fetch(url, config);

      // Token expirado ou inválido
      if (response.status === 401) {
        authService.logout();
        throw new Error('Sessão expirada. Faça login novamente.');
      }

      // Acesso negado
      if (response.status === 403) {
        throw new Error('Você não tem permissão para acessar este recurso.');
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

## 3. Hooks Personalizados

### src/hooks/useAuth.js

```javascript
import { useState, useEffect } from 'react';
import { authService } from '../services/auth.service.js';

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated());
  const [userInfo, setUserInfo] = useState(authService.getUserInfo());
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const updateAuthState = () => {
      setIsAuthenticated(authService.isAuthenticated());
      setUserInfo(authService.getUserInfo());
    };

    // Listener para mudanças de autenticação
    const unsubscribe = authService.addListener(updateAuthState);

    return unsubscribe;
  }, []);

  const login = async () => {
    setIsLoading(true);
    try {
      authService.login();
    } catch (error) {
      console.error('Erro no login:', error);
      setIsLoading(false);
    }
  };

  const logout = () => {
    authService.logout();
  };

  const handleAuthCallback = () => {
    try {
      return authService.handleAuthCallback();
    } catch (error) {
      console.error('Erro no callback de auth:', error);
      return false;
    }
  };

  return {
    isAuthenticated,
    userInfo,
    isLoading,
    login,
    logout,
    handleAuthCallback
  };
}
```

### src/hooks/useApi.js

```javascript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../services/api.client.js';

export function useApi() {
  const queryClient = useQueryClient();

  // Hook para queries GET
  const useApiQuery = (key, endpoint, options = {}) => {
    return useQuery({
      queryKey: Array.isArray(key) ? key : [key],
      queryFn: () => apiClient.get(endpoint),
      ...options
    });
  };

  // Hook para mutations (POST, PUT, DELETE)
  const useApiMutation = (mutationFn, options = {}) => {
    return useMutation({
      mutationFn,
      onSuccess: () => {
        // Invalidar queries relacionadas
        if (options.invalidateQueries) {
          queryClient.invalidateQueries(options.invalidateQueries);
        }
      },
      ...options
    });
  };

  return {
    useApiQuery,
    useApiMutation,
    queryClient
  };
}
```

## 4. Componentes

### src/components/ProtectedRoute.jsx

```javascript
import { Navigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

export function ProtectedRoute({ children, allowedRoles = [] }) {
  const { isAuthenticated, userInfo } = useAuth();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(userInfo?.role)) {
    return (
      <div className="unauthorized">
        <h2>Acesso Negado</h2>
        <p>Você não tem permissão para acessar esta página.</p>
      </div>
    );
  }

  return children;
}
```

### src/components/UserProfile.jsx

```javascript
import { useAuth } from '../hooks/useAuth.js';

export function UserProfile() {
  const { userInfo, logout } = useAuth();

  if (!userInfo) return null;

  const getRoleLabel = (role) => {
    const labels = {
      student: 'Aluno',
      partner: 'Parceiro',
      employee: 'Funcionário',
      admin: 'Administrador'
    };
    return labels[role] || role;
  };

  return (
    <div className="user-profile">
      <div className="user-info">
        <p><strong>ID:</strong> {userInfo.id}</p>
        <p><strong>Perfil:</strong> {getRoleLabel(userInfo.role)}</p>
        <p><strong>Tenant:</strong> {userInfo.tenant}</p>
      </div>
      <button onClick={logout} className="logout-btn">
        Sair
      </button>
    </div>
  );
}
```

## 5. Páginas

### src/pages/LoginPage.jsx

```javascript
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth.js';

export function LoginPage() {
  const { isAuthenticated, login, handleAuthCallback } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Verificar se é callback de autenticação
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('token')) {
      const success = handleAuthCallback();
      if (success) {
        navigate('/dashboard');
      }
    }
  }, [handleAuthCallback, navigate]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard');
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="login-page">
      <div className="login-container">
        <h1>Portal de Benefícios KNN</h1>
        <p>Faça login para acessar os benefícios exclusivos.</p>
        <button onClick={login} className="login-btn">
          Entrar com KNN ID
        </button>
      </div>
    </div>
  );
}
```

### src/pages/StudentDashboard.jsx

```javascript
import { useAuth } from '../hooks/useAuth.js';
import { useApi } from '../hooks/useApi.js';
import { UserProfile } from '../components/UserProfile.jsx';

export function StudentDashboard() {
  const { userInfo } = useAuth();
  const { useApiQuery } = useApi();

  // Buscar parceiros
  const { data: partnersData, isLoading, error } = useApiQuery(
    ['partners'],
    '/student/partners?limit=10'
  );

  // Buscar favoritos
  const { data: favoritesData } = useApiQuery(
    ['favorites'],
    '/student/favorites'
  );

  if (isLoading) {
    return <div className="loading">Carregando...</div>;
  }

  if (error) {
    return <div className="error">Erro: {error.message}</div>;
  }

  return (
    <div className="student-dashboard">
      <header className="dashboard-header">
        <h1>Bem-vindo, {userInfo?.id}!</h1>
        <UserProfile />
      </header>

      <main className="dashboard-content">
        <section className="partners-section">
          <h2>Parceiros Disponíveis</h2>
          <div className="partners-grid">
            {partnersData?.data?.map(partner => (
              <div key={partner.id} className="partner-card">
                <h3>{partner.trade_name}</h3>
                <p>{partner.category}</p>
                <p>{partner.description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="favorites-section">
          <h2>Meus Favoritos</h2>
          <div className="favorites-count">
            {favoritesData?.data?.length || 0} parceiros favoritados
          </div>
        </section>
      </main>
    </div>
  );
}
```

## 6. Configuração do App Principal

### src/App.jsx

```javascript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ProtectedRoute } from './components/ProtectedRoute.jsx';
import { LoginPage } from './pages/LoginPage.jsx';
import { StudentDashboard } from './pages/StudentDashboard.jsx';
import { useAuth } from './hooks/useAuth.js';

// Configurar React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function AppRoutes() {
  const { isAuthenticated } = useAuth();

  return (
    <Routes>
      <Route
        path="/login"
        element={isAuthenticated ? <Navigate to="/dashboard" /> : <LoginPage />}
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <StudentDashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/"
        element={<Navigate to={isAuthenticated ? "/dashboard" : "/login"} />}
      />

      <Route
        path="*"
        element={<div>Página não encontrada</div>}
      />
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="app">
          <AppRoutes />
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
```

## 7. Estilos CSS (Exemplo)

### src/App.css

```css
.app {
  min-height: 100vh;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* Login Page */
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-container {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  text-align: center;
  max-width: 400px;
  width: 100%;
}

.login-btn {
  background: #4f46e5;
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 16px;
  cursor: pointer;
  margin-top: 1rem;
}

.login-btn:hover {
  background: #4338ca;
}

/* Dashboard */
.student-dashboard {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

/* User Profile */
.user-profile {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-info p {
  margin: 0.25rem 0;
  font-size: 0.875rem;
  color: #6b7280;
}

.logout-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

/* Partners Grid */
.partners-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
}

.partner-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 1rem;
  background: white;
}

.partner-card h3 {
  margin: 0 0 0.5rem 0;
  color: #1f2937;
}

/* Loading and Error States */
.loading, .error {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
  font-size: 1.125rem;
}

.error {
  color: #ef4444;
}

.unauthorized {
  text-align: center;
  padding: 2rem;
}
```

## 8. Exemplo de Uso Avançado

### Componente para Favoritar Parceiros

```javascript
import { useState } from 'react';
import { useApi } from '../hooks/useApi.js';
import { apiClient } from '../services/api.client.js';

export function FavoriteButton({ partnerId, isFavorited: initialFavorited }) {
  const [isFavorited, setIsFavorited] = useState(initialFavorited);
  const { useApiMutation } = useApi();

  const favoriteMutation = useApiMutation(
    async () => {
      if (isFavorited) {
        return apiClient.delete(`/student/partners/${partnerId}/favorite`);
      } else {
        return apiClient.post(`/student/partners/${partnerId}/favorite`);
      }
    },
    {
      onSuccess: () => {
        setIsFavorited(!isFavorited);
      },
      onError: (error) => {
        alert(`Erro: ${error.message}`);
      },
      invalidateQueries: ['favorites']
    }
  );

  return (
    <button
      onClick={() => favoriteMutation.mutate()}
      disabled={favoriteMutation.isLoading}
      className={`favorite-btn ${isFavorited ? 'favorited' : ''}`}
    >
      {favoriteMutation.isLoading ? '...' : (isFavorited ? '❤️' : '🤍')}
    </button>
  );
}
```

## Conclusão

Este exemplo fornece uma implementação completa e funcional de autenticação React integrada com o backend do Portal de Benefícios KNN. Os principais pontos incluem:

- **Gerenciamento de Estado**: Hooks personalizados para auth e API
- **Roteamento Protegido**: Componentes que verificam autenticação e roles
- **Tratamento de Erros**: Handling adequado de erros de API
- **Cache de Dados**: React Query para otimização de requisições
- **Experiência do Usuário**: Loading states e feedback visual

Para usar este código:

1. Instale as dependências necessárias
2. Configure as variáveis de ambiente
3. Adapte os estilos conforme seu design system
4. Teste todos os fluxos de autenticação
5. Implemente tratamento de erros específico para sua aplicação
