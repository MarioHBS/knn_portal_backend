# Guia de Configuração de Autenticação

## Problema Identificado

O servidor JWKS em `https://auth.knnidiomas.com.br/.well-known/jwks.json` não está acessível, causando erro 400 "JWT inválido" nos endpoints que requerem autenticação.

## Soluções Disponíveis

### 1. Solução Atual (Recomendada para Desenvolvimento)

**TESTING_MODE=true** - Já implementado e funcionando

```env
# .env
TESTING_MODE=true
```

**Vantagens:**

- Funciona imediatamente
- Ideal para desenvolvimento local
- Não requer configuração adicional

**Desvantagens:**

- Não testa autenticação real
- Não deve ser usado em produção

### 2. Implementar Autenticação JWT Local (Recomendada para Produção)

Criar endpoints de autenticação locais que geram JWTs válidos.

#### Implementação

1. **Adicionar endpoint de login:**

```python
# src/api/auth_local.py
from datetime import datetime, timedelta
import jwt
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["authentication"])

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    # Validação simples (implementar conforme necessário)
    if request.username == "admin" and request.password == "admin123":
        # Gerar JWT
        payload = {
            "sub": request.username,
            "role": "student",  # ou "admin", "employee", "partner"
            "tenant": "knn",
            "exp": datetime.utcnow() + timedelta(hours=24),
            "iat": datetime.utcnow(),
            "iss": "knn-portal",
            "aud": "knn-portal"
        }

        # Usar chave secreta do .env
        from src.config import JWT_SECRET_KEY
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm="HS256")

        return LoginResponse(access_token=token)

    raise HTTPException(status_code=401, detail="Credenciais inválidas")
```

2. **Adicionar configuração:**

```env
# .env
JWT_SECRET_KEY=sua_chave_secreta_muito_forte_aqui
TESTING_MODE=false
```

3. **Modificar auth.py para suportar JWT local:**

```python
# Em src/auth.py, adicionar na função verify_token:

# Após falha do Firebase, antes do JWKS externo:
try:
    # Tentar decodificar com chave local
    from src.config import JWT_SECRET_KEY
    payload_dict = jwt.decode(token, JWT_SECRET_KEY, algorithms=["HS256"])
    return JWTPayload(**payload_dict)
except jwt.InvalidTokenError:
    # Continuar para JWKS externo
    pass
```

### 3. Configurar Firebase Auth Adequadamente

Se preferir usar Firebase Auth:

1. **Verificar credenciais:**
   - Arquivo `credentials/default-service-account-key.json` deve existir
   - Projeto Firebase deve estar configurado corretamente

2. **Configurar variáveis:**

```env
# .env
FIREBASE_PROJECT_ID=seu-projeto-firebase
GOOGLE_APPLICATION_CREDENTIALS=credentials/default-service-account-key.json
```

3. **Testar conexão:**

```bash
python scripts/maintenance/test_firebase_connection.py
```

### 4. Criar Mock Server JWKS Local

Para testes mais realistas:

```python
# scripts/mock_jwks_server.py
from fastapi import FastAPI
import uvicorn
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import base64
import json

app = FastAPI()

# Gerar chave RSA para testes
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048
)

public_key = private_key.public_key()

@app.get("/.well-known/jwks.json")
async def get_jwks():
    # Retornar JWKS mock
    public_numbers = public_key.public_numbers()

    jwks = {
        "keys": [
            {
                "kty": "RSA",
                "kid": "test-key-1",
                "use": "sig",
                "alg": "RS256",
                "n": base64.urlsafe_b64encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, 'big')).decode().rstrip('='),
                "e": base64.urlsafe_b64encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, 'big')).decode().rstrip('=')
            }
        ]
    }

    return jwks

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
```

Executar em terminal separado:
```bash
python scripts/mock_jwks_server.py
```

E alterar no .env:
```env
JWKS_URL=http://localhost:9000/.well-known/jwks.json
```

### 5. Configurar Servidor JWKS Completo (Produção)

Para um ambiente de produção completo:

1. **Usar Auth0:**
   - Criar conta no Auth0
   - Configurar aplicação
   - Usar JWKS_URL do Auth0

2. **Usar Keycloak:**
   - Instalar Keycloak
   - Configurar realm e cliente
   - Usar endpoint JWKS do Keycloak

3. **Implementar servidor próprio:**
   - Criar servidor Node.js/Express ou Python/FastAPI
   - Implementar geração de JWT
   - Expor endpoint /.well-known/jwks.json
   - Hospedar em auth.knnidiomas.com.br

## Recomendações

### Para Desenvolvimento Local:

1. **Manter TESTING_MODE=true** (mais simples)
2. **Ou implementar JWT local** (mais realista)

### Para Produção

1. **Implementar autenticação JWT local** (controle total)
2. **Ou usar Firebase Auth** (se já configurado)
3. **Ou usar serviço terceiro** (Auth0, Keycloak)

## Testando a Solução

Após implementar qualquer solução:

```bash
# Testar endpoint
curl -X GET "http://localhost:8080/v1/student/partners" \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

## Status Atual

✅ **TESTING_MODE=true** - Funcionando para desenvolvimento
❌ **JWKS externo** - Servidor não acessível
⚠️ **Firebase Auth** - Precisa verificar configuração
💡 **JWT local** - Recomendado implementar
