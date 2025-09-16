# Guia de Autenticação Frontend React

Este documento detalha o fluxo completo de autenticação que o frontend React deve implementar para utilizar os serviços do backend KNN Portal Journey Club.

## Visão Geral do Fluxo

1. **Login com Firebase Authentication**
2. **Obtenção do Token Firebase**
3. **Envio do Token para o Backend**
4. **Recebimento do JWT Local**
5. **Uso do JWT em Requisições Subsequentes**

## 1. Configuração Inicial do Firebase

### Instalação das Dependências

```bash
npm install firebase
```

### Configuração do Firebase

```javascript
// src/config/firebase.js
import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const firebaseConfig = {
  apiKey: "sua-api-key",
  authDomain: "seu-projeto.firebaseapp.com",
  projectId: "seu-projeto-id",
  storageBucket: "seu-projeto.appspot.com",
  messagingSenderId: "123456789",
  appId: "sua-app-id"
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
```

## 2. Implementação do Login

### Hook de Autenticação

```javascript
// src/hooks/useAuth.js
import { useState, useEffect } from 'react';
import { 
  signInWithEmailAndPassword,
  signOut,
  onAuthStateChanged
} from 'firebase/auth';
import { auth } from '../config/firebase';

const API_BASE_URL = 'http://localhost:8080/v1';

export const useAuth = () => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [jwtToken, setJwtToken] = useState(localStorage.getItem('jwt_token'));

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      if (firebaseUser) {
        try {
          // Obter o token Firebase
          const firebaseToken = await firebaseUser.getIdToken();
          
          // Enviar para o backend e obter JWT local
          const jwtResponse = await loginWithFirebaseToken(firebaseToken);
          
          if (jwtResponse.success) {
            setJwtToken(jwtResponse.jwt_token);
            localStorage.setItem('jwt_token', jwtResponse.jwt_token);
            setUser(firebaseUser);
          }
        } catch (error) {
          console.error('Erro na autenticação:', error);
          setUser(null);
          setJwtToken(null);
          localStorage.removeItem('jwt_token');
        }
      } else {
        setUser(null);
        setJwtToken(null);
        localStorage.removeItem('jwt_token');
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const login = async (email, password) => {
    try {
      setLoading(true);
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      return { success: true, user: userCredential.user };
    } catch (error) {
      return { success: false, error: error.message };
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await signOut(auth);
      setJwtToken(null);
      localStorage.removeItem('jwt_token');
      return { success: true };
    } catch (error) {
      return { success: false, error: error.message };
    }
  };

  return {
    user,
    jwtToken,
    loading,
    login,
    logout
  };
};

// Função para trocar token Firebase por JWT local
const loginWithFirebaseToken = async (firebaseToken) => {
  try {
    const response = await fetch(`${API_BASE_URL}/users/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        firebase_token: firebaseToken
      })
    });

    if (!response.ok) {
      throw new Error(`Erro HTTP: ${response.status}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Erro ao fazer login com token Firebase:', error);
    throw error;
  }
};
```

## 3. Componente de Login

```javascript
// src/components/Login.jsx
import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login, loading } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const result = await login(email, password);
    
    if (!result.success) {
      setError(result.error);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="email">Email:</label>
        <input
          type="email"
          id="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
      </div>
      
      <div>
        <label htmlFor="password">Senha:</label>
        <input
          type="password"
          id="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
      </div>
      
      {error && <div style={{color: 'red'}}>{error}</div>}
      
      <button type="submit" disabled={loading}>
        {loading ? 'Entrando...' : 'Entrar'}
      </button>
    </form>
  );
};

export default Login;
```

## 4. Serviço de API

### Cliente HTTP Configurado

```javascript
// src/services/api.js
const API_BASE_URL = 'http://localhost:8080/v1';

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  // Método para fazer requisições autenticadas
  async authenticatedRequest(endpoint, options = {}) {
    const token = localStorage.getItem('jwt_token');
    
    if (!token) {
      throw new Error('Token de autenticação não encontrado');
    }

    const defaultHeaders = {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    };

    const config = {
      ...options,
      headers: {
        ...defaultHeaders,
        ...options.headers
      }
    };

    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, config);
      
      if (response.status === 401) {
        // Token expirado ou inválido
        localStorage.removeItem('jwt_token');
        window.location.href = '/login';
        throw new Error('Sessão expirada. Faça login novamente.');
      }

      if (!response.ok) {
        throw new Error(`Erro HTTP: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Erro na requisição:', error);
      throw error;
    }
  }

  // Métodos específicos para diferentes endpoints
  
  // Obter dados do usuário atual
  async getCurrentUser() {
    return this.authenticatedRequest('/users/me');
  }

  // Obter lista de estudantes (exemplo)
  async getStudents(page = 1, limit = 10) {
    return this.authenticatedRequest(`/students?page=${page}&limit=${limit}`);
  }

  // Criar novo estudante
  async createStudent(studentData) {
    return this.authenticatedRequest('/students', {
      method: 'POST',
      body: JSON.stringify(studentData)
    });
  }

  // Atualizar estudante
  async updateStudent(studentId, studentData) {
    return this.authenticatedRequest(`/students/${studentId}`, {
      method: 'PUT',
      body: JSON.stringify(studentData)
    });
  }

  // Deletar estudante
  async deleteStudent(studentId) {
    return this.authenticatedRequest(`/students/${studentId}`, {
      method: 'DELETE'
    });
  }

  // Obter parceiros
  async getPartners() {
    return this.authenticatedRequest('/partners');
  }

  // Obter funcionários
  async getEmployees() {
    return this.authenticatedRequest('/employees');
  }
}

