
-- Criar tabelas
CREATE TABLE IF NOT EXISTS students (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    cpf_hash TEXT NOT NULL,
    nome_aluno TEXT NOT NULL,
    curso TEXT NOT NULL,
    ocupacao_aluno TEXT,
    email_aluno TEXT,
    celular_aluno TEXT,
    cep_aluno TEXT,
    bairro TEXT,
    complemento_aluno TEXT,
    nome_responsavel TEXT,
    email_responsavel TEXT,
    active_until DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS partners (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    cnpj_hash TEXT NOT NULL,
    trade_name TEXT NOT NULL,
    category TEXT NOT NULL,
    address TEXT NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS promotions (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    partner_id UUID NOT NULL REFERENCES partners(id),
    title TEXT NOT NULL,
    type TEXT NOT NULL,
    valid_from TIMESTAMP NOT NULL,
    valid_to TIMESTAMP NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    target_profile TEXT NOT NULL DEFAULT 'both'
);

CREATE TABLE IF NOT EXISTS validation_codes (
    id UUID PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id),
    partner_id UUID NOT NULL REFERENCES partners(id),
    code_hash TEXT NOT NULL,
    expires TIMESTAMP NOT NULL,
    used_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS redemptions (
    id UUID PRIMARY KEY,
    validation_code_id UUID NOT NULL REFERENCES validation_codes(id),
    value NUMERIC(10,2) NOT NULL,
    used_at TIMESTAMP NOT NULL
);

-- Limpar dados existentes
TRUNCATE TABLE redemptions CASCADE;
TRUNCATE TABLE validation_codes CASCADE;
TRUNCATE TABLE promotions CASCADE;
TRUNCATE TABLE partners CASCADE;
TRUNCATE TABLE students CASCADE;
    

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    'd0811aff-b710-420f-aeef-b6eed5206b17',
    'knn-dev-tenant',
    '3a74ca7993e0bc436448e089faf10944ec2a89d1bce08f81886ae0d42fb7d50b',
    'Ana Silva',
    'ADVANCED 1',
    'Estudante',
    'ana.silva@exemplo.com',
    '(11) 99999-1234',
    '01310-100',
    'Bela Vista',
    'Apto 101',
    NULL,
    NULL,
    '2026-08-27'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    '84595448-fd5f-41df-84d8-d5069f3446e0',
    'knn-dev-tenant',
    '14809a752d7cbd7e9b26a597d80b745caaf553dfe48d0ac143ca15c86dc285d6',
    'Bruno Santos',
    'TEENS 3',
    'Estudante',
    'bruno.santos@exemplo.com',
    '(11) 98888-5678',
    '04038-001',
    'Vila Olímpia',
    'Casa 15',
    'Maria Santos',
    'maria.santos@exemplo.com',
    '2026-02-23'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    '62d0fae2-349d-438c-b449-fdb0eb8b7601',
    'knn-dev-tenant',
    '8b1711db0009d91d529d84c6b391fe3ab766bd103e902b2d3427c31d3029b69a',
    'Carla Oliveira',
    'SEEDS 1',
    'Professora',
    'carla.oliveira@exemplo.com',
    '(11) 97777-9012',
    '05407-002',
    'Pinheiros',
    NULL,
    NULL,
    NULL,
    '2025-11-25'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    'b16f6ac5-a6c7-4363-8f2c-e7d0ff7bf56f',
    'knn-dev-tenant',
    '99aaf489c540b7ed54186c966f2bfbb11accddc4d622dc669516c8db14e7a28e',
    'Daniel Pereira',
    'TWEENS 4',
    'Engenheiro',
    'daniel.pereira@exemplo.com',
    '(11) 96666-3456',
    '01452-000',
    'Jardins',
    'Bloco B, Apto 502',
    NULL,
    NULL,
    '2026-05-24'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    '5e194bfd-5912-4f0d-840e-8fb32112bde6',
    'knn-dev-tenant',
    '07b94371acf6fa9a7d11c202a73f07ad086bf21e9af88d40f8af12ec014cd692',
    'Eduarda Costa',
    'KINDER 6A',
    'Estudante',
    NULL,
    '(11) 95555-7890',
    '02011-000',
    'Santana',
    'Casa 22',
    'Roberto Costa',
    'roberto.costa@exemplo.com',
    '2025-07-28'
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    'b275d5f8-db44-4876-befa-4980a031b95b',
    'knn-dev-tenant',
    '54e233ac80434697df497d54f4575c70242ec0ec22c202fc78b2fc09fedd51e7',
    'Livraria Cultura',
    'Livraria',
    'Av. Paulista, 2073 - São Paulo/SP',
    True
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    '948a9e5b-7bcf-4b55-90e2-490f19e82ace',
    'knn-dev-tenant',
    '098b9dbf84b9c119493a4a1e428cb2a9a93939da3fcf2f5c0a28280cc7005bf2',
    'Restaurante Sabor & Arte',
    'Alimentação',
    'Rua Augusta, 1200 - São Paulo/SP',
    True
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    'f5b2e761-9f23-48a0-b069-40fe9047ab88',
    'knn-dev-tenant',
    '906de17b19296dc3a9cf0ec225d112513caa44f31da6e63f4578692075bca5bf',
    'Cinema Lumière',
    'Entretenimento',
    'Shopping Cidade, Loja 42 - São Paulo/SP',
    True
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'c9979320-307e-4443-afdd-b274be2be6d4',
    'knn-dev-tenant',
    'b275d5f8-db44-4876-befa-4980a031b95b',
    '20% de desconto em livros de idiomas',
    'discount',
    '2025-07-28T16:09:19.391310',
    '2025-10-26T16:09:19.391310',
    True,
    'both'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'a0456e1e-32b1-4fa9-be3d-860284465eb9',
    'knn-dev-tenant',
    'b275d5f8-db44-4876-befa-4980a031b95b',
    'Brinde exclusivo na compra acima de R$ 100',
    'gift',
    '2025-08-12T16:09:19.391310',
    '2025-10-11T16:09:19.391310',
    True,
    'student'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    '2d8afc19-6550-4d4f-b7b9-813f8b1964f7',
    'knn-dev-tenant',
    '948a9e5b-7bcf-4b55-90e2-490f19e82ace',
    '15% de desconto no almoço executivo',
    'discount',
    '2025-08-17T16:09:19.391310',
    '2025-11-15T16:09:19.391310',
    True,
    'employee'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'cd6c6459-9768-40c1-9264-9aeb42be7572',
    'knn-dev-tenant',
    'f5b2e761-9f23-48a0-b069-40fe9047ab88',
    'Ingresso com 30% de desconto nas segundas e terças',
    'discount',
    '2025-08-22T16:09:19.391310',
    '2025-11-25T16:09:19.391310',
    True,
    'both'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '1a9b58d0-4541-4c3c-b6be-d80fa96f7737',
    'knn-dev-tenant',
    'b16f6ac5-a6c7-4363-8f2c-e7d0ff7bf56f',
    '948a9e5b-7bcf-4b55-90e2-490f19e82ace',
    '3bb78535cc9555ff19fe3556aaa41c78a0a45c64d49ba2bc564507648a8e77a1',
    '2025-08-27T16:09:19.391310',
    '2025-08-26T16:09:19.391310'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '40d99fdd-a322-4270-a047-0e980cb49264',
    'knn-dev-tenant',
    'b16f6ac5-a6c7-4363-8f2c-e7d0ff7bf56f',
    'b275d5f8-db44-4876-befa-4980a031b95b',
    '97c489b6c1231ecd9fac99df40e60cec000a70a057d5971fb520c578da8e8841',
    '2025-08-27T16:09:19.391310',
    '2025-08-26T16:09:19.391310'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    'fd4ca261-dda3-4194-999d-80f89473a8a7',
    'knn-dev-tenant',
    'd0811aff-b710-420f-aeef-b6eed5206b17',
    'b275d5f8-db44-4876-befa-4980a031b95b',
    '3fb836229505c02d85ef0286b0c93213db710766d841f00d91db5edaeade136b',
    '2025-08-27T16:09:19.391310',
    NULL
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '4cb70297-e354-453f-8891-5bcf2e7d3f5c',
    'knn-dev-tenant',
    'b16f6ac5-a6c7-4363-8f2c-e7d0ff7bf56f',
    'b275d5f8-db44-4876-befa-4980a031b95b',
    '24eb33c5f8f98314500b1c7f3fe403413c3b3fe0e4ae8ac5cc464dd2b686802c',
    '2025-08-28T16:09:19.391310',
    NULL
);

INSERT INTO redemptions (id, validation_code_id, value, used_at)
VALUES (
    '9a915493-1c3b-4004-8852-3fae6f4e5db9',
    '1a9b58d0-4541-4c3c-b6be-d80fa96f7737',
    28.0,
    '2025-08-26T16:09:19.391310'
);

INSERT INTO redemptions (id, validation_code_id, value, used_at)
VALUES (
    '5443b021-5d19-4b0a-b497-d3c5317aae81',
    '40d99fdd-a322-4270-a047-0e980cb49264',
    71.0,
    '2025-08-26T16:09:19.391310'
);