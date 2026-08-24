# Orçamento Conversacional — Pipeline Core

Sistema de registro de despesas por linguagem natural, via Telegram, usando
um modelo de linguagem local (Qwen 2.5 3B rodando no Ollama), orquestrado
pelo Nanobot, com os dados salvos em Postgres.

Este documento assume que você **nunca rodou Docker antes** e explica cada
passo, cada comando, e o que esperar como resultado de cada um.

---

## Índice

1. [O que você precisa ter instalado](#1-o-que-você-precisa-ter-instalado)
2. [Conseguir o token do bot no Telegram](#2-conseguir-o-token-do-bot-no-telegram)
3. [Configurar o arquivo .env](#3-configurar-o-arquivo-env)
4. [Subir tudo com Docker](#4-subir-tudo-com-docker)
5. [Testar no Telegram](#5-testar-no-telegram)
6. [Comandos do dia a dia](#6-comandos-do-dia-a-dia)
7. [Problemas comuns e como resolver](#7-problemas-comuns-e-como-resolver)
8. [O que cada arquivo do projeto faz](#8-o-que-cada-arquivo-do-projeto-faz)
9. [Alternativa: instalação local (sem Docker)](#9-alternativa-instalação-local-sem-docker)
10. [Próximos passos do projeto](#10-próximos-passos-do-projeto)

---

## 1. O que você precisa ter instalado

Só duas coisas na sua máquina. Você **não** precisa instalar Python, Postgres,
Ollama ou Nanobot separadamente — tudo isso roda dentro dos containers.

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

Você precisa ver duas linhas de versão, sem erro. A versão do Compose
precisa ser **2.20.0 ou mais nova** (esse projeto usa um recurso do
`depends_on` que só existe a partir dessa versão). Exemplo de saída esperada:

```
Docker version 27.3.1, build ce12230
Docker Compose version v2.29.7
```

Se `docker compose version` der erro "command not found", você provavelmente
tem o Docker Compose antigo (`docker-compose`, com hífen, versão 1.x) — nesse
caso é melhor atualizar o Docker Desktop / Docker Engine.

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

Guarde esse token — é a única credencial que você precisa para este projeto.

---

## 3. Configurar o arquivo .env

O projeto já vem com um arquivo chamado **`.env`** na raiz da pasta
(`orcamento-conversacional/.env`). Ele é lido automaticamente pelo Docker
Compose — você não precisa renomear nada.

**Atenção**: arquivos que começam com ponto (`.env`) são "ocultos" por
padrão no Explorador de Arquivos do Windows, no Finder do Mac, e em `ls`
sem flags no Linux/Mac. Se você extraiu o `.zip` e não está vendo o
`.env`, ele provavelmente está lá mesmo assim — veja como mostrar arquivos
ocultos:

- **Windows (Explorador de Arquivos)**: aba "Exibir" → marque "Itens ocultos".
- **Mac (Finder)**: com o Finder aberto, pressione `Cmd + Shift + .` (ponto).
- **Linux/Mac (terminal)**: use `ls -la` em vez de `ls`.

Ou, mais simples: abra a pasta pelo terminal e edite direto por lá:

```bash
cd orcamento-conversacional
nano .env
```

(`nano` é um editor de texto de terminal; salve com `Ctrl+O`, Enter, e saia
com `Ctrl+X`. Se preferir, abra o arquivo com o VS Code: `code .env`, ou
qualquer editor de texto comum.)

Dentro do `.env`, troque esta linha:

```
TELEGRAM_TOKEN=coloque_seu_token_aqui
```

pelo token real que você copiou do BotFather, por exemplo:

```
TELEGRAM_TOKEN=7123456789:AAHxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

As outras variáveis (`POSTGRES_PASSWORD`, `DATABASE_URL`) já vêm com valores
que funcionam — não precisa mexer nelas para rodar em Docker.

Salve o arquivo.

---

## 4. Subir tudo com Docker

Com o terminal aberto **dentro da pasta `orcamento-conversacional`** (a que
tem o arquivo `docker-compose.yml`), rode:

```bash
docker compose up -d --build
```

O que esse comando faz, em ordem:

| Etapa | O que acontece | Tempo aproximado |
|---|---|---|
| 1 | Baixa as imagens base (Postgres, Ollama) da internet | 1–3 min (primeira vez) |
| 2 | Constrói (`--build`) as imagens do servidor MCP e do Nanobot | 1–2 min (primeira vez) |
| 3 | Sobe o Postgres e aplica o `schema.sql` automaticamente | poucos segundos |
| 4 | Sobe o Ollama | poucos segundos |
| 5 | Baixa o modelo `qwen2.5:3b` (container `ollama-pull`, descartável) | **3–8 min (primeira vez)**, é um download de ~2 GB |
| 6 | Sobe o servidor MCP, esperando o Postgres ficar pronto | poucos segundos |
| 7 | Sobe o Nanobot, esperando tudo acima estar pronto | poucos segundos |

A flag `-d` ("detached") faz tudo rodar em segundo plano e devolve o
controle do terminal para você. A primeira execução pode levar uns 10
minutos no total, principalmente por causa do download do modelo. As
próximas vezes que você rodar `docker compose up -d` (sem `--build`, porque
as imagens já existem), sobe em segundos.

### Como saber se deu tudo certo

Rode:

```bash
docker compose ps
```

Você deve ver uma tabela com 5 serviços (o `ollama-pull` aparece como
"Exited (0)", o que é esperado — ele roda uma vez, baixa o modelo, e
termina):

```
NAME                    IMAGE                    STATUS
orcamento_postgres      postgres:16-alpine       Up (healthy)
orcamento_ollama        ollama/ollama:latest     Up (healthy)
orcamento_ollama_pull   ollama/ollama:latest     Exited (0)
orcamento_mcp           ...mcp-orcamento         Up (healthy)
orcamento_nanobot       ...nanobot               Up
```

Se `orcamento_nanobot` aparecer como "Restarting" ou some da lista, veja a
seção [Problemas comuns](#7-problemas-comuns-e-como-resolver) e rode:

```bash
docker compose logs nanobot
```

para ver o erro exato.

---

## 5. Testar no Telegram

1. No Telegram, procure pelo username do bot que você criou no BotFather
   (ex: `@orcamento_seunome_bot`) e abra uma conversa com ele.
2. Envie: `/start` (opcional, mas ajuda a confirmar que o bot está
   respondendo).
3. Envie algo como:

   ```
   Gastei 35 no almoço hoje
   ```

4. Em alguns segundos (a primeira resposta é mais lenta, porque o modelo
   local ainda está "esquentando"), o bot deve responder confirmando o
   registro, algo como:

   ```
   Registrado: R$ 35,00 em alimentação (almoço).
   ```

Se o bot não responder nada, veja a seção de problemas comuns abaixo.

---

## 6. Comandos do dia a dia

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

**Ver os logs só do servidor de tools (para depurar registro/consulta de despesas):**
```bash
docker compose logs -f mcp-orcamento
```

**Parar tudo (mantendo os dados salvos):**
```bash
docker compose down
```

**Subir de novo depois de parar:**
```bash
docker compose up -d
```

**Depois de editar `SOUL.md` ou `config.docker.json`** (não precisa
reconstruir a imagem, são montados direto no container):
```bash
docker compose restart nanobot
```

**Depois de editar `mcp_server/expense_tools.py`** (precisa reconstruir,
porque o código é copiado para dentro da imagem):
```bash
docker compose up -d --build mcp-orcamento
```

**Apagar absolutamente tudo, inclusive os dados do banco e o modelo baixado**
(útil se algo ficou corrompido e você quer recomeçar do zero):
```bash
docker compose down -v
```

**Entrar no banco de dados para ver as despesas registradas manualmente:**
```bash
docker exec -it orcamento_postgres psql -U orcamento -d orcamento
```
Dentro do `psql`, experimente:
```sql
SELECT * FROM despesas ORDER BY criado_em DESC LIMIT 10;
```
Para sair do `psql`: digite `\q` e Enter.

**Atalho opcional:** se você tem `make` instalado (padrão no Mac/Linux), o
projeto inclui um `Makefile` com os comandos mais usados: `make up`,
`make down`, `make logs`, `make restart`, `make ps`. É só conveniência —
por baixo rodam exatamente os comandos `docker compose` documentados aqui.

---

## 7. Problemas comuns e como resolver

### `docker compose up` reclama de "port is already allocated"

Alguma outra coisa na sua máquina já está usando a porta 5432 (Postgres) ou
11434 (Ollama). Ou você já tem um Postgres/Ollama instalado localmente
rodando. Duas opções:
- Pare o serviço que está usando a porta, ou
- Edite `docker-compose.yml` e troque, por exemplo, `"5432:5432"` para
  `"5433:5432"` (a porta da esquerda é a que fica exposta na sua máquina).

### `orcamento_nanobot` fica em "Restarting" ou cai

Rode `docker compose logs nanobot` e procure a última mensagem de erro.
Causas mais comuns:
- **`TELEGRAM_TOKEN` inválido ou ainda com o valor de exemplo**: confira o
  `.env`, garanta que colou o token certo, sem espaços extras, e rode
  `docker compose up -d --build nanobot` de novo.
- **Erro de conexão com `mcp-orcamento` ou `ollama`**: rode
  `docker compose ps` e confira se os dois estão "healthy". Se não
  estiverem, veja os logs deles individualmente.

### O bot não responde nada no Telegram

- Confira `docker compose logs -f nanobot` enquanto manda uma mensagem —
  deve aparecer alguma atividade no log no mesmo instante.
- Confira se o `orcamento_ollama_pull` realmente terminou com sucesso
  (`docker compose ps` deve mostrar "Exited (0)", não "Exited (1)" ou
  parecido). Se o download do modelo falhou, rode:
  ```bash
  docker compose up ollama-pull
  ```
  para tentar de novo.

### `docker compose version` diz "unknown flag" ou não existe

Você tem o Docker Compose antigo (v1, com hífen: `docker-compose`). Este
projeto usa um recurso (`service_completed_successfully` no `depends_on`)
que exige a v2.20+. Atualize o Docker Desktop, ou instale o plugin
`docker-compose-plugin` separadamente (Linux).

### O download do modelo (`ollama-pull`) está muito lento ou trava

É um download de ~2 GB direto dos servidores do Ollama — depende da sua
internet. Pode acompanhar o progresso com:
```bash
docker compose logs -f ollama-pull
```
Se travar de vez, `docker compose up ollama-pull` tenta de novo sem refazer
o que já foi baixado (o volume `orcamento_ollama_models` persiste).

### Quero trocar o modelo (usar um Qwen maior, por exemplo)

Edite duas coisas:
1. `docker-compose.yml`, no serviço `ollama-pull`, troque `qwen2.5:3b` pelo
   nome do modelo desejado (confira nomes válidos em
   https://ollama.com/library).
2. `nanobot_config/config.docker.json`, no campo `modelPresets.local.model`,
   troque para o mesmo nome.

Depois: `docker compose up -d --build`.

---

## 8. O que cada arquivo do projeto faz

```
orcamento-conversacional/
├── .env                         # SUAS credenciais (token do Telegram, senha do banco).
│                                  Lido automaticamente pelo docker compose.
├── .env.example                 # Modelo de referência do .env, sem credenciais reais.
├── docker-compose.yml           # Define os containers (postgres, ollama, ollama-pull,
│                                  mcp-orcamento, nanobot), como eles se conectam entre si,
│                                  e a ordem de inicialização.
├── Makefile                     # Atalhos opcionais (make up, make logs, etc).
├── requirements.txt             # Dependências Python do servidor MCP (mcp, psycopg2-binary).
│
├── db/
│   ├── schema.sql                # Cria as tabelas usuarios, categorias, despesas.
│   │                              Aplicado automaticamente na 1ª subida do Postgres.
│   └── connection.py             # Código Python que conecta no Postgres (pool de conexões)
│                                  e resolve o usuário do Telegram para um id interno.
│
├── mcp_server/
│   ├── expense_tools.py          # As "ferramentas" que o agente de IA usa:
│   │                              registrar_despesa, listar_despesas, resumo_por_categoria.
│   │                              Roda em modo HTTP dentro do Docker.
│   └── Dockerfile                # Como construir a imagem desse servidor.
│
└── nanobot_config/
    ├── config.json                # Config do Nanobot para rodar FORA do Docker
    │                              (instalação local — ver seção 9).
    ├── config.docker.json         # Config do Nanobot para rodar DENTRO do Docker —
    │                              é este que está ativo quando você usa `docker compose up`.
    ├── Dockerfile                 # Como construir a imagem do Nanobot.
    ├── SOUL.md                    # As instruções que dizem ao agente COMO se comportar:
    │                              como extrair valor/categoria/data de uma mensagem,
    │                              quando pedir confirmação, o que ele NÃO deve fazer ainda.
    ├── AGENTS.md                  # Regras gerais de comportamento (idioma, uso de tools,
    │                              tratamento de erro). Complementa o SOUL.md.
    └── USER.md                    # Perfil do usuário — começa vazio, o Nanobot vai
                                    preenchendo automaticamente com o tempo.
```

### Por que existem dois arquivos de config do Nanobot?

`config.json` (para rodar localmente, fora do Docker) aponta para
`localhost` e usa o servidor MCP via *stdio* (um subprocesso Python direto).
`config.docker.json` (usado dentro do Docker) aponta para os nomes dos
containers (`ollama`, `mcp-orcamento`) e usa o servidor MCP via *HTTP*,
porque dentro do Docker cada serviço é um processo isolado que só conversa
com os outros pela rede interna do Compose — não dá para chamar um
subprocesso de dentro de outro container.

---

## 9. Alternativa: instalação local (sem Docker)

Se você preferir rodar Postgres/Ollama/Nanobot direto na sua máquina em vez
de em containers (mais chato de configurar, mas mais fácil de depurar linha
por linha):

### 9.1. Subir só o Postgres em Docker

```bash
docker compose up -d postgres
```
(Isso sobe *só* o Postgres — não o Ollama, nem o Nanobot, nem o MCP server.
O `schema.sql` é aplicado automaticamente.)

### 9.2. Instalar o Ollama e baixar o modelo

```bash
# instale o Ollama: https://docs.ollama.com/
ollama pull qwen2.5:3b
ollama serve   # se não estiver rodando como serviço
```

### 9.3. Instalar as dependências Python do servidor MCP

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Exporte as variáveis de ambiente no mesmo terminal:

```bash
export DATABASE_URL=postgresql://orcamento:orcamento@localhost:5432/orcamento
export TELEGRAM_TOKEN=seu_token_aqui
```

(No Windows PowerShell, use `$env:DATABASE_URL = "..."` e
`$env:TELEGRAM_TOKEN = "..."`.)

### 9.4. Instalar e rodar o Nanobot

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

## 10. Próximos passos do projeto

1. Testar o fluxo ponta a ponta com mensagens reais e ajustar o `SOUL.md`
   conforme os erros de extração observados (linguagem informal,
   abreviações, valores ambíguos).
2. Adicionar a tool de relatórios completos (comparação entre períodos,
   evolução de despesas).
3. Implementar a camada de recomendações: consolidar os dados de
   `resumo_por_categoria` e enviar para uma LLM avançada via API.

---

## Aviso sobre validação

Não tenho um daemon Docker disponível no ambiente onde gerei este projeto,
então não consegui rodar `docker compose up` de ponta a ponta e ver os
containers subindo de verdade. O que validei diretamente:
- Sintaxe do `docker-compose.yml` (YAML válido, parseado com sucesso).
- O servidor MCP em modo HTTP: subi localmente e confirmei que responde
  `200 OK` no endpoint `/mcp`.
- Os arquivos `config.json` e `config.docker.json` são JSON válido.

Se algo travar exatamente no `docker compose up`, comece pela seção
[7. Problemas comuns](#7-problemas-comuns-e-como-resolver) — o candidato
mais provável é a versão do Docker Compose (precisa ser 2.20+).
