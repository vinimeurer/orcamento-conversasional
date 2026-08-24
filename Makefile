# Atalhos para os comandos de Docker Compose mais usados neste projeto.
# Uso: make <alvo>   (ex: make up)
# Isso é só conveniência — todos os comandos abaixo também estão
# documentados em texto puro no README.md, caso você prefira digitá-los
# na mão ou não tenha `make` instalado.

.PHONY: up down restart logs ps build pull-model reset clean

up:
	docker compose up -d --build

down:
	docker compose down

restart:
	docker compose restart nanobot

logs:
	docker compose logs -f nanobot

ps:
	docker compose ps

build:
	docker compose build

pull-model:
	docker compose run --rm ollama-pull

# Remove containers e volumes (APAGA os dados do Postgres e o modelo baixado)
reset:
	docker compose down -v

clean: reset
