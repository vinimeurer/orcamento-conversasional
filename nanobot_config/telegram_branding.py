"""Aplica branding Orçamento Conversacional ao channel Telegram do nanobot.

Executado UMA vez no build do Docker, após `pip install nanobot-ai`.
Motivo: o texto do /start, o menu (BOT_COMMANDS) e o /help são hardcoded
no nanobot 0.3.0 e não têm opção oficial de config — ver:
- nanobot/channels/telegram/runtime.py::_on_start (~L1140)
- nanobot/channels/telegram/runtime.py::BOT_COMMANDS (~L424)
- nanobot/command/builtin.py::build_help_text (~L983)

O patch é idempotente e falha alto se o upstream mudar (para o upgrade
0.3.0 -> 0.3.5+ quebrar de forma visível, não silenciosa).
"""

from __future__ import annotations

import pathlib
import sys

START_MESSAGE_HTML = """👋 Olá! Bem-vindo ao <b>Orçamento Conversacional</b>
Sou seu assistente financeiro pessoal no Telegram.



💰 <b>1. REGISTRAR DESPESAS</b>
Escreva como você fala:
<blockquote>Gastei 35 no almoço no pix</blockquote>
<blockquote>Paguei 120 no mercado no crédito ontem</blockquote>
<blockquote>Paguei 200 da conta de luz dia 1 do mês passado no débito</blockquote>

🔍 <b>2. CONSULTAR GASTOS</b>
Pergunte por período ou categoria:
<blockquote>Quanto gastei em alimentação este mês?</blockquote>
<blockquote>Quanto gastei entre 01/08 e 15/08?</blockquote>

📄 <b>3. RELATÓRIO EM PDF</b>
Receba o dashboard completo:
<blockquote>Gera meu relatório de agosto</blockquote>



▶️ Para rever esta mensagem, envie <code>/help</code>"""

# Fallback sem formatação do /start (se o Telegram rejeitar o HTML).
START_MESSAGE_TEXT = """👋 Olá! Bem-vindo ao Orçamento Conversacional
Sou seu assistente financeiro pessoal no Telegram.



💰 1. REGISTRAR DESPESAS
Escreva como você fala:
- Gastei 35 no almoço no pix
- Paguei 120 no mercado no crédito ontem
- Paguei 200 da conta de luz dia 1 do mês passado no débito

🔍 2. CONSULTAR GASTOS
Pergunte por período ou categoria:
- Quanto gastei em alimentação este mês?
- Quanto gastei entre 01/08 e 15/08?

📄 3. RELATÓRIO EM PDF
Receba o dashboard completo:
- Gera meu relatório de agosto



▶️ Para rever esta mensagem, envie /help"""

# /help completo: boas-vindas + como usar + comandos.
# É o que o usuário vê ao digitar /help no Telegram (HTML) e nos
# outros canais (texto puro via build_help_text).
HELP_MESSAGE_HTML = """👋 Olá! Bem-vindo ao <b>Orçamento Conversacional</b>
Sou seu assistente financeiro pessoal no Telegram.



💰 <b>1. REGISTRAR DESPESAS</b>
Escreva como você fala:
<blockquote>Gastei 35 no almoço no pix</blockquote>
<blockquote>Paguei 120 no mercado no crédito ontem</blockquote>
<blockquote>Paguei 200 da conta de luz dia 1 do mês passado no débito</blockquote>

🔍 <b>2. CONSULTAR GASTOS</b>
Pergunte por período ou categoria:
<blockquote>Quanto gastei em alimentação este mês?</blockquote>
<blockquote>Quanto gastei entre 01/08 e 15/08?</blockquote>

📄 <b>3. RELATÓRIO EM PDF</b>
Receba o dashboard completo:
<blockquote>Gera meu relatório de agosto</blockquote>



💬 <b>COMANDOS</b>
<code>/new</code> — Começar uma nova conversa
<code>/stop</code> — Parar a resposta atual
<code>/history</code> — Ver as últimas mensagens
<code>/help</code> — Ver esta ajuda



▶️ Para rever esta mensagem, envie <code>/help</code>"""

HELP_MESSAGE_TEXT = """👋 Olá! Bem-vindo ao Orçamento Conversacional
Sou seu assistente financeiro pessoal no Telegram.



💰 1. REGISTRAR DESPESAS
Escreva como você fala:
- Gastei 35 no almoço no pix
- Paguei 120 no mercado no crédito ontem
- Paguei 200 da conta de luz dia 1 do mês passado no débito

🔍 2. CONSULTAR GASTOS
Pergunte por período ou categoria:
- Quanto gastei em alimentação este mês?
- Quanto gastei entre 01/08 e 15/08?

📄 3. RELATÓRIO EM PDF
Receba o dashboard completo:
- Gera meu relatório de agosto



💬 COMANDOS
/new — Começar uma nova conversa
/stop — Parar a resposta atual
/history — Ver as últimas mensagens
/help — Ver esta ajuda



▶️ Para rever esta mensagem, envie /help"""

