-- Schema do Orçamento Conversacional.
--
-- Este arquivo é para instalação NOVA (banco vazio) — é o que roda
-- automaticamente na primeira subida do container Postgres, via
-- docker-entrypoint-initdb.d. Se você já tem um banco com dados, NÃO rode
-- este arquivo por cima; use db/migration_002_metodo_pagamento.sql, que
-- atualiza o schema existente sem apagar nada.

CREATE TABLE IF NOT EXISTS usuarios (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    nome TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS categorias (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL
);

INSERT INTO categorias (nome) VALUES
    ('alimentacao'),
    ('transporte'),
    ('moradia'),
    ('saude'),
    ('lazer'),
    ('educacao'),
    ('compras'),
    ('assinaturas'),
    ('outros')
ON CONFLICT (nome) DO NOTHING;

CREATE TABLE IF NOT EXISTS metodo_pagamento (
    id SERIAL PRIMARY KEY,
    nome TEXT UNIQUE NOT NULL
);

INSERT INTO metodo_pagamento (nome) VALUES
    ('pix'),
    ('debito'),
    ('credito'),
    ('dinheiro'),
    ('boleto'),
    ('debito_automatico'),
    ('faturamento'),
    ('ted'),
    ('vale_refeicao'),
    ('vale_alimentacao'),
    ('outros')
ON CONFLICT (nome) DO NOTHING;

CREATE TABLE IF NOT EXISTS despesas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id),
    valor NUMERIC(12, 2) NOT NULL CHECK (valor > 0),
    descricao TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias (id),
    metodo_pagamento_id INTEGER REFERENCES metodo_pagamento (id),
    data_despesa DATE NOT NULL,
    mensagem_original TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_despesas_usuario_data
    ON despesas (usuario_id, data_despesa);

CREATE INDEX IF NOT EXISTS idx_despesas_categoria
    ON despesas (categoria_id);

CREATE INDEX IF NOT EXISTS idx_despesas_metodo_pagamento
    ON despesas (metodo_pagamento_id);