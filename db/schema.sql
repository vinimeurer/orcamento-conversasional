-- Schema inicial do Orçamento Conversacional
-- Foco desta etapa: registro e consulta simples de despesas.
-- Modelagem mais detalhada (índices adicionais, relatórios, views) fica
-- para a etapa de "Modelagem do banco de dados".

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

CREATE TABLE IF NOT EXISTS despesas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios (id),
    valor NUMERIC(12, 2) NOT NULL CHECK (valor > 0),
    descricao TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias (id),
    forma_pagamento TEXT,
    data_despesa DATE NOT NULL,
    mensagem_original TEXT,
    criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_despesas_usuario_data
    ON despesas (usuario_id, data_despesa);

CREATE INDEX IF NOT EXISTS idx_despesas_categoria
    ON despesas (categoria_id);
