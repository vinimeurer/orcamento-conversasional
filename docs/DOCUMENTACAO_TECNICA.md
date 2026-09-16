# Documentação Técnica — Orçamento Conversacional

Este documento assume que você **nunca rodou Docker antes** e explica cada passo, cada comando, e o que esperar como resultado de cada um. Para uma visão geral do projeto, veja o [README.md](README.md).

---

## Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Conseguir o token do bot no Telegram](#2-conseguir-o-token-do-bot-no-telegram)
3. [Conseguir a chave da API do Gemini](#3-conseguir-a-chave-da-api-do-gemini)
4. [Configurar o arquivo .env](#4-configurar-o-arquivo-env)
5. [Subir tudo com Docker](#5-subir-tudo-com-docker)
6. [Testar no Telegram](#6-testar-no-telegram)
7. [Referência completa de comandos](#7-referência-completa-de-comandos)
8. [Problemas comuns e como resolver](#8-problemas-comuns-e-como-resolver)
9. [O que cada arquivo do projeto faz](#9-o-que-cada-arquivo-do-projeto-faz)
10. [Detalhes de arquitetura](#10-detalhes-de-arquitetura)
11. [Banco de dados](#11-banco-de-dados)
12. [Referência das ferramentas (tools) do agente](#12-referência-das-ferramentas-tools-do-agente)
13. [Alternativa: instalação local (sem Docker)](#13-alternativa-instalação-local-sem-docker)
14. [Próximos passos do projeto](#14-próximos-passos-do-projeto)

---

## 1. Pré-requisitos

Só uma coisa precisa estar instalada na sua máquina. Você **não** precisa instalar Python, Postgres ou o Nanobot separadamente — tudo isso roda dentro dos containers.

### Docker Desktop (Windows/Mac) ou Docker Engine (Linux)

- **Windows ou Mac**: baixe e instale o Docker Desktop em
  https://www.docker.com/products/docker-desktop/ — depois de instalar, abra
  o aplicativo Docker Desktop e espere ele mostrar "Docker is running" (ícone
  fica verde/estável na bandeja do sistema).
- **Linux**: siga https://docs.docker.com/engine/install/ para a sua
  distribuição, e depois https://docs.docker.com/engine/install/linux-postinstall/
  para poder rodar `docker` sem `sudo`.

### Verificar se está tudo certo

Abra um terminal (PowerShell no Windows, Terminal no Mac/Linux) e rode:

```bash
docker --version
docker compose version
```

Você precisa ver duas linhas de versão, sem erro. Se `docker compose version` disser "unknown flag" ou não existir, você tem o Docker Compose antigo (v1, com hífen: `docker-compose`) — veja a seção [8](#8-problemas-comuns-e-como-resolver).

---

## 2. Conseguir o token do bot no Telegram

1. Abra o Telegram (celular ou desktop) e procure por **@BotFather** na
   busca. É o bot oficial do Telegram para criar outros bots — verifique que
   tem o selo de verificado.
2. Envie para ele: `/newbot`
3. Ele vai perguntar um **nome** para o seu bot. Pode ser qualquer coisa,
   ex: `Orçamento Conversacional`.
4. Depois ele pergunta um **username**. Esse precisa ser único em todo o
   Telegram e **tem que terminar em "bot"**, ex: `orcamento_seunome_bot`.
5. Se der certo, o BotFather responde uma mensagem parecida com esta:

   ```
   Done! Congratulations on your new bot. You will find it at
   t.me/orcamento_seunome_bot. You can now add a description...

   Use this token to access the HTTP API:
   7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

   Keep your token secure and store it safely...
   ```

6. Copie a linha do token inteira (o formato é `números:letras_e_números`).
   Você vai colar isso no arquivo `.env` no próximo passo.

Guarde esse token — ele dá controle total sobre o bot.

---

## 3. Conseguir a chave da API do Gemini

O Nanobot usa a API oficial do Google Gemini como modelo de linguagem.

1. Acesse https://aistudio.google.com/api-keys e faça login com sua conta
   Google.
2. Clique em **Create API key** (o Google cria um projeto automaticamente).
3. Copie a chave e cole no `.env` no próximo passo.

**Sobre custos:** não pede cartão. O **free tier** cobre os modelos
Flash/Flash-Lite com limites de requisições por minuto/dia (~10 req/min e
~250–1.500 req/dia dependendo do modelo) — folgado para este projeto. Os
modelos Pro são pagos. Tabela oficial:
https://ai.google.dev/gemini-api/docs/pricing

---

## 4. Configurar o arquivo .env

Copie o modelo de exemplo, se ainda não tiver feito:

```bash
cp .env.example .env
```

**Atenção**: arquivos que começam com ponto (`.env`) são "ocultos" por
padrão no Explorador de Arquivos do Windows, no Finder do Mac, e em `ls`
sem flags no Linux/Mac. Use `ls -la` para vê-lo no terminal, ou abra a
pasta pelo editor de texto.

Dentro do `.env`, troque estas duas linhas pelos valores reais:

```
TELEGRAM_TOKEN=coloque_seu_token_aqui      ← token do BotFather (seção 2)
GEMINI_API_KEY=coloque_sua_chave_aqui      ← chave do AI Studio (seção 3)
```

A variável `GEMINI_MODEL` define qual modelo usar (padrão:
`gemini-3.6-flash`). Só mexa se quiser trocar por outro ID válido da lista
oficial: https://ai.google.dev/gemini-api/docs/models

As outras variáveis (`POSTGRES_PASSWORD`, `DATABASE_URL`) já vêm com valores
que funcionam — não precisa mexer nelas para rodar em Docker.

Salve o arquivo.

---

## 5. Subir tudo com Docker

Com o terminal aberto **dentro da pasta `orcamento-conversacional`** (a que
tem o arquivo `docker-compose.yml`), rode:

```bash
docker compose up -d --build
```
(ou `make up`, que roda exatamente esse comando)

O que esse comando faz, em ordem:

| Etapa | O que acontece | Tempo aproximado |
|---|---|---|
| 1 | Baixa as imagens base (Postgres) da internet | 1–3 min (primeira vez) |
| 2 | Constrói (`--build`) a imagem do Nanobot (inclui o servidor MCP embutido) | 2–4 min (primeira vez) |
| 3 | Sobe o Postgres e aplica o `schema.sql` automaticamente | poucos segundos |
| 4 | Sobe o Nanobot, esperando o Postgres ficar pronto | poucos segundos |

Não há download nem execução de modelo na sua máquina: o Gemini roda na
nuvem do Google.

A flag `-d` ("detached") faz tudo rodar em segundo plano. As próximas vezes
que você rodar `docker compose up -d` (sem `--build`), sobe em segundos.

### Como saber se deu tudo certo

Rode:

```bash
docker compose ps
```
(ou `make ps`)

Você deve ver 2 serviços:

```
NAME                    IMAGE                    STATUS
orcamento_postgres      postgres:16-alpine       Up (healthy)
orcamento_nanobot       ...nanobot               Up
```

Confira também os logs do Nanobot — deve aparecer o MCP conectado:

```bash
docker compose logs nanobot
```
(ou `make logs`, que já acompanha em tempo real com `-f`)

Procure por linhas como:

```
MCP: registered tool 'mcp_orcamento_registrar_despesa' from server 'orcamento'
MCP: registered tool 'mcp_orcamento_listar_despesas' from server 'orcamento'
MCP: registered tool 'mcp_orcamento_resumo_por_categoria' from server 'orcamento'
MCP: registered tool 'mcp_orcamento_gerar_relatorio_pdf' from server 'orcamento'
MCP server 'orcamento': connected, 4 capabilities registered
✓ Health endpoint: http://127.0.0.1:18790/health
bot @seubot connected
```

Se o `orcamento_nanobot` aparecer como "Restarting" ou sumir da lista, veja
a seção [8. Problemas comuns](#8-problemas-comuns-e-como-resolver).

---

## 6. Testar no Telegram

1. No Telegram, procure pelo username do bot que você criou no BotFather
   (ex: `@orcamento_seunome_bot`) e abra uma conversa com ele.
2. Envie `/start`. Na primeira conversa, o Nanobot pode pedir um **código de
   pareamento** — ele aparece nos logs (`docker compose logs -f nanobot`,
   linha "Generated pairing code ..."). Envie esse código para o bot.
3. Envie algo como:

   ```
   Gastei 35 no almoço hoje, no pix
   ```

4. Em alguns segundos, o bot deve responder confirmando o registro, algo
   como:

   ```
   Registrado: R$ 35,00 em alimentação (almoço, no pix).
   ```

5. Para testar o relatório, envie algo como:

   ```
   Me manda o relatório de setembro
   ```

   Se você não informar o período, o agente vai perguntar — o período é
   obrigatório para gerar o relatório. Em alguns segundos, você recebe um
   PDF de 3 páginas anexado na conversa.

Se o bot não responder nada, veja a seção de problemas comuns abaixo.

---

## 7. Referência completa de comandos

Todos rodados dentro da pasta `orcamento-conversacional`.

| Tarefa | Comando | Atalho `make` |
|---|---|---|
| Subir tudo (constrói se necessário) | `docker compose up -d --build` | `make up` |
| Ver status dos containers | `docker compose ps` | `make ps` |
| Ver logs de tudo, em tempo real | `docker compose logs -f` | — |
| Ver logs só do Nanobot | `docker compose logs -f nanobot` | `make logs` |
| Parar tudo (mantendo os dados) | `docker compose down` | `make down` |
| Subir de novo depois de parar | `docker compose up -d` | — |
| Reiniciar só o Nanobot | `docker compose restart nanobot` | `make restart` |
| Reconstruir as imagens sem subir | `docker compose build` | `make build` |
| Apagar tudo, **inclusive os dados do banco** | `docker compose down -v` | `make reset` / `make clean` |
| Abrir um shell `psql` no banco | `docker exec -it orcamento_postgres psql -U orcamento -d orcamento` | `make view-db` |

`Ctrl+C` num comando de `logs -f` só interrompe a *visualização* — os
containers continuam rodando em segundo plano.

### Depois de editar arquivos

| Você editou... | Comando necessário | Por quê |
|---|---|---|
| `SOUL.md`, `AGENTS.md`, `config.docker.json` ou `.env` | `docker compose up -d nanobot` | Não precisa reconstruir — config e prompts são montados direto no container |
| `mcp_server/*.py` ou `db/connection.py` | `docker compose up -d --build nanobot` | Precisa reconstruir, porque o venv do MCP é criado na imagem |

### Explorando o banco manualmente

```bash
make view-db
```
(ou o comando completo: `docker exec -it orcamento_postgres psql -U orcamento -d orcamento`)

Dentro do `psql`, experimente:
```sql
\dt                    -- lista as tabelas
\d despesas            -- estrutura da tabela despesas

SELECT * FROM usuarios;
SELECT * FROM categorias;
SELECT * FROM metodo_pagamento;
SELECT * FROM despesas ORDER BY criado_em DESC LIMIT 20;

\q                     -- sai do psql
```

---

## 8. Problemas comuns e como resolver

### `Error: Environment variable 'GEMINI_API_KEY' referenced in config is not set`

O `.env` não tem a variável `GEMINI_API_KEY` definida. Abra o `.env`,
garanta que a linha existe (mesmo que com valor provisório) e rode
`docker compose up -d nanobot` de novo.

### `401`, `unauthorized` ou `invalid api key` nos logs do Nanobot

A `GEMINI_API_KEY` está errada, revogada ou com espaço extra. Gere uma nova
chave em https://aistudio.google.com/api-keys e atualize o `.env`.

### `429` ou erros de rate limit / quota

Você bateu no limite do free tier do Gemini (requisições por minuto ou por
dia). Opções: aguardar alguns minutos, trocar `GEMINI_MODEL` no `.env` para
um modelo Flash-Lite (limites maiores) e subir de novo, ou habilitar
billing na sua conta Google Cloud.

### `model not found` nos logs

O valor de `GEMINI_MODEL` não é um ID válido da Gemini API. Confira a lista
oficial em https://ai.google.dev/gemini-api/docs/models e corrija o `.env`.

### O bot não chama as tools / diz que não pode registrar

Rode `docker compose logs nanobot` e procure por:
- `MCP server 'orcamento': connected` — se não aparecer, houve falha ao
  iniciar o servidor MCP embutido; veja erros logo acima dessa linha;
- `Max iterations (...) reached` — significa que o modelo entrou em loop de
  tool-calls; o limite configurável está em
  `agents.defaults.maxToolIterations` do config.

### O agente pede o método de pagamento repetidamente / não registra

Desde a introdução da tabela `metodo_pagamento`, o campo é **obrigatório**
— o agente deve perguntar se você não informar como pagou. Se ele estiver
travando mesmo depois de você responder, confira se a resposta bate com um
dos métodos reconhecidos no `SOUL.md` (pix, débito, crédito, dinheiro,
boleto, débito automático, faturamento, TED, vale-refeição,
vale-alimentação) — qualquer outra coisa cai automaticamente em "outros".

### O relatório em PDF não chega / erro ao enviar

Confira nos logs se apareceu `detalhe_tecnico` no resultado da tool
`gerar_relatorio_pdf` — normalmente indica que o `TELEGRAM_TOKEN` não
chegou até o processo do servidor MCP (confira o bloco `env` do serviço
`orcamento` em `config.docker.json`) ou uma falha de rede pontual ao
chamar a API do Telegram.

### O bot não responde nada no Telegram

- Confira `docker compose logs -f nanobot` enquanto manda uma mensagem —
  deve aparecer alguma atividade no log no mesmo instante.
- Verifique se você completou o pareamento (seção 6, passo 2).
- Confira se não há **outra instância** do bot rodando com o mesmo token
  (local, em outro container, ou em outra máquina) — o Telegram só permite
  um processo fazendo `getUpdates` por vez; duas instâncias brigando geram
  um erro `Conflict: terminated by other getUpdates request` nos logs.

### `docker compose version` diz "unknown flag" ou não existe

Você tem o Docker Compose antigo (v1, com hífen: `docker-compose`). Atualize
o Docker Desktop, ou instale o plugin `docker-compose-plugin` separadamente
(Linux).

### "Docker fantasma": container antigo que não aparece no `docker ps`

Se você já teve mais de uma instalação de Docker na máquina (por exemplo,
Docker Desktop **e** um Docker Engine instalado via `apt` em algum momento),
pode existir um container antigo rodando num contexto diferente do que seu
terminal está usando agora. Sintoma: erro de `Conflict` do Telegram mesmo
com só um container aparecendo no `docker ps`. Diagnóstico:

```bash
docker context ls              # lista os contextos disponíveis
docker context use default     # troca para o contexto "de sistema"
docker ps -a                   # confira se aparece algo a mais aqui
```

---

## 9. O que cada arquivo do projeto faz

```
orcamento-conversacional/
├── .env                         # SUAS credenciais (token do Telegram, chave
│                                 #   do Gemini, senha do banco). Lido
│                                 #   automaticamente pelo docker compose.
├── .env.example                 # Modelo de referência do .env, sem credenciais reais.
├── docker-compose.yml            # Define os containers (postgres, nanobot) e
│                                 #   a ordem de inicialização.
├── Makefile                     # Atalhos opcionais (make up, make logs, etc).
├── requirements.txt              # Dependências Python do servidor MCP
│                                 #   (mcp, psycopg2-binary, reportlab, matplotlib, requests).
│
├── db/
│   ├── schema.sql                # Cria as tabelas usuarios, categorias,
│   │                              #   metodo_pagamento, despesas. Aplicado
│   │                              #   automaticamente na 1ª subida do Postgres.
│   ├── migration_002_metodo_pagamento.sql
│   │                              #   Migração segura para quem já tinha um banco
│   │                              #   antes da tabela metodo_pagamento existir —
│   │                              #   não apaga nenhum dado, só reorganiza.
│   └── connection.py             # Pool de conexão com o Postgres e resolução
│                                 #   do usuário do Telegram para um id interno.
│
├── mcp_server/
│   ├── expense_tools.py          # As 4 ferramentas do agente (ver seção 12).
│   ├── dashboard_builder.py      # Página 1 do relatório: cabeçalho, cards de
│   │                              #   KPI, gastos por categoria, composição,
│   │                              #   evolução diária, principais gastos.
│   ├── dashboard_pagamento.py    # Página 2: mesmo panorama, por método de
│   │                              #   pagamento (distribuição, resumo, evolução
│   │                              #   multi-linha, categoria × método).
│   ├── dashboard_gastos_dia.py   # Página 3: tabela completa de gastos por dia,
│   │                              #   com paginação automática se não couber
│   │                              #   numa página só.
│   ├── dash_style.py             # Paleta de cores e nomes de exibição para
│   │                              #   categorias e métodos de pagamento.
│   ├── icons.py                  # ~24 ícones vetoriais desenhados direto no
│   │                              #   PDF (sem depender de fonte de ícone externa).
│   └── Dockerfile                # Imagem standalone opcional do MCP server
│                                  #   (modo HTTP — não é o modo usado em produção).
│
└── nanobot_config/
    ├── config.json                # Config do Nanobot para rodar FORA do Docker
    │                              #   (instalação local — ver seção 13). MCP via
    │                              #   stdio relativo à raiz do projeto.
    ├── config.docker.json         # Config ativa quando roda via `docker compose up`.
    │                              #   MCP via stdio em /opt/mcpvenv (venv isolado).
    ├── Dockerfile                 # Constrói a imagem do Nanobot: instala o
    │                              #   nanobot-ai + o venv isolado /opt/mcpvenv
    │                              #   com as dependências do servidor MCP.
    ├── SOUL.md                    # Instruções de COMO o agente se comporta:
    │                              #   extração de campos, quando perguntar em
    │                              #   vez de assumir, quando gerar relatório.
    ├── AGENTS.md                  # Regras gerais complementares (idioma, uso
    │                              #   de tools, tratamento de erro).
    └── USER.md                    # Perfil do usuário — preenchido automaticamente
                                    #   pelo Nanobot com o tempo.
```

---

## 10. Detalhes de arquitetura

- **Modelo de linguagem**: Google Gemini via API oficial
  (`providers.gemini`). O modelo é escolhido pela variável `GEMINI_MODEL`
  no `.env` (padrão: `gemini-3.6-flash`). Nada roda de modelo local — essa
  foi uma mudança deliberada em relação à ideia original do projeto (que
  previa um modelo local via Ollama), motivada por simplicidade de
  infraestrutura.
- **Servidor MCP**: roda como subprocesso (stdio) dentro do próprio
  container do Nanobot, usando o venv isolado `/opt/mcpvenv`. Por que
  isolado? O SDK Python `mcp` 2.x usado pelas tools conflita com a versão
  (`mcp>=1.26,<2`) exigida pelo próprio `nanobot-ai`.
- **Por que dois arquivos de config do Nanobot?** `config.json` (para
  rodar localmente, fora do Docker) aponta o MCP server via *stdio*
  relativo à raiz do projeto. `config.docker.json` (usado dentro do
  Docker) usa caminhos absolutos do container (`/opt/mcp_server/...`) e o
  venv `/opt/mcpvenv/bin/python3`.
- **Proteção contra loops**: `agents.defaults.maxToolIterations: 6` limita
  quantas chamadas de tool seguidas o agente pode fazer num mesmo turno.
- **Geração do PDF**: cada página do relatório é desenhada com coordenadas
  absolutas via ReportLab (não com flowables automáticos), porque o layout
  do dashboard é específico o bastante para exigir controle total do grid.
  As três páginas são páginas físicas de PDF de verdade (`canvas.showPage()`
  entre cada uma) — não simulação de espaço em branco, então uma página
  nunca "vaza" elementos para a outra. Os gráficos (donut, linha) são
  gerados como imagem via Matplotlib e embutidos no PDF; o resto (cards,
  tabelas, ícones) é desenhado direto no canvas.
- **Envio do PDF**: a tool `gerar_relatorio_pdf` chama a API do Telegram
  diretamente (`sendDocument`) em vez de devolver o arquivo pelo protocolo
  MCP — decisão tomada porque o suporte do Nanobot a recursos binários via
  MCP não é bem documentado/testado, enquanto uma chamada HTTP direta é
  previsível.

---

## 11. Banco de dados

### Tabelas

| Tabela | Campos principais | Observações |
|---|---|---|
| `usuarios` | `id`, `telegram_id` (único), `nome`, `criado_em` | Um registro por usuário do Telegram |
| `categorias` | `id`, `nome` (único) | Conjunto fixo: alimentação, transporte, moradia, saúde, lazer, educação, compras, assinaturas, outros |
| `metodo_pagamento` | `id`, `nome` (único) | pix, débito, crédito, dinheiro, boleto, débito automático, faturamento, TED, vale-refeição, vale-alimentação, outros |
| `despesas` | `id`, `usuario_id` (FK), `valor`, `descricao`, `categoria_id` (FK), `metodo_pagamento_id` (FK, nullable), `data_despesa`, `mensagem_original`, `criado_em` | `valor` restrito a `> 0`; índices por `(usuario_id, data_despesa)`, `categoria_id` e `metodo_pagamento_id` |

`metodo_pagamento_id` é nullable no schema (embora obrigatório na tool de
registro) para acomodar despesas legadas de antes da coluna existir — veja
`db/migration_002_metodo_pagamento.sql`.

### Aplicando a migração em um banco já existente

Se você já tinha o projeto rodando antes da tabela `metodo_pagamento`
existir, **não** rode `schema.sql` por cima do banco atual. Use a migração,
que preserva todos os dados:

```bash
docker exec -i orcamento_postgres psql -U orcamento -d orcamento \
    < db/migration_002_metodo_pagamento.sql
```

Ela cria a tabela nova, tenta reconhecer o método de pagamento a partir do
texto livre antigo (quando existir), e renomeia (não apaga) a coluna
antiga para um nome de arquivo histórico.

---

## 12. Referência das ferramentas (tools) do agente

O agente tem acesso a 4 ferramentas, registradas via MCP:

| Tool | O que faz | Parâmetros obrigatórios |
|---|---|---|
| `registrar_despesa` | Registra uma despesa nova | `valor`, `descricao`, `categoria`, `metodo_pagamento` |
| `listar_despesas` | Lista despesas de um período, com total e quantidade | `data_inicio`, `data_fim` |
| `resumo_por_categoria` | Total e % de participação por categoria num período | `data_inicio`, `data_fim` |
| `gerar_relatorio_pdf` | Gera e envia o relatório em PDF (dashboard de 3 páginas) pelo Telegram | `data_inicio`, `data_fim` |

Em todas as tools que recebem período, o agente é instruído (via
`SOUL.md`) a **perguntar** a data em vez de assumir um período, caso o
usuário não informe.

O relatório gerado por `gerar_relatorio_pdf` tem 3 páginas, cada uma
desenhada por seu próprio módulo:

1. **Panorama por categoria** (`dashboard_builder.py`) — KPIs, gastos por
   categoria (barras), composição (donut), evolução diária, principais
   gastos, resumo textual automático.
2. **Panorama por método de pagamento** (`dashboard_pagamento.py`) —
   mesma estrutura, dimensionada por método de pagamento em vez de
   categoria, mais um gráfico de barras empilhadas cruzando categoria ×
   método.
3. **Tabela de gastos por dia** (`dashboard_gastos_dia.py`) — cada
   despesa do período, com data, descrição, método de pagamento,
   categoria e valor; paginada automaticamente se não couber numa única
   página física.

---

## 13. Alternativa: instalação local (sem Docker)

Se você preferir rodar Postgres/Nanobot direto na sua máquina em vez de em
containers (mais chato de configurar, mas mais fácil de depurar linha por
linha):

### 13.1. Subir só o Postgres em Docker

```bash
docker compose up -d postgres
```
(Isso sobe *só* o Postgres. O `schema.sql` é aplicado automaticamente.)

### 13.2. Instalar as dependências Python do servidor MCP

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Exporte as variáveis de ambiente no mesmo terminal:

```bash
export DATABASE_URL=postgresql://orcamento:orcamento@localhost:5432/orcamento
export TELEGRAM_TOKEN=seu_token_aqui
export GEMINI_API_KEY=sua_chave_aqui
export GEMINI_MODEL=gemini-3.6-flash
```

(No Windows PowerShell, use `$env:DATABASE_URL = "..."`, etc.)

### 13.3. Instalar e rodar o Nanobot

```bash
pip install -U nanobot-ai
```

Copie `nanobot_config/config.json` para `~/.nanobot/config.json`, e
`nanobot_config/SOUL.md` para `~/.nanobot/workspace/SOUL.md` (crie a pasta
`workspace` se ela não existir).

Rode a partir da raiz deste projeto (o caminho do MCP server no
`config.json` é relativo a esse diretório):

```bash
nanobot gateway --config nanobot_config/config.json --verbose
```

### Testar sem o Telegram (útil para depurar a extração)

```bash
nanobot agent -c nanobot_config/config.json -m "Paguei 120 no mercado no cartão hoje"
```

---

## 14. Próximos passos do projeto

1. Testar o fluxo ponta a ponta com mensagens reais e ajustar o `SOUL.md`
   conforme os erros de extração observados (linguagem informal,
   abreviações, valores ambíguos).
2. Implementar a camada de recomendações: consolidar os dados de
   `resumo_por_categoria` e enviar para uma LLM avançada via API.
3. Vincular automaticamente as despesas ao usuário do Telegram autenticado
   (hoje o `telegram_id` é passado pelo modelo ao chamar a tool — pendência
   de segurança conhecida).
4. Avaliação exploratória com usuários reais do público-alvo (18–29 anos).

---

## Aviso sobre validação

O pipeline foi validado em execução real com Docker: containers subindo,
MCP conectado via stdio com as 4 tools registradas, e inserções no Postgres
confirmadas via `psql`. A geração das 3 páginas do relatório foi validada
com dados simulados (incluindo paginação automática da página 3 com mais
de 80 despesas). A sintaxe do `docker-compose.yml` e dos JSONs de config é
verificada antes de cada subida.

Se algo travar exatamente no `docker compose up`, comece pela seção
[8. Problemas comuns](#8-problemas-comuns-e-como-resolver).