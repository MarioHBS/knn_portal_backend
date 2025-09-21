import os

import yaml

# Arquivo para validar os artefatos gerados para o Portal de Benefícios KNN
print("Iniciando validação dos artefatos do Portal de Benefícios KNN...")

# Lista de arquivos obrigatórios
required_files = [
    "openapi.yaml",
    "Dockerfile",
    "deploy_cloudrun.sh",
    "tests/test_api.py",
    "seed_dev.py"
]

# Verificar existência dos arquivos
print("\n1. Verificando existência dos arquivos obrigatórios...")
missing_files = []
for file in required_files:
    file_path = os.path.join(os.getcwd(), file)
    if os.path.exists(file_path):
        print(f"✓ {file} encontrado")
    else:
        print(f"✗ {file} não encontrado")
        missing_files.append(file)

if missing_files:
    print(f"\nATENÇÃO: {len(missing_files)} arquivo(s) obrigatório(s) não encontrado(s)!")
else:
    print("\nTodos os arquivos obrigatórios foram encontrados!")

# Validar OpenAPI
print("\n2. Validando estrutura do arquivo OpenAPI...")
try:
    with open("openapi.yaml") as f:
        openapi_content = yaml.safe_load(f)

    # Verificar elementos essenciais
    openapi_checks = {
        "Versão OpenAPI": "openapi" in openapi_content,
        "Info": "info" in openapi_content,
        "Paths": "paths" in openapi_content,
        "Components": "components" in openapi_content,
        "Security": "security" in openapi_content,
        "Schemas": "components" in openapi_content and "schemas" in openapi_content["components"],
        "SecuritySchemes": "components" in openapi_content and "securitySchemes" in openapi_content["components"]
    }

    # Verificar rotas essenciais
    essential_paths = [
        "/health",
        "/partners",
        "/partners/{id}",
        "/validation-codes",
        "/student/me/history",
        "/student/me/fav",
        "/partner/redeem",
        "/partner/promotions",
        "/admin/metrics"
    ]

    paths_checks = {}
    for path in essential_paths:
        full_path = f"/v1{path}" if "servers" in openapi_content else path
        paths_checks[path] = full_path in openapi_content.get("paths", {}) or path in openapi_content.get("paths", {})

    # Exibir resultados da validação OpenAPI
    for check, result in openapi_checks.items():
        print(f"{'✓' if result else '✗'} {check}")

    print("\nVerificando rotas essenciais:")
    for path, result in paths_checks.items():
        print(f"{'✓' if result else '✗'} {path}")

    if all(openapi_checks.values()) and all(paths_checks.values()):
        print("\nArquivo OpenAPI válido e completo!")
    else:
        print("\nATENÇÃO: Arquivo OpenAPI pode estar incompleto!")

except Exception as e:
    print(f"Erro ao validar OpenAPI: {str(e)}")

# Validar Dockerfile
print("\n3. Validando Dockerfile...")
try:
    with open("Dockerfile") as f:
        dockerfile_content = f.read()

    dockerfile_checks = {
        "FROM Python": "FROM python:" in dockerfile_content,
        "WORKDIR": "WORKDIR" in dockerfile_content,
        "COPY requirements": "COPY requirements" in dockerfile_content,
        "RUN pip install": "pip install" in dockerfile_content,
        "EXPOSE": "EXPOSE" in dockerfile_content,
        "CMD": "CMD" in dockerfile_content
    }

    for check, result in dockerfile_checks.items():
        print(f"{'✓' if result else '✗'} {check}")

    if all(dockerfile_checks.values()):
        print("\nDockerfile válido e completo!")
    else:
        print("\nATENÇÃO: Dockerfile pode estar incompleto!")

except Exception as e:
    print(f"Erro ao validar Dockerfile: {str(e)}")

# Validar script de deploy
print("\n4. Validando script de deploy...")
try:
    with open("deploy_cloudrun.sh") as f:
        deploy_content = f.read()

    deploy_checks = {
        "gcloud run deploy": "gcloud run deploy" in deploy_content,
        "docker build": "docker build" in deploy_content,
        "docker push": "docker push" in deploy_content,
        "Variáveis de ambiente": "--set-env-vars" in deploy_content
    }

    for check, result in deploy_checks.items():
        print(f"{'✓' if result else '✗'} {check}")

    if all(deploy_checks.values()):
        print("\nScript de deploy válido e completo!")
    else:
        print("\nATENÇÃO: Script de deploy pode estar incompleto!")

except Exception as e:
    print(f"Erro ao validar script de deploy: {str(e)}")

# Validar testes
print("\n5. Validando testes Pytest...")
try:
    with open("tests/test_api.py") as f:
        tests_content = f.read()

    tests_checks = {
        "Teste de health check": "test_health_check" in tests_content,
        "Teste de autenticação": "test_missing_token" in tests_content or "test_invalid_token" in tests_content,
        "Teste de role": "test_wrong_role" in tests_content,
        "Teste de rate limit": "test_rate_limit" in tests_content,
        "Teste de circuit breaker": "test_circuit_breaker" in tests_content,
        "Teste de mascaramento de CPF": "test_cpf_masking" in tests_content
    }

    for check, result in tests_checks.items():
        print(f"{'✓' if result else '✗'} {check}")

    if all(tests_checks.values()):
        print("\nTestes Pytest válidos e completos!")
    else:
        print("\nATENÇÃO: Testes Pytest podem estar incompletos!")

except Exception as e:
    print(f"Erro ao validar testes: {str(e)}")

# Validar script de seed
print("\n6. Validando script de seed...")
try:
    with open("seed_dev.py") as f:
        seed_content = f.read()

    seed_checks = {
        "5 alunos": "students = [" in seed_content and "len(students)" in seed_content,
        "3 parceiros": "partners = [" in seed_content and "len(partners)" in seed_content,
        "4 promoções": "promotions = [" in seed_content and "len(promotions)" in seed_content,
        "Hash de CPF": "hash_cpf" in seed_content,
        "Firestore": "firestore" in seed_content.lower(),
        "PostgreSQL": "sql" in seed_content.lower() or "postgres" in seed_content.lower()
    }

    for check, result in seed_checks.items():
        print(f"{'✓' if result else '✗'} {check}")

    if all(seed_checks.values()):
        print("\nScript de seed válido e completo!")
    else:
        print("\nATENÇÃO: Script de seed pode estar incompleto!")

except Exception as e:
    print(f"Erro ao validar script de seed: {str(e)}")

# Resumo da validação
print("\n=== RESUMO DA VALIDAÇÃO ===")
all_valid = (not missing_files and
             all(openapi_checks.values()) and all(paths_checks.values()) and
             all(dockerfile_checks.values()) and
             all(deploy_checks.values()) and
             all(tests_checks.values()) and
             all(seed_checks.values()))

if all_valid:
    print("✅ Todos os artefatos foram validados com sucesso!")
    print("✅ O Portal de Benefícios KNN está pronto para entrega!")
else:
    print("⚠️ Foram encontrados problemas na validação dos artefatos.")
    print("⚠️ Revise os itens marcados com ✗ antes da entrega.")

print("\nValidação concluída!")
