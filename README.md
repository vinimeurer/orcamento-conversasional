# Orçamento Conversacional — Pipeline Core

Sistema de registro de despesas por linguagem natural, via Telegram,
usando o **Google Gemini** (API oficial, modelo configurável via `.env`,
por padrão `gemini-3.6-flash`) como modelo de linguagem, orquestrado pelo
Nanobot, com os dados salvos em Postgres.

Este documento assume que você **nunca rodou Docker antes** e explica cada
passo, cada comando, e o que esperar como resultado de cada um.

---

## Índice

1. [O que você precisa ter instalado](#1-o-que-você-precisa-ter-instalado)
2. [Conseguir o token do bot no Telegram](#2-conseguir-o-token-do-bot-no-telegram)
3. [Conseguir a chave da API do Gemini](#3-conseguir-a-chave-da-api-do-gemini)
4. [Configurar o arquivo .env](#4-configurar-o-arquivo-env)
5. [Subir tudo com Docker](#5-subir-tudo-com-docker)
6. [Testar no Telegram](#6-testar-no-telegram)
7. [Comandos do dia a dia](#7-comandos-do-dia-a-dia)
8. [Problemas comuns e como resolver](#8-problemas-comuns-e-como-resolver)
9. [O que cada arquivo do projeto faz](#9-o-que-cada-arquivo-do-projeto-faz)
10. [Alternativa: instalação local (sem Docker)](#10-alternativa-instalação-local-sem-docker)
11. [Próximos passos do projeto](#11-próximos-passos-do-projeto)

---

## 1. O que você precisa ter instalado

Só uma coisa na sua máquina. Você **não** precisa instalar Python, Postgres
ou Nanobot separadamente — tudo isso roda dentro dos containers.

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

Você precisa ver duas linhas de versão, sem erro.

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

Guarde esse token.

---

## 3. Conseguir a chave da API do Gemini

O Nanobot usa a API oficial do Google Gemini como modelo de linguagem.

1. Acesse https://aistudio.google.com/api-keys e faça login com sua conta
   Google.
2. Clique em **Create API key** (o Google cria um projeto automaticamente).
3. Copie a chave e cole no `.env` no próximo passo.

Sobre custos: não pede cartão. O **free tier** cobre os modelos
Flash/Flash-Lite com limites de requisições por minuto/dia (~10 req/min e
~250–1.500 req/dia dependendo do modelo) — folgado para este projeto. Os
modelos Pro são pagos. Tabela oficial:
https://ai.google.dev/gemini-api/docs/pricing

---

## 4. Configurar o arquivo .env

O projeto já vem com um arquivo chamado **`.env`** na raiz da pasta
(`orcamento-conversacional/.env`). Ele é lido automaticamente pelo Docker
Compose — você não precisa renomear nada.

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

Procure por linhas como:

```
MCP: registered tool 'mcp_orcamento_registrar_despesa' from server 'orcamento'
MCP server 'orcamento': connected, 3 capabilities registered
✓ Health endpoint: http://127.0.0.1:18790/health
bot @seubot connected
```

Se o `orcamento_nanobot` aparecer como "Restarting" ou sumir da lista, veja
a seção [Problemas comuns](#8-problemas-comuns-e-como-resolver).

---

## 6. Testar no Telegram

1. No Telegram, procure pelo username do bot que você criou no BotFather
   (ex: `@orcamento_seunome_bot`) e abra uma conversa com ele.
2. Envie `/start`. Na primeira conversa, o Nanobot pode pedir um **código de
   pareamento** — ele aparece nos logs (`docker compose logs -f nanobot`,
   linha "Generated pairing code ..."). Envie esse código para o bot.
3. Envie algo como:

   ```
   Gastei 35 no almoço hoje
   ```

4. Em alguns segundos, o bot deve responder confirmando o registro, algo
   como:

   ```
   Registrado: R$ 35,00 em alimentação (almoço).
   ```

Se o bot não responder nada, veja a seção de problemas comuns abaixo.

---

## 7. Comandos do dia a dia

Todos rodados dentro da pasta `orcamento-conversacional`.

**Ver os logs de tudo, em tempo real:**
```bash
docker compose logs -f
```
(`Ctrl+C` para sair — isso só para de *mostrar* os logs, os containers
continuam rodando.)

**Ver os logs só do Nanobot (o mais útil para depurar conversas):**
```bash
docker compose logs -f nanobot
```

**Parar tudo (mantendo os dados salvos):**
```bash
docker compose down
```

**Subir de novo depois de parar:**
```bash
docker compose up -d
```

**Depois de editar `SOUL.md`, `config.docker.json` ou o `.env`** (não
precisa reconstruir a imagem; config e prompts são montados direto no
container):
```bash
docker compose up -d nanobot    # recria o container aplicando o novo .env
```

**Depois de editar `mcp_server/expense_tools.py` ou `db/connection.py`**
(precisa reconstruir, porque o venv do MCP é criado na imagem):
```bash
docker compose up -d --build nanobot
```

**Apagar absolutamente tudo, inclusive os dados do banco**
(útil se algo ficou corrompido e você quer recomeçar do zero):
```bash
docker compose down -v
```

**Entrar no banco de dados para ver as despesas registradas manualmente:**
```bash
make view-db
```
(ou o comando completo: `docker exec -it orcamento_postgres psql -U orcamento -d orcamento`)

Dentro do `psql`, experimente:
```sql
\dt              -- lista as tabelas
\d despesas      -- estrutura da tabela despesas

SELECT * FROM usuarios;
SELECT * FROM despesas;
SELECT * FROM categorias;
SELECT * FROM despesas ORDER BY criado_em DESC LIMIT 20;

\q               -- sai do psql
```

**Outros atalhos do Makefile** (`make` instalado por padrão no Mac/Linux):
`make up`, `make down`, `make logs`, `make restart`, `make ps`,
`make build`, `make reset`, `make view-db`.

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
um modelo Flash-Lite (limites maiores, ex: `gemini-3.1-flash-lite`) e subir
de novo, ou habilitar billing na sua conta Google Cloud.

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

### O bot não responde nada no Telegram

- Confira `docker compose logs -f nanobot` enquanto manda uma mensagem —
  deve aparecer alguma atividade no log no mesmo instante.
- Verifique se você completou o pareamento (seção 6, passo 2).

### `docker compose version` diz "unknown flag" ou não existe

Você tem o Docker Compose antigo (v1, com hífen: `docker-compose`). Atualize
o Docker Desktop, ou instale o plugin `docker-compose-plugin` separadamente
(Linux).

---

## 9. O que cada arquivo do projeto faz

```
orcamento-conversacional/
├── .env                         # SUAS credenciais (token do Telegram, chave
│                                #   do Gemini, senha do banco). Lido
│                                #   automaticamente pelo docker compose.
├── .env.example                 # Modelo de referência do .env, sem credenciais reais.
├── docker-compose.yml           # Define os containers (postgres, nanobot) e
│                                #   a ordem de inicialização.
├── Makefile                     # Atalhos opcionais (make up, make logs, etc).
├── requirements.txt             # Dependências Python do servidor MCP (mcp, psycopg2-binary).
│
├── db/
│   ├── schema.sql               # Cria as tabelas usuarios, categorias, despesas.
│   │                            #   Aplicado automaticamente na 1ª subida do Postgres.
│   └── connection.py            # Código Python que conecta no Postgres (pool de conexões)
│                                #   e resolve o usuário do Telegram para um id interno.
│
├── mcp_server/
│   ├── expense_tools.py         # As "ferramentas" que o agente de IA usa:
│   │                            #   registrar_despesa, listar_despesas, resumo_por_categoria.
│   │                            #   Roda via stdio DENTRO do container do Nanobot.
│   └── Dockerfile               # Imagem standalone opcional do MCP server (modo HTTP).
│
└── nanobot_config/
    ├── config.json              # Config do Nanobot para rodar FORA do Docker
    │                            #   (instalação local — ver seção 10). MCP via stdio
    │                            #   relativo à raiz do projeto.
    ├── config.docker.json       # Config do Nanobot para rodar DENTRO do Docker —
    │                            #   é este que está ativo quando você usa `docker compose up`.
    │                            #   MCP via stdio em /opt/mcpvenv (venv isolado).
    ├── Dockerfile               # Como construir a imagem do Nanobot. Instala o
    │                            #   nanobot + um venv isolado (/opt/mcpvenv) com as
    │                            #   dependências do servidor MCP.
    ├── SOUL.md                  # As instruções que dizem ao agente COMO se comportar:
    │                            #   como extrair valor/categoria/data de uma mensagem,
    │                            #   quando pedir confirmação, o que ele NÃO deve fazer ainda.
    ├── AGENTS.md                # Regras gerais de comportamento (idioma, uso de tools,
    │                            #   tratamento de erro). Complementa o SOUL.md.
    └── USER.md                  # Perfil do usuário — começa vazio, o Nanobot vai
                                  preenchendo automaticamente com o tempo.
```

### Detalhes da arquitetura atual

- **Modelo de linguagem**: Google Gemini via API oficial
  (`providers.gemini`). O modelo é escolhido pela variável `GEMINI_MODEL`
  no `.env` (padrão: `gemini-3.6-flash`). Nada roda de modelo local.
- **Servidor MCP**: roda como subprocesso (stdio) dentro do próprio
  container do Nanobot, usando o venv isolado `/opt/mcpvenv`. Por que
  isolado? O SDK Python `mcp` 2.x usado pelas tools conflita com a versão
  (`mcp>=1.26,<2`) exigida pelo próprio nanobot.
- **Proteção contra loops**: `agents.defaults.maxToolIterations: 6` limita
  quantas chamadas de tool seguidas o agente pode fazer num mesmo turno.

### Por que existem dois arquivos de config do Nanobot?

`config.json` (para rodar localmente, fora do Docker) aponta o MCP server
via *stdio* relativo à raiz do projeto. `config.docker.json` (usado dentro
do Docker) usa caminhos absolutos do container (`/opt/mcp_server/...`) e o
venv `/opt/mcpvenv/bin/python3`.

---

## 10. Alternativa: instalação local (sem Docker)

Se você preferir rodar Postgres/Nanobot direto na sua máquina em vez de em
containers (mais chato de configurar, mas mais fácil de depurar linha por
linha):

### 10.1. Subir só o Postgres em Docker

```bash
docker compose up -d postgres
```
(Isso sobe *só* o Postgres. O `schema.sql` é aplicado automaticamente.)

### 10.2. Instalar as dependências Python do servidor MCP

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

### 10.3. Instalar e rodar o Nanobot

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

## 11. Próximos passos do projeto

1. Testar o fluxo ponta a ponta com mensagens reais e ajustar o `SOUL.md`
   conforme os erros de extração observados (linguagem informal,
   abreviações, valores ambíguos).
2. Adicionar a tool de relatórios completos (comparação entre períodos,
   evolução de despesas).
3. Implementar a camada de recomendações: consolidar os dados de
   `resumo_por_categoria` e enviar para uma LLM avançada via API.
4. Vincular automaticamente as despesas ao usuário do Telegram autenticado
   (hoje o `telegram_id` é passado pelo modelo ao chamar a tool).

---

## Aviso sobre validação

O pipeline foi validado em execução real com Docker: containers subindo,
MCP conectado via stdio com as 3 tools registradas, e inserções no Postgres
confirmadas via `psql`. A sintaxe do `docker-compose.yml` e dos JSONs de
config é verificada antes de cada subida.

Se algo travar exatamente no `docker compose up`, comece pela seção
[8. Problemas comuns](#8-problemas-comuns-e-como-resolver).
