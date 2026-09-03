"""
Ícones vetoriais simples, desenhados direto no canvas do ReportLab.

Por que desenhar na mão em vez de usar um icon font: o ambiente de build
não tem acesso a baixar fontes de ícones (Font Awesome etc.), e os ícones
do template de referência são bem simples — dá pra aproximar com formas
geométricas básicas sem perder o efeito "dashboard limpo".

Todas as funções recebem (c, cx, cy, r, cor) e desenham centralizadas em
(cx, cy) dentro de um raio aproximado r, na cor "cor" (hex string).
"""
import math

from reportlab.lib import colors


def _cor(c, hexstr):
    c.setStrokeColor(colors.HexColor(hexstr))
    c.setFillColor(colors.HexColor(hexstr))


def icon_fork(c, cx, cy, r, cor):
    """Alimentação — garfo simplificado (3 dentes + cabo)."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    for dx in (-r * 0.35, 0, r * 0.35):
        c.line(cx + dx, cy + r * 0.55, cx + dx, cy + r * 0.05)
    c.line(cx - r * 0.35, cy + r * 0.05, cx + r * 0.35, cy + r * 0.05)
    c.line(cx, cy + r * 0.05, cx, cy - r * 0.55)


def icon_house(c, cx, cy, r, cor):
    """Moradia — casa simplificada (telhado + corpo)."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    p = c.beginPath()
    p.moveTo(cx - r * 0.5, cy - r * 0.05)
    p.lineTo(cx, cy + r * 0.55)
    p.lineTo(cx + r * 0.5, cy - r * 0.05)
    c.drawPath(p, stroke=1, fill=0)
    c.rect(cx - r * 0.35, cy - r * 0.55, r * 0.7, r * 0.5, stroke=1, fill=0)


def icon_car(c, cx, cy, r, cor):
    """Transporte — carro simplificado (corpo + 2 rodas)."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    c.roundRect(cx - r * 0.55, cy - r * 0.1, r * 1.1, r * 0.4, r * 0.15, stroke=1, fill=0)
    p = c.beginPath()
    p.moveTo(cx - r * 0.3, cy + r * 0.3)
    p.lineTo(cx - r * 0.15, cy + r * 0.55)
    p.lineTo(cx + r * 0.15, cy + r * 0.55)
    p.lineTo(cx + r * 0.3, cy + r * 0.3)
    c.drawPath(p, stroke=1, fill=0)
    c.circle(cx - r * 0.3, cy - r * 0.15, r * 0.14, stroke=1, fill=1)
    c.circle(cx + r * 0.3, cy - r * 0.15, r * 0.14, stroke=1, fill=1)


def icon_music(c, cx, cy, r, cor):
    """Lazer — nota musical simplificada."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    c.line(cx + r * 0.15, cy + r * 0.5, cx + r * 0.15, cy - r * 0.2)
    c.ellipse(cx - r * 0.15, cy - r * 0.45, cx + r * 0.15, cy - r * 0.1, stroke=1, fill=0)
    p = c.beginPath()
    p.moveTo(cx + r * 0.15, cy + r * 0.5)
    p.curveTo(cx + r * 0.55, cy + r * 0.4, cx + r * 0.5, cy + r * 0.1, cx + r * 0.15, cy + r * 0.15)
    c.drawPath(p, stroke=1, fill=0)


def icon_heart(c, cx, cy, r, cor):
    """Saúde — coração simplificado."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    p = c.beginPath()
    p.moveTo(cx, cy - r * 0.45)
    p.curveTo(cx - r * 0.75, cy + r * 0.15, cx - r * 0.45, cy + r * 0.6, cx, cy + r * 0.2)
    p.curveTo(cx + r * 0.45, cy + r * 0.6, cx + r * 0.75, cy + r * 0.15, cx, cy - r * 0.45)
    c.drawPath(p, stroke=1, fill=0)


def icon_bag(c, cx, cy, r, cor):
    """Compras — sacola simplificada (trapézio + alça em arco)."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    largura_baixo = r * 0.5
    largura_cima = r * 0.32
    y_baixo = cy - r * 0.5
    y_cima = cy + r * 0.15
    p = c.beginPath()
    p.moveTo(cx - largura_baixo, y_baixo)
    p.lineTo(cx - largura_cima, y_cima)
    p.lineTo(cx + largura_cima, y_cima)
    p.lineTo(cx + largura_baixo, y_baixo)
    p.close()
    c.drawPath(p, stroke=1, fill=0)
    c.arc(cx - r * 0.22, y_cima - r * 0.05, cx + r * 0.22, y_cima + r * 0.4,
          startAng=0, extent=180)


def icon_book(c, cx, cy, r, cor):
    """Educação — livro simplificado."""
    _cor(c, cor)
    c.setLineWidth(1.1)
    c.rect(cx - r * 0.5, cy - r * 0.45, r * 1.0, r * 0.9, stroke=1, fill=0)
    c.line(cx, cy - r * 0.45, cx, cy + r * 0.45)