BRANDING_MARKER = "# ORCAMENTO-CONVERSACIONAL-BRANDING"


def _site_file(*parts: str) -> pathlib.Path:
    import nanobot

    base = pathlib.Path(nanobot.__file__).resolve().parent
    path = base.joinpath(*parts)
    if not path.exists():
        raise SystemExit(f"[branding] arquivo não encontrado: {path}")
    return path


def patch_start_message(runtime_path: pathlib.Path) -> None:
    text = runtime_path.read_text(encoding="utf-8")
    old_block = '''        await update.message.reply_text(
            f"👋 Hi {user.first_name}! I'm nanobot.\\n\\n"
            "Send me a message and I'll respond!\\n"
            "Type /help to see available commands."
        )'''
    if "ORCAMENTO_START_MESSAGE_HTML" in text:
        print("[branding] /start já patcheado (HTML), pulando.")
        return
    if old_block not in text:
        raise SystemExit(
            "[branding] bloco _on_start original não encontrado — "
            "versão do nanobot mudou? Revise telegram_branding.py. "
            f"Arquivo: {runtime_path}"
        )
    new_block = '''        try:
            await update.message.reply_text(
                ORCAMENTO_START_MESSAGE_HTML, parse_mode="HTML"
            )
        except BadRequest:
            await update.message.reply_text(ORCAMENTO_START_MESSAGE_TEXT)'''
    text = text.replace(old_block, new_block)

    const_block = (
        f"{BRANDING_MARKER}\n"
        f'ORCAMENTO_START_MESSAGE_HTML = """\n{START_MESSAGE_HTML}\n"""\n\n'
        f'ORCAMENTO_START_MESSAGE_TEXT = """\n{START_MESSAGE_TEXT}\n"""\n\n\n'
    )
    # Insere após os imports (antes de "class TelegramChannel").
    anchor = "class TelegramChannel(BaseChannel):"
    if anchor not in text:
        raise SystemExit("[branding] anchor TelegramChannel não encontrado.")
    text = text.replace(anchor, const_block + anchor, 1)
    runtime_path.write_text(text, encoding="utf-8")
    print("[branding] /start patcheado (HTML + fallback).")


def patch_bot_commands(runtime_path: pathlib.Path) -> None:
    text = runtime_path.read_text(encoding="utf-8")
    if "ORCAMENTO_BOT_COMMANDS" in text:
        print("[branding] BOT_COMMANDS já patcheado, pulando.")
        return
    start = text.find("    BOT_COMMANDS = [")
    if start == -1:
        raise SystemExit("[branding] BOT_COMMANDS não encontrado.")
    end = text.find("]", start)
    if end == -1:
        raise SystemExit("[branding] fim de BOT_COMMANDS não encontrado.")
    new_menu = '''    BOT_COMMANDS = ORCAMENTO_BOT_COMMANDS  # branding aplicado abaixo'''
    text = text[:start] + new_menu + text[end + 1 :]

    const_block = (
        f"\n\n{BRANDING_MARKER}\n"
        "ORCAMENTO_BOT_COMMANDS = [\n"
        '    BotCommand("help", "Ver ajuda"),\n'
        '    BotCommand("new", "Começar nova conversa"),\n'
        '    BotCommand("stop", "Parar resposta atual"),\n'
        '    BotCommand("history", "Ver mensagens recentes"),\n'
        "]\n\n\n"
    )
    anchor = "class TelegramChannel(BaseChannel):"
    text = text.replace(anchor, const_block.strip("\n") + "\n\n\n" + anchor, 1)
    runtime_path.write_text(text, encoding="utf-8")
    print("[branding] BOT_COMMANDS (menu) patcheado.")