export const apiService = new ApiService();
```

## 5. Hook para Dados da API

```javascript
// src/hooks/useApiData.js
import { useState, useEffect } from 'react';
import { apiService } from '../services/api';

export const useApiData = (endpoint, dependencies = []) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const result = await apiService.authenticatedRequest(endpoint);
        setData(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, dependencies);

  const refetch = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const result = await apiService.authenticatedRequest(endpoint);
      setData(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return { data, loading, error, refetch };
};
```

## 6. Componente de Exemplo - Lista de Estudantes

```javascript
// src/components/StudentsList.jsx
import React from 'react';
import { useApiData } from '../hooks/useApiData';

const StudentsList = () => {
  const { data: students, loading, error, refetch } = useApiData('/students');

  if (loading) return <div>Carregando estudantes...</div>;
  if (error) return <div>Erro: {error}</div>;

  return (
    <div>
      <h2>Lista de Estudantes</h2>
      <button onClick={refetch}>Atualizar</button>
      
      {students?.data?.map(student => (
        <div key={student.id} style={{border: '1px solid #ccc', margin: '10px', padding: '10px'}}>
          <h3>{student.nome}</h3>
          <p>Email: {student.email}</p>
          <p>Curso: {student.curso}</p>
          <p>Status: {student.status}</p>
        </div>
      ))}
    </div>
  );
};

export default StudentsList;
```

## 7. Contexto de Autenticação

```javascript
// src/contexts/AuthContext.jsx
import React, { createContext, useContext } from 'react';
import { useAuth } from '../hooks/useAuth';

const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
  const auth = useAuth();
  
  return (
    <AuthContext.Provider value={auth}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuthContext = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuthContext deve ser usado dentro de AuthProvider');
  }
  return context;
};
```

## 8. Componente de Rota Protegida

```javascript
// src/components/ProtectedRoute.jsx
import React from 'react';
import { useAuthContext } from '../contexts/AuthContext';
import Login from './Login';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuthContext();

  if (loading) {
    return <div>Carregando...</div>;
  }

  if (!user) {
    return <Login />;
  }

  return children;
};

export default ProtectedRoute;
```

## 9. App Principal

```javascript
// src/App.jsx
import React from 'react';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import StudentsList from './components/StudentsList';

function App() {
  return (
    <AuthProvider>
      <div className="App">
        <ProtectedRoute>
          <h1>KNN Portal Journey Club</h1>
          <StudentsList />
        </ProtectedRoute>
      </div>
    </AuthProvider>
  );
}

export default App;
```

## 10. Fluxo Detalhado das Requisições

### Passo 1: Login Firebase
```javascript
// O usuário faz login com email/senha no Firebase
const userCredential = await signInWithEmailAndPassword(auth, email, password);
const firebaseToken = await userCredential.user.getIdToken();
```

### Passo 2: Troca de Token
```javascript
// Envia o token Firebase para o backend
POST /v1/users/login
Content-Type: application/json

{
  "firebase_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6..."
}

