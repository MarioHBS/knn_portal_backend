"""
Script para iniciar o servidor FastAPI para testes locais.
"""
import uvicorn

if __name__ == "__main__":
    print("Iniciando servidor FastAPI para o Portal de Benefícios KNN...")
    print("Acesse a documentação em: http://localhost:8080/v1/docs")
    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
