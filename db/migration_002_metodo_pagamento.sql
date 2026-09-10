-- Migração: introduz a tabela metodo_pagamento e uma FK em despesas.
--
-- SEGURA PARA RODAR EM UM BANCO COM DADOS: não apaga nenhuma linha, não
-- sobrescreve a coluna antiga (só renomeia ela pra guardar como histórico),
-- e é reexecutável (rodar duas vezes não quebra nada).
--
-- Como aplicar:
--   docker exec -i orcamento_postgres psql -U orcamento -d orcamento \
--       < db/migration_002_metodo_pagamento.sql
--
-- Depois de rodar, confira o resultado com:
--   SELECT forma_pagamento_texto_legado, metodo_pagamento_id
--   FROM despesas WHERE metodo_pagamento_id IS NULL;
-- (mostra as despesas cujo texto livre antigo não foi reconhecido
-- automaticamente — ver seção final deste arquivo)

BEGIN;

-- 1) Cria a tabela nova e semeia os métodos, sem sobrescrever se já existir
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

-- 2) Adiciona a coluna de FK nova em despesas (nullable — despesas antigas
--    cujo texto livre não bater com nenhum método conhecido ficam com
--    valor NULL aqui, em vez de travar a migração ou inventar um valor)
ALTER TABLE despesas
    ADD COLUMN IF NOT EXISTS metodo_pagamento_id INTEGER REFERENCES metodo_pagamento (id);

CREATE INDEX IF NOT EXISTS idx_despesas_metodo_pagamento
    ON despesas (metodo_pagamento_id);

-- 3) Backfill + rename da coluna antiga, tudo dentro de um bloco condicional
--    único: só executa se a coluna forma_pagamento ainda existir. Isso é o
--    que torna o script seguro para rodar mais de uma vez — na segunda
--    execução a condição é falsa (a coluna já foi renomeada) e nada aqui
--    dentro roda de novo, então não há erro de "coluna não existe".
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'despesas' AND column_name = 'forma_pagamento'
    ) THEN
        -- Tenta reconhecer o método a partir do texto livre antigo (a
        -- coluna forma_pagamento era digitada livremente pelo modelo,
        -- então cobre as variações mais prováveis, com e sem acento)
        UPDATE despesas d
        SET metodo_pagamento_id = mp.id
        FROM metodo_pagamento mp
        WHERE d.metodo_pagamento_id IS NULL
          AND d.forma_pagamento IS NOT NULL
          AND (
                (mp.nome = 'pix'      AND d.forma_pagamento ILIKE '%pix%')
             OR (mp.nome = 'debito'   AND (d.forma_pagamento ILIKE '%débito%' OR d.forma_pagamento ILIKE '%debito%' OR d.forma_pagamento ILIKE '%debit%'))
             OR (mp.nome = 'credito'  AND (d.forma_pagamento ILIKE '%crédito%' OR d.forma_pagamento ILIKE '%credito%' OR d.forma_pagamento ILIKE '%credit%'))
              OR (mp.nome = 'dinheiro' AND (d.forma_pagamento ILIKE '%dinheiro%' OR d.forma_pagamento ILIKE '%espécie%' OR d.forma_pagamento ILIKE '%especie%' OR d.forma_pagamento ILIKE '%cash%'))
              OR (mp.nome = 'boleto' AND d.forma_pagamento ILIKE '%boleto%')
              OR (mp.nome = 'debito_automatico' AND (d.forma_pagamento ILIKE '%débito automático%' OR d.forma_pagamento ILIKE '%debito automatico%' OR d.forma_pagamento ILIKE '%debit automatic%'))
              OR (mp.nome = 'faturamento' AND (d.forma_pagamento ILIKE '%faturamento%' OR d.forma_pagamento ILIKE '%fatura%'))
              OR (mp.nome = 'ted' AND d.forma_pagamento ILIKE '%ted%')
              OR (mp.nome = 'vale_refeicao' AND (d.forma_pagamento ILIKE '%vale refeição%' OR d.forma_pagamento ILIKE '%vale refeicao%' OR d.forma_pagamento ILIKE '%vale-refeição%' OR d.forma_pagamento ILIKE '%vale-refeicao%'))
              OR (mp.nome = 'vale_alimentacao' AND (d.forma_pagamento ILIKE '%vale alimentação%' OR d.forma_pagamento ILIKE '%vale alimentacao%' OR d.forma_pagamento ILIKE '%vale-alimentação%' OR d.forma_pagamento ILIKE '%vale-alimentacao%'))
              );

        -- Preserva a coluna antiga em vez de apagar — só renomeia, pra
        -- deixar claro que é histórico/legado e não é mais usada.
        ALTER TABLE despesas RENAME COLUMN forma_pagamento TO forma_pagamento_texto_legado;
    END IF;
END $$;

COMMIT;

-- Depois de aplicar, rode a query do topo deste arquivo pra ver quantas
-- despesas antigas não foram reconhecidas automaticamente. Se houver
-- poucas, você pode corrigir manualmente com algo como:
--
--   UPDATE despesas SET metodo_pagamento_id =
--       (SELECT id FROM metodo_pagamento WHERE nome = 'pix')
--   WHERE id = <id_da_despesa>;
--
-- A coluna forma_pagamento_texto_legado continua na tabela (não some),
-- então nenhum dado original é perdido mesmo que o reconhecimento
-- automático erre ou deixe algo de fora.
