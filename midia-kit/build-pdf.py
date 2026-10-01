#!/usr/bin/env python3
"""Gera midia-kit-soraya-oliveira.pdf a partir de index.html.

Mesmo conteudo da pagina, adaptado para papel. As fontes do Google sao
baixadas e embutidas: sem isso o PDF sai sem acentos.

Uso:  python3 build-pdf.py
"""

import hashlib
import os
import re
import shutil
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(AQUI, ".build")
FONTES = os.path.join(BUILD, "fontes")
SAIDA = os.path.join(AQUI, "midia-kit-soraya-oliveira.pdf")

CSS_GOOGLE = ("https://fonts.googleapis.com/css2?family=Anton&family=Caveat:wght@600;700"
              "&family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,600;"
              "1,9..144,500;1,9..144,600&family=Karla:wght@400;500;700&display=swap")

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/130.0.0.0 Safari/537.36")

CHROMES = [
    os.environ.get("CHROME", ""),
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


def buscar(cmd, *args):
    r = subprocess.run([cmd, *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"falhou: {cmd} {' '.join(args)}\n{r.stderr[:400]}")
    return r.stdout


def achar_chrome():
    for c in CHROMES:
        if c and os.path.exists(c):
            return c
    for nome in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        c = shutil.which(nome)
        if c:
            return c
    raise SystemExit("Chrome/Chromium nao encontrado. Defina CHROME=/caminho/do/chrome.")


def baixar_fontes():
    os.makedirs(os.path.join(FONTES, "f"), exist_ok=True)
    css = buscar("curl", "-sS", "-A", UA, CSS_GOOGLE)
    if "@font-face" not in css:
        raise SystemExit("o CSS do Google Fonts voltou vazio — sem rede?")
    for url in sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css))):
        nome = hashlib.md5(url.encode()).hexdigest()[:10] + ".woff2"
        destino = os.path.join(FONTES, "f", nome)
        if not os.path.exists(destino):
            buscar("curl", "-sS", "-A", UA, "-o", destino, url)
        # caminho relativo ao proprio CSS, que fica em .build/fontes/
        css = css.replace(url, "f/" + nome)
    with open(os.path.join(FONTES, "fontes.css"), "w", encoding="utf-8") as f:
        f.write(css)


def montar_html():
    with open(os.path.join(AQUI, "index.html"), encoding="utf-8") as f:
        s = f.read()
    s = re.sub(r'<link rel="stylesheet" href="https://fonts\.googleapis\.com[^"]*">',
               '<link rel="stylesheet" href=".build/fontes/fontes.css">', s)
    with open(os.path.join(AQUI, "print.css"), encoding="utf-8") as f:
        s = s.replace("</head>", "<style>\n" + f.read() + "\n</style>\n</head>")
    caminho = os.path.join(AQUI, ".print.html")
    with open(caminho, "w", encoding="utf-8") as f:
        f.write(s)
    return caminho


def main():
    os.makedirs(BUILD, exist_ok=True)
    print("1/3 fontes...")
    baixar_fontes()
    print("2/3 html de impressao...")
    pagina = montar_html()
    print("3/3 pdf...")
    subprocess.run([achar_chrome(), "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", "--run-all-compositor-stages-before-draw",
                    "--virtual-time-budget=8000", f"--print-to-pdf={SAIDA}", pagina],
                   cwd=AQUI, capture_output=True, text=True)
    if not os.path.exists(SAIDA):
        raise SystemExit("o Chrome nao gerou o PDF")
    print(f"pronto: {SAIDA} ({os.path.getsize(SAIDA)//1024} KB)")


if __name__ == "__main__":
    sys.exit(main())
