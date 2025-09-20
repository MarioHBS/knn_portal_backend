
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
    'c3a5582f-ac24-4e4d-bb00-fdaa1da3bc59',
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
    '2026-09-18'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    '8463f29a-419f-45a0-951a-b0b92b65294d',
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
    '2026-03-17'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    'df6e93c7-44ee-428c-9bd9-fc43e3501af8',
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
    '2025-12-17'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    'dcf5f9c7-7436-48a1-bf5d-787cd3071c78',
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
    '2026-06-15'
);

INSERT INTO students (id, tenant_id, cpf_hash, nome_aluno, curso, ocupacao_aluno, email_aluno, celular_aluno, cep_aluno, bairro, complemento_aluno, nome_responsavel, email_responsavel, active_until)
VALUES (
    'be5c7758-09bd-4123-bbbc-868048c1da57',
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
    '2025-08-19'
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    '273d9e1b-a6a8-4ef5-898b-56f825c8b638',
    'knn-dev-tenant',
    '54e233ac80434697df497d54f4575c70242ec0ec22c202fc78b2fc09fedd51e7',
    'Livraria Cultura',
    'Livraria',
    'Av. Paulista, 2073 - São Paulo/SP',
    True
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    'ea1bd9c7-f3af-420d-b88b-f6ae0c364dd2',
    'knn-dev-tenant',
    '098b9dbf84b9c119493a4a1e428cb2a9a93939da3fcf2f5c0a28280cc7005bf2',
    'Restaurante Sabor & Arte',
    'Alimentação',
    'Rua Augusta, 1200 - São Paulo/SP',
    True
);

INSERT INTO partners (id, tenant_id, cnpj_hash, trade_name, category, address, active)
VALUES (
    'b0675270-d6a5-41d7-81e0-6733ae839c5c',
    'knn-dev-tenant',
    '906de17b19296dc3a9cf0ec225d112513caa44f31da6e63f4578692075bca5bf',
    'Cinema Lumière',
    'Entretenimento',
    'Shopping Cidade, Loja 42 - São Paulo/SP',
    True
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    '7ab7554a-6efd-4204-bd10-d844c8aedbf5',
    'knn-dev-tenant',
    '273d9e1b-a6a8-4ef5-898b-56f825c8b638',
    '20% de desconto em livros de idiomas',
    'discount',
    '2025-08-19T23:42:18.190055',
    '2025-11-17T23:42:18.190055',
    True,
    'both'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'dd745047-c3b7-480d-8955-de2f9fb7201d',
    'knn-dev-tenant',
    '273d9e1b-a6a8-4ef5-898b-56f825c8b638',
    'Brinde exclusivo na compra acima de R$ 100',
    'gift',
    '2025-09-03T23:42:18.190055',
    '2025-11-02T23:42:18.190055',
    True,
    'student'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'ad6bbf71-bf7e-4869-bc02-20318f34ce75',
    'knn-dev-tenant',
    'ea1bd9c7-f3af-420d-b88b-f6ae0c364dd2',
    '15% de desconto no almoço executivo',
    'discount',
    '2025-09-08T23:42:18.190055',
    '2025-12-07T23:42:18.190055',
    True,
    'employee'
);

INSERT INTO promotions (id, tenant_id, partner_id, title, type, valid_from, valid_to, active, target_profile)
VALUES (
    'd922090f-3a07-4316-8805-52ed4cb53222',
    'knn-dev-tenant',
    'b0675270-d6a5-41d7-81e0-6733ae839c5c',
    'Ingresso com 30% de desconto nas segundas e terças',
    'discount',
    '2025-09-13T23:42:18.190055',
    '2025-12-17T23:42:18.190055',
    True,
    'both'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '3bf62380-61e9-442f-a797-9cf081c612bf',
    'knn-dev-tenant',
    'dcf5f9c7-7436-48a1-bf5d-787cd3071c78',
    'b0675270-d6a5-41d7-81e0-6733ae839c5c',
    '3bb78535cc9555ff19fe3556aaa41c78a0a45c64d49ba2bc564507648a8e77a1',
    '2025-09-18T23:42:18.190055',
    '2025-09-17T23:42:18.190055'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    'a21013a0-9b51-4db9-bdc1-6789e7c60e63',
    'knn-dev-tenant',
    'df6e93c7-44ee-428c-9bd9-fc43e3501af8',
    'ea1bd9c7-f3af-420d-b88b-f6ae0c364dd2',
    '97c489b6c1231ecd9fac99df40e60cec000a70a057d5971fb520c578da8e8841',
    '2025-09-18T23:42:18.190055',
    '2025-09-17T23:42:18.190055'
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    'd5fc2d92-3512-45d2-bbe9-2f408c207686',
    'knn-dev-tenant',
    'df6e93c7-44ee-428c-9bd9-fc43e3501af8',
    'ea1bd9c7-f3af-420d-b88b-f6ae0c364dd2',
    '3fb836229505c02d85ef0286b0c93213db710766d841f00d91db5edaeade136b',
    '2025-09-18T23:42:18.190055',
    NULL
);

INSERT INTO validation_codes (id, tenant_id, student_id, partner_id, code_hash, expires, used_at)
VALUES (
    '80ab14f2-748a-4163-8ee2-933e4970c499',
    'knn-dev-tenant',
    'c3a5582f-ac24-4e4d-bb00-fdaa1da3bc59',
    '273d9e1b-a6a8-4ef5-898b-56f825c8b638',
    '24eb33c5f8f98314500b1c7f3fe403413c3b3fe0e4ae8ac5cc464dd2b686802c',
    '2025-09-19T23:42:18.190055',
    NULL
);

INSERT INTO redemptions (id, validation_code_id, value, used_at)
VALUES (
    'afabd313-230f-47ea-b507-629887822462',
    '3bf62380-61e9-442f-a797-9cf081c612bf',
    84.0,
    '2025-09-17T23:42:18.190055'
);

INSERT INTO redemptions (id, validation_code_id, value, used_at)
VALUES (
    '9d659420-d7db-4ca0-8151-71291a877e87',
    'a21013a0-9b51-4db9-bdc1-6789e7c60e63',
    77.0,
    '2025-09-17T23:42:18.190055'
);