def patch_help_text(builtin_path: pathlib.Path) -> None:
    """O /help (outros canais) mostra boas-vindas + como usar + comandos.

    Aqui o build_help_text passa a retornar HELP_MESSAGE_TEXT para
    CLI/WebUI/outros canais não mostrarem mais a lista admin do nanobot.
    No Telegram vale o HTML via patch_help_handler.
    """
    text = builtin_path.read_text(encoding="utf-8")
    if "ORCAMENTO_HELP_MESSAGE" in text:
        print("[branding] /help já patcheado, pulando.")
        return
    old_fn_start = text.find("def build_help_text() -> str:")
    if old_fn_start == -1:
        raise SystemExit("[branding] build_help_text não encontrada.")
    # Fim da função = próxima linha que começa com "def " ou "class " no nível 0.
    tail = text[old_fn_start:]
    lines = tail.splitlines(keepends=True)
    # Linha 0 é o def; consome até a primeira linha não-indentada e não-vazia após o corpo.
    end_offset = None
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "":
            continue
        if not line.startswith(" ") and not line.startswith("\t"):
            end_offset = sum(len(line_) for line_ in lines[:i])
            break
    if end_offset is None:
        raise SystemExit("[branding] não consegui delimitar build_help_text.")
    old_fn = tail[:end_offset]
    if 'nanobot commands:' not in old_fn:
        raise SystemExit(
            "[branding] corpo de build_help_text mudou no upstream. Revise."
        )
    new_fn = (
        f'{BRANDING_MARKER}\n'
        f'ORCAMENTO_HELP_MESSAGE = """\n{HELP_MESSAGE_TEXT}\n"""\n\n\n'
        "def build_help_text() -> str:\n"
        '    """Build canonical help text shared across channels."""\n'
        "    return ORCAMENTO_HELP_MESSAGE\n"
        "\n\n"
    )
    text = text[:old_fn_start] + new_fn + text[old_fn_start + end_offset :]
    builtin_path.write_text(text, encoding="utf-8")
    print("[branding] /help patcheado (boas-vindas + comandos).")


def patch_help_handler(runtime_path: pathlib.Path) -> None:
    """Faz o /help no Telegram enviar o HTML completo (boas-vindas + comandos).

    O build_help_text (texto puro) continua valendo para CLI/WebUI e como
    fallback se o Telegram rejeitar o HTML.
    """
    text = runtime_path.read_text(encoding="utf-8")
    old_call = "        await update.message.reply_text(build_help_text())"
    if old_call not in text:
        if "ORCAMENTO_HELP_MESSAGE_HTML" in text:
            print("[branding] handler do /help já patcheado, pulando.")
            return
        raise SystemExit(
            "[branding] chamada do _on_help não encontrada — "
            "versão do nanobot mudou? Revise telegram_branding.py. "
            f"Arquivo: {runtime_path}"
        )
    new_call = '''        try:
            await update.message.reply_text(
                ORCAMENTO_HELP_MESSAGE_HTML, parse_mode="HTML"
            )
        except BadRequest:
            await update.message.reply_text(build_help_text())'''
    text = text.replace(old_call, new_call, 1)
    const_block = (
        f"{BRANDING_MARKER}-HELP\n"
        f'ORCAMENTO_HELP_MESSAGE_HTML = """\n{HELP_MESSAGE_HTML}\n"""\n\n\n'
    )
    anchor = "class TelegramChannel(BaseChannel):"
    if anchor not in text:
        raise SystemExit("[branding] anchor TelegramChannel não encontrado.")
    text = text.replace(anchor, const_block + anchor, 1)
    runtime_path.write_text(text, encoding="utf-8")
    print("[branding] handler do /help patcheado (HTML completo).")


def main() -> None:
    runtime_path = _site_file("channels", "telegram", "runtime.py")
    builtin_path = _site_file("command", "builtin.py")
    print(f"[branding] patching {runtime_path}")
    print(f"[branding] patching {builtin_path}")
    patch_start_message(runtime_path)
    # Re-lê porque o arquivo mudou no passo anterior.
    patch_bot_commands(_site_file("channels", "telegram", "runtime.py"))
    patch_help_handler(_site_file("channels", "telegram", "runtime.py"))
    patch_help_text(builtin_path)
    # Validação só por texto: importar runtime.py aqui exigiria a dep
    # opcional `python-telegram-bot`, que só é instalada no primeiro
    # `nanobot gateway` (via `nanobot plugins enable telegram`).
    runtime_text = _site_file("channels", "telegram", "runtime.py").read_text(
        encoding="utf-8"
    )
    builtin_text = _site_file("command", "builtin.py").read_text(encoding="utf-8")
    assert "ORCAMENTO_START_MESSAGE_HTML" in runtime_text
    assert "ORCAMENTO_START_MESSAGE_TEXT" in runtime_text
    assert "ORCAMENTO_HELP_MESSAGE_HTML" in runtime_text
    assert '<blockquote>' in runtime_text
    assert 'ORCAMENTO_START_MESSAGE_HTML, parse_mode="HTML"' in runtime_text
    assert 'ORCAMENTO_HELP_MESSAGE_HTML, parse_mode="HTML"' in runtime_text
    assert "Orçamento Conversacional" in runtime_text
    assert "ORCAMENTO_BOT_COMMANDS" in runtime_text
    assert 'BotCommand("start"' not in runtime_text
    assert "ORCAMENTO_HELP_MESSAGE" in builtin_text
    assert "Orçamento Conversacional" in builtin_text
    assert "COMANDOS" in builtin_text
    assert "Hi {user.first_name}! I'm nanobot." not in runtime_text
    assert "nanobot commands:" not in builtin_text
    print("[branding] OK: /start curto, /help completo, menu sem /start.")


if __name__ == "__main__":
    sys.exit(main())