// Resposta do backend
{
  "success": true,
  "jwt_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_info": {
    "uid": "firebase_uid",
    "email": "user@example.com",
    "tenant": "tenant_id"
  }
}
```

### Passo 3: Requisições Autenticadas
```javascript
// Todas as requisições subsequentes usam o JWT
GET /v1/users/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

GET /v1/students
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...

POST /v1/students
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
Content-Type: application/json

{
  "nome": "João Silva",
  "email": "joao@example.com",
  "curso": "Engenharia"
}
```

## 11. Tratamento de Erros

### Erros Comuns e Como Tratar

```javascript
// src/utils/errorHandler.js
export const handleApiError = (error) => {
  if (error.message.includes('401')) {
    // Token expirado
    localStorage.removeItem('jwt_token');
    window.location.href = '/login';
    return 'Sessão expirada. Faça login novamente.';
  }
  
  if (error.message.includes('403')) {
    return 'Você não tem permissão para acessar este recurso.';
  }
  
  if (error.message.includes('404')) {
    return 'Recurso não encontrado.';
  }
  
  if (error.message.includes('500')) {
    return 'Erro interno do servidor. Tente novamente mais tarde.';
  }
  
  return error.message || 'Erro desconhecido.';
};
```

## 12. Endpoints Disponíveis

### Autenticação
- `POST /v1/users/login` - Login com token Firebase
- `GET /v1/users/me` - Dados do usuário atual
- `POST /v1/users/test-firebase-token` - Teste de validação de token

### Estudantes
- `GET /v1/students` - Listar estudantes
- `POST /v1/students` - Criar estudante
- `GET /v1/students/{id}` - Obter estudante específico
- `PUT /v1/students/{id}` - Atualizar estudante
- `DELETE /v1/students/{id}` - Deletar estudante

### Parceiros
- `GET /v1/partners` - Listar parceiros
- `POST /v1/partners` - Criar parceiro
- `GET /v1/partners/{id}` - Obter parceiro específico
- `PUT /v1/partners/{id}` - Atualizar parceiro
- `DELETE /v1/partners/{id}` - Deletar parceiro

### Funcionários
- `GET /v1/employees` - Listar funcionários
- `POST /v1/employees` - Criar funcionário
- `GET /v1/employees/{id}` - Obter funcionário específico
- `PUT /v1/employees/{id}` - Atualizar funcionário
- `DELETE /v1/employees/{id}` - Deletar funcionário

## 13. Considerações de Segurança

1. **Armazenamento do JWT**: O token JWT é armazenado no localStorage. Para maior segurança, considere usar httpOnly cookies.

2. **Expiração de Token**: O backend gerencia a expiração do JWT. O frontend deve tratar erros 401 e redirecionar para login.

3. **HTTPS**: Em produção, sempre use HTTPS para todas as comunicações.

4. **Validação de Entrada**: Sempre valide dados no frontend antes de enviar para o backend.

## 14. Exemplo de Uso Completo

```javascript
// Exemplo de como usar tudo junto
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import { useAuthContext } from '../contexts/AuthContext';

const Dashboard = () => {
  const { user, logout } = useAuthContext();
  const [userData, setUserData] = useState(null);
  const [students, setStudents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        // Carregar dados do usuário
        const userInfo = await apiService.getCurrentUser();
        setUserData(userInfo);

        // Carregar estudantes
        const studentsData = await apiService.getStudents();
        setStudents(studentsData.data || []);
      } catch (error) {
        console.error('Erro ao carregar dados:', error);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const handleLogout = async () => {
    await logout();
  };

  if (loading) return <div>Carregando...</div>;

  return (
    <div>
      <header>
        <h1>Dashboard</h1>
        <div>
          <span>Bem-vindo, {userData?.email}</span>
          <button onClick={handleLogout}>Sair</button>
        </div>
      </header>
      
      <main>
        <section>
          <h2>Estudantes ({students.length})</h2>
          {students.map(student => (
            <div key={student.id}>
              <h3>{student.nome}</h3>
              <p>{student.email}</p>
            </div>
          ))}
        </section>
      </main>
    </div>
  );
};

export default Dashboard;
```

Este guia fornece uma implementação completa do fluxo de autenticação entre o frontend React e o backend KNN Portal Journey Club, incluindo todos os exemplos de código necessários para uma integração bem-sucedida.