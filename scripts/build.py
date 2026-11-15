"""Gera as páginas do site a partir dos textos em fonte/*.md.

Uso (na pasta girlfit-legal):  python3 -I scripts/build.py

Só usa a biblioteca padrão do Python. Entende o markdown que os textos usam: títulos,
parágrafos, listas (com um nível dentro), tabelas, negrito, links e linhas (---).
"""

import html
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE_URL = "https://pedrogoat23.github.io/girlfit-legal"
EMAIL = "girlfitapp@gmail.com"

PAGES = {
    "termos": ("Termos de Uso", "Regras de uso e assinatura do app GirlFit."),
    "privacidade": ("Política de Privacidade", "Como o app GirlFit cuida dos seus dados."),
}


def slug(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text).lower()
    table = str.maketrans("áàâãéêíóôõúüç", "aaaaeeiooouuc")
    text = text.translate(table)
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def inline(text: str) -> str:
    out = html.escape(text, quote=False)
    out = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)\s]+)\)",
        lambda m: f'<a href="{html.escape(m.group(2))}">{m.group(1)}</a>',
        out,
    )
    out = re.sub(
        r"(?<![\w@./\"])([\w.+-]+@[\w-]+\.[\w.]+\w)",
        r'<a href="mailto:\1">\1</a>',
        out,
    )
    return out


def cells(line: str) -> list[str]:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def render_table(lines: list[str]) -> str:
    head = cells(lines[0])
    rows = [cells(line) for line in lines[2:]]
    th = "".join(f"<th>{inline(h)}</th>" for h in head)
    body = []
    for row in rows:
        tds = "".join(
            f'<td data-label="{html.escape(re.sub(r"[*]", "", head[i]))}">{inline(c)}</td>'
            for i, c in enumerate(row)
        )
        body.append(f"<tr>{tds}</tr>")
    return f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_list(lines: list[str]) -> str:
    out = ["<ul>"]
    nested = False
    for line in lines:
        is_child = line.startswith("  - ")
        text = inline(line.strip()[2:])
        if is_child and not nested:
            out[-1] = out[-1].removesuffix("</li>")
            out.append("<ul>")
            nested = True
        elif not is_child and nested:
            out.append("</ul></li>")
            nested = False
        out.append(f"<li>{text}</li>")
    if nested:
        out.append("</ul></li>")
    out.append("</ul>")
    return "".join(out)


def render(md: str) -> tuple[str, str, list[tuple[str, str]], str]:
    lines = md.splitlines()
    title = ""
    updated = ""
    toc: list[tuple[str, str]] = []
    blocks: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line.startswith("# "):
            title = line[2:].strip()
            i += 1
            continue
        if line.startswith("**Última atualização:**"):
            updated = line.replace("**Última atualização:**", "").strip()
            i += 1
            continue
        if line.startswith("## ") or line.startswith("### "):
            level = 2 if line.startswith("## ") else 3
            text = line[level + 1 :].strip()
            anchor = slug(text)
            if level == 2:
                toc.append((anchor, text))
            blocks.append(f'<h{level} id="{anchor}">{inline(text)}</h{level}>')
            i += 1
            continue
        if line.strip() == "---":
            blocks.append("<hr>")
            i += 1
            continue
        if line.startswith("|"):
            group = []
            while i < len(lines) and lines[i].startswith("|"):
                group.append(lines[i])
                i += 1
            blocks.append(render_table(group))
            continue
        if line.startswith("- "):
            group = []
            while i < len(lines) and (lines[i].startswith("- ") or lines[i].startswith("  - ")):
                group.append(lines[i])
                i += 1
            blocks.append(render_list(group))
            continue
        group = []
        while i < len(lines) and lines[i].strip() and not re.match(r"(#|\||- |---)", lines[i]):
            group.append(inline(lines[i].strip()))
            i += 1
        blocks.append(f"<p>{'<br>'.join(group)}</p>")
    return title, updated, toc, "\n".join(blocks)


def shell(*, title: str, description: str, depth: int, current: str, body: str, path: str) -> str:
    up = "../" * depth
    labels = {"termos": "Termos", "privacidade": "Privacidade"}
    current_attr = ' aria-current="page"'
    nav = "".join(
        f'<a href="{up}{key}/"{current_attr if key == current else ""}>{labels[key]}</a>'
        for key in PAGES
    )
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(description)}">
<meta name="theme-color" content="#fff6f8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#140f13" media="(prefers-color-scheme: dark)">
<link rel="canonical" href="{BASE_URL}/{path}">
<link rel="icon" type="image/png" href="{up}assets/favicon.png">
<link rel="apple-touch-icon" href="{up}assets/icon.png">
<link rel="stylesheet" href="{up}assets/style.css">
</head>
<body>
<header class="top"><div class="top-inner">
<a class="brand" href="{up or './'}"><img src="{up}assets/icon.png" alt="" width="34" height="34"><span>GirlFit</span></a>
<nav aria-label="Páginas">{nav}</nav>
</div></header>
<main>
{body}
</main>
<footer>
<p>GirlFit · Pedro Antônio Marcos de Souza · Brasil<br>
Contato e privacidade: <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</footer>
</body>
</html>
"""


def build_page(key: str) -> None:
    name, description = PAGES[key]
    md = (ROOT / "fonte" / f"{key}.md").read_text(encoding="utf-8")
    if "A CONFIRMAR" in md:
        sys.exit(f"fonte/{key}.md ainda tem '[A CONFIRMAR]'. Resolva antes de publicar.")
    title, updated, toc, content = render(md)
    items = "".join(f'<li><a href="#{a}">{inline(t)}</a></li>' for a, t in toc)
    body = (
        f"<h1>{inline(title)}</h1>\n"
        f'<p class="updated">Última atualização: {html.escape(updated)}</p>\n'
        f'<details class="toc"><summary>Sumário</summary><ol>{items}</ol></details>\n'
        f"{content}"
    )
    out = ROOT / key / "index.html"
    out.parent.mkdir(exist_ok=True)
    out.write_text(
        shell(
            title=f"{name} · GirlFit",
            description=description,
            depth=1,
            current=key,
            body=body,
            path=f"{key}/",
        ),
        encoding="utf-8",
    )


def build_index() -> None:
    body = """<section class="hero">
<img src="assets/icon.png" alt="Ícone do app GirlFit" width="96" height="96">
<h1>GirlFit</h1>
<p>Treino feminino, dieta flexível e a Britney, sua assistente. Aqui estão as regras do app e como cuidamos dos seus dados.</p>
</section>
<div class="cards">
<a class="card" href="termos/"><strong>Termos de Uso</strong><span>Assinatura, renovação, cancelamento, avisos de saúde e regras de uso.</span></a>
<a class="card" href="privacidade/"><strong>Política de Privacidade</strong><span>Quais dados usamos, com quem compartilhamos e como excluir a sua conta.</span></a>
</div>
<p class="updated">Dúvidas, pedidos sobre seus dados ou suporte: <a href="mailto:girlfitapp@gmail.com">girlfitapp@gmail.com</a></p>"""
    (ROOT / "index.html").write_text(
        shell(
            title="GirlFit · Termos e Privacidade",
            description="Termos de Uso e Política de Privacidade do app GirlFit.",
            depth=0,
            current="",
            body=body,
            path="",
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    for page in PAGES:
        build_page(page)
    build_index()
    print("Páginas geradas: index.html, termos/index.html, privacidade/index.html")