def icon_gear(c, cx, cy, r, cor):
    """Serviços — engrenagem simplificada."""
    _cor(c, cor)
    c.setLineWidth(1.0)
    c.circle(cx, cy, r * 0.32, stroke=1, fill=0)
    c.circle(cx, cy, r * 0.12, stroke=1, fill=0)
    for i in range(8):
        ang = math.radians(i * 45)
        x1, y1 = cx + r * 0.35 * math.cos(ang), cy + r * 0.35 * math.sin(ang)
        x2, y2 = cx + r * 0.55 * math.cos(ang), cy + r * 0.55 * math.sin(ang)
        c.line(x1, y1, x2, y2)


def icon_refresh(c, cx, cy, r, cor):
    """Assinaturas — setas circulares simplificadas (recorrência)."""
    _cor(c, cor)
    c.setLineWidth(1.2)
    c.arc(cx - r * 0.45, cy - r * 0.45, cx + r * 0.45, cy + r * 0.45,
          startAng=20, extent=320)
    p = c.beginPath()
    p.moveTo(cx + r * 0.5, cy - r * 0.05)
    p.lineTo(cx + r * 0.2, cy - r * 0.05)
    p.lineTo(cx + r * 0.42, cy - r * 0.35)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def icon_dots(c, cx, cy, r, cor):
    """Outros — três pontos."""
    _cor(c, cor)
    for dx in (-r * 0.4, 0, r * 0.4):
        c.circle(cx + dx, cy, r * 0.12, stroke=0, fill=1)


def icon_calendar(c, cx, cy, r, cor):
    _cor(c, cor)
    c.setLineWidth(1.0)
    c.roundRect(cx - r * 0.5, cy - r * 0.45, r * 1.0, r * 0.85, r * 0.08, stroke=1, fill=0)
    c.line(cx - r * 0.5, cy + r * 0.15, cx + r * 0.5, cy + r * 0.15)
    c.line(cx - r * 0.25, cy + r * 0.4, cx - r * 0.25, cy + r * 0.55)
    c.line(cx + r * 0.25, cy + r * 0.4, cx + r * 0.25, cy + r * 0.55)


def icon_list(c, cx, cy, r, cor):
    _cor(c, cor)
    c.setLineWidth(1.6)
    for i, dy in enumerate((0.35, 0, -0.35)):
        largura = r * (0.7 if i != 2 else 0.45)
        c.line(cx - largura / 2, cy + r * dy, cx + largura / 2, cy + r * dy)


def icon_barchart(c, cx, cy, r, cor):
    _cor(c, cor)
    alturas = [0.35, 0.6, 0.9]
    larg = r * 0.28
    for i, h in enumerate(alturas):
        x = cx - r * 0.5 + i * (larg + r * 0.12)
        c.rect(x, cy - r * 0.5, larg, r * h, stroke=0, fill=1)


def icon_pie(c, cx, cy, r, cor_fundo, cor_fatia, fracao=0.24):
    """Ícone de pizza: círculo claro + fatia escura aproximada por polígono
    (mais previsível do que depender de arcTo para um glifo tão pequeno)."""
    _cor(c, cor_fundo)
    c.circle(cx, cy, r * 0.55, stroke=0, fill=1)

    _cor(c, cor_fatia)
    ang_inicio = math.pi / 2
    ang_fim = ang_inicio - fracao * 2 * math.pi
    passos = 12
    p = c.beginPath()
    p.moveTo(cx, cy)
    for i in range(passos + 1):
        ang = ang_inicio + (ang_fim - ang_inicio) * i / passos
        p.lineTo(cx + r * 0.55 * math.cos(ang), cy + r * 0.55 * math.sin(ang))
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def icon_star(c, cx, cy, r, cor):
    _cor(c, cor)
    pontos = []
    for i in range(10):
        ang = math.pi / 2 + i * math.pi / 5
        raio = r * 0.55 if i % 2 == 0 else r * 0.24
        pontos.append((cx + raio * math.cos(ang), cy + raio * math.sin(ang)))
    p = c.beginPath()
    p.moveTo(*pontos[0])
    for x, y in pontos[1:]:
        p.lineTo(x, y)
    p.close()
    c.drawPath(p, stroke=0, fill=1)


def icon_wallet(c, cx, cy, r, cor):
    _cor(c, cor)
    c.setLineWidth(1.1)
    c.roundRect(cx - r * 0.5, cy - r * 0.35, r * 1.0, r * 0.7, r * 0.1, stroke=1, fill=0)
    c.roundRect(cx + r * 0.05, cy - r * 0.12, r * 0.35, r * 0.24, r * 0.05, stroke=1, fill=0)
    c.circle(cx + r * 0.25, cy, r * 0.045, stroke=0, fill=1)


def icon_lightbulb(c, cx, cy, r, cor):
    _cor(c, cor)
    c.setLineWidth(1.0)
    c.circle(cx, cy + r * 0.1, r * 0.4, stroke=1, fill=0)
    c.rect(cx - r * 0.15, cy - r * 0.45, r * 0.3, r * 0.2, stroke=1, fill=0)
    c.line(cx - r * 0.1, cy - r * 0.25, cx + r * 0.1, cy - r * 0.25)