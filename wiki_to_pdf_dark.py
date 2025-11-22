#!/usr/bin/env python3
"""
Wiki → PDF (HelpNDoc / GitLab / Zoho Desk)
------------------------------------------
Gera um único PDF consolidado com o conteúdo de:
 - NetPACS / NetRIS (HelpNDoc)
 - GitLab Wiki
 - Base de Conhecimento Zoho Desk (com login manual)

Requisitos:
 pip install selenium beautifulsoup4 requests pdfkit
 E também:
 - Chrome + ChromeDriver compatível
 - wkhtmltopdf (https://wkhtmltopdf.org/downloads.html)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os, sys, time, pdfkit, requests, platform
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException
from urllib.parse import urlparse, urljoin
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ============================================================
# 🔹 CONFIGURAÇÕES
# ============================================================

class Config:
    """Configurações centralizadas da aplicação"""
    
    # URL padrão para o campo de entrada
    DEFAULT_URL = "https://desk.animati.com.br/agent/animati/support-team/base-de-conhecimento/page#Solutions"
    
    # Domínio Zoho Desk (pode ser customizado)
    ZOHO_DESK_DOMAIN = "desk.animati.com.br"
    
    @staticmethod
    def get_wkhtmltopdf_path():
        """Retorna o caminho do wkhtmltopdf baseado no sistema operacional"""
        system = platform.system()
        
        if system == "Windows":
            return r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
        elif system == "Linux":
            # Tenta encontrar no PATH ou localizações comuns
            common_paths = [
                "/usr/bin/wkhtmltopdf",
                "/usr/local/bin/wkhtmltopdf"
            ]
            for path in common_paths:
                if os.path.exists(path):
                    return path
            return "wkhtmltopdf"  # Assume que está no PATH
        elif system == "Darwin":  # macOS
            return "/usr/local/bin/wkhtmltopdf"
        else:
            return "wkhtmltopdf"  # Default - assume no PATH

# ============================================================
# 🔹 GITLAB WIKI
# ============================================================

def coletar_conteudo_gitlab(root_url, pasta_saida, delay=1.5):
    """Baixa todas as páginas da wiki GitLab pública e gera PDF único."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(root_url)
    time.sleep(delay)

    base = root_url.split("/-/wikis/")[0].rstrip("/")
    domain = urlparse(root_url).netloc

    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()

    for a in soup.select("a[href*='/-/wikis/']"):
        href = a["href"]
        href_full = urljoin(base, href)
        if "/-/wikis/" in href_full and domain in href_full:
            links.add(href_full)

    links = [l for l in sorted(links) if "/users/sign_in" not in l]
    if not links:
        raise RuntimeError("Nenhum link encontrado na wiki GitLab.")

    html_parts, toc_entries = [], []

    for i, link in enumerate(links, start=1):
        print(f"Baixando ({i}/{len(links)}): {link}")
        driver.get(link)
        time.sleep(1.2)
        if "/users/sign_in" in driver.current_url:
            print(f"⚠️ Ignorado (login obrigatório): {link}")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")
        content_div = (
            soup.find("div", class_="wiki-page-content")
            or soup.find("div", id="wiki-content")
            or soup.find("article")
            or soup.find("main")
        )

        if not content_div or len(content_div.get_text(strip=True)) < 30:
            print(f"⚠️ Ignorado (sem conteúdo reconhecível): {link}")
            continue

        # Remove menus, rodapés, etc.
        for sel in ["header", "footer", "nav", "div.page-sidebar", "div.comment"]:
            for tag in content_div.select(sel):
                tag.decompose()

        title = soup.find("h1") or soup.find("h2") or soup.title
        title_text = title.get_text(strip=True) if title else f"Tópico {i}"

        for img in content_div.find_all("img", src=True):
            src = img["src"]
            if not src.startswith("http"):
                img["src"] = urljoin(base, src)

        anchor = f"sec{i}"
        toc_entries.append((anchor, title_text))
        html_parts.append(f"<a id='{anchor}'></a><h1>{title_text}</h1>{content_div}<hr>")

    driver.quit()

    return gerar_pdf("Documentação GitLab Wiki", pasta_saida, toc_entries, html_parts)


# ============================================================
# 🔹 HELP N DOC (NETPACS / NETRIS)
# ============================================================

def coletar_conteudo_helpndoc(root_url, pasta_saida, delay=1.5):
    """Baixa todas as páginas HelpNDoc (NetPACS / NetRIS)."""
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(root_url)
    time.sleep(delay)

    base_domain = urlparse(root_url).netloc
    links = []

    try:
        driver.switch_to.frame("FrameTOC")
        soup_toc = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup_toc.select("a[href]"):
            href = a["href"]
            if href.startswith("http") and base_domain in href:
                links.append(href)
            else:
                links.append(urljoin(root_url, href))
        driver.switch_to.default_content()
    except Exception:
        driver.switch_to.default_content()

    if not links:
        soup_page = BeautifulSoup(driver.page_source, "html.parser")
        for a in soup_page.select("a[href$='.html']"):
            links.append(urljoin(root_url, a["href"]))

    if not links:
        raise RuntimeError("Nenhum link encontrado (HelpNDoc).")

    html_parts, toc_entries = [], []
    for i, link in enumerate(links, start=1):
        print(f"Baixando ({i}/{len(links)}): {link}")
        r = requests.get(link, timeout=10)
        r.encoding = "utf-8"
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.title.string.strip() if soup.title else f"Tópico {i}"
        content_div = soup.find("div", id="topic-content") or soup.body

        for img in content_div.find_all("img", src=True):
            src = img["src"]
            if not src.startswith("http"):
                img["src"] = urljoin(root_url, src)

        anchor = f"sec{i}"
        toc_entries.append((anchor, title))
        html_parts.append(f"<a id='{anchor}'></a><h1>{title}</h1>{content_div}<hr>")

    driver.quit()
    return gerar_pdf("Documentação HelpNDoc", pasta_saida, toc_entries, html_parts)


# ============================================================
# 🔹 ZOHO DESK (LOGIN MANUAL)
# ============================================================

def coletar_conteudo_zohodesk(root_url, pasta_saida, delay=2, debug=False):
    """Baixa todos os artigos da base de conhecimento do Zoho Desk (modo agente ou portal)."""
    chrome_options = Options()
    chrome_options.add_argument("--window-size=1400,900")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(root_url)

    messagebox.showinfo(
        "Login necessário",
        "Faça login no Zoho Desk e acesse a base de conhecimento.\n\n"
        "Quando a lista de artigos estiver visível, clique em OK."
    )

    # ==========================================================
    # 🔹 Detecta iframe da base
    # ==========================================================
    try:
        iframe = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "zd_setup_iframe"))
        )
        driver.switch_to.frame(iframe)
        print("✅ Mudou para o iframe da base de conhecimento.")
    except:
        print("ℹ️ Nenhum iframe detectado — continuando na página principal.")

    # ==========================================================
    # 🔹 Aguarda renderização da base de conhecimento
    # ==========================================================
    print("⏳ Aguardando renderização da base de conhecimento...")
    try:
        WebDriverWait(driver, 40).until(
            EC.presence_of_element_located((By.XPATH, "//a[contains(@href,'#Solutions/dv/')]"))
        )
        time.sleep(3)
    except Exception as e:
        print(f"⚠️ A base de conhecimento não carregou totalmente: {e}")

    # ==========================================================
    # 🔹 Coleta links de artigos
    # ==========================================================
    print("🔍 Coletando links de artigos...")
    soup = BeautifulSoup(driver.page_source, "html.parser")
    links = set()

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if "#Solutions/dv/" in href:
            if href.startswith("/"):
                href = f"https://{Config.ZOHO_DESK_DOMAIN}" + href
            links.add(href)

    print(f"✅ {len(links)} artigos detectados.\n")

    if not links:
        raise RuntimeError("Nenhum link de artigo encontrado. Verifique se a base foi carregada corretamente.")

    html_parts, toc_entries = [], []

    # ==========================================================
    # 🔹 Percorre e captura o conteúdo de cada artigo
    # ==========================================================
    for i, link in enumerate(sorted(links), start=1):
        print(f"📖 ({i}/{len(links)}) Acessando: {link}")
        driver.get(link)

        try:
            # Espera o container correto renderizar (modo agente Zoho)
            WebDriverWait(driver, 40).until(
                EC.presence_of_element_located((By.XPATH, "//div[@data-id='richcontent_area']"))
            )
            time.sleep(2)
        except Exception:
            print(f"⚠️ Conteúdo não apareceu a tempo: {link}")
            continue

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Extrai o título
        title_tag = (
            soup.find("span", {"data-id": "article_title_box"}) or
            soup.find("h1") or
            soup.title
        )
        title_text = title_tag.get_text(strip=True) if title_tag else f"Artigo {i}"

        # Extrai o corpo do artigo (estrutura atual do Zoho Animati)
        content_div = soup.find("div", {"data-id": "richcontent_area"})
        if not content_div:
            # fallback (modo público antigo)
            content_div = (
                soup.find("div", {"data-id": "article_answer_container"}) or
                soup.find("div", class_="articleBody") or
                soup.find("div", class_="answer-container")
            )

        if not content_div:
            print(f"⚠️ Ignorado (sem conteúdo detectado): {link}")
            continue

        # Remove elementos desnecessários
        for sel in ["header", "footer", "nav", "aside", ".feedbackSection", ".articleFeedback", ".commentSection"]:
            for tag in content_div.select(sel):
                tag.decompose()

        # Corrige imagens relativas
        for img in content_div.find_all("img", src=True):
            src = img["src"]
            if not src.startswith("http"):
                img["src"] = urljoin(root_url, src)

        # Debug opcional: salva HTML bruto do artigo
        if debug:
            debug_path = os.path.join(pasta_saida, f"debug_artigo_{i}.html")
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(str(content_div))

        # Adiciona ao HTML final
        anchor = f"art{i}"
        toc_entries.append((anchor, title_text))
        html_parts.append(f"<a id='{anchor}'></a><h1>{title_text}</h1>\n{content_div}\n<hr>")
        print(f"✅ Capturado: {title_text[:80]}...")

    driver.quit()

    # ==========================================================
    # 🔹 Geração do PDF
    # ==========================================================
    if not html_parts:
        raise RuntimeError("Nenhum artigo pôde ser capturado. Verifique se o conteúdo está visível após o login.")

    html_final = [
        "<html><head><meta charset='utf-8'>",
        "<style>body{font-family:Arial;padding:20px;}h1{border-bottom:1px solid #ccc;}img{max-width:100%;}</style>",
        "</head><body>",
        f"<h1>Base de Conhecimento - Zoho Desk</h1><div class='toc'><h2>Índice ({len(toc_entries)} artigos)</h2>"
    ]
    for anchor, title in toc_entries:
        html_final.append(f"<a href='#{anchor}'>{title}</a><br>")
    html_final.append("</div><hr>")
    html_final.extend(html_parts)
    html_final.append("</body></html>")

    temp_html = os.path.join(pasta_saida, "temp_zohodesk.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_final))

    pdf_path = os.path.join(pasta_saida, "ZohoDesk_BaseConhecimento.pdf")
    config = pdfkit.configuration(wkhtmltopdf=Config.get_wkhtmltopdf_path())

    pdfkit.from_file(temp_html, pdf_path, options={
        "enable-local-file-access": "",
        "encoding": "UTF-8",
        "page-size": "A4",
        "zoom": "1.1",
        "quiet": ""
    }, configuration=config)
    os.remove(temp_html)

    print(f"\n✅ PDF gerado com {len(toc_entries)} artigos.")
    return pdf_path, len(toc_entries)

# ============================================================
# 🔹 GERADOR DE PDF COMUM
# ============================================================

def gerar_pdf(titulo, pasta_saida, toc_entries, html_parts):
    """Gera um único PDF com índice clicável."""
    html_final = [
        "<html><head><meta charset='utf-8'>",
        "<style>body{font-family:Arial;padding:20px;}"
        "h1{border-bottom:1px solid #ccc;}img{max-width:100%;}</style>",
        "</head><body>",
        f"<h1>{titulo}</h1><div class='toc'><h2>Índice ({len(toc_entries)} tópicos)</h2>"
    ]
    for anchor, title in toc_entries:
        html_final.append(f"<a href='#{anchor}'>{title}</a><br>")
    html_final.append("</div><hr>")
    html_final.extend(html_parts)
    html_final.append("</body></html>")

    temp_html = os.path.join(pasta_saida, "temp_doc.html")
    with open(temp_html, "w", encoding="utf-8") as f:
        f.write("\n".join(html_final))

    pdf_path = os.path.join(pasta_saida, f"{titulo.replace(' ', '_')}.pdf")
    options = {
        "enable-local-file-access": "",
        "encoding": "UTF-8",
        "page-size": "A4",
        "zoom": "1.1",
        "quiet": ""
    }
    config = pdfkit.configuration(wkhtmltopdf=Config.get_wkhtmltopdf_path())
    pdfkit.from_file(temp_html, pdf_path, options=options, configuration=config)
    os.remove(temp_html)
    return pdf_path, len(toc_entries)


# ============================================================
# 🔹 DETECTOR AUTOMÁTICO
# ============================================================

def coletar_e_gerar_pdf(root_url, pasta_saida):
    if Config.ZOHO_DESK_DOMAIN in root_url:
        return coletar_conteudo_zohodesk(root_url, pasta_saida)
    elif "/-/wikis/" in root_url:
        return coletar_conteudo_gitlab(root_url, pasta_saida)
    else:
        return coletar_conteudo_helpndoc(root_url, pasta_saida)


# ============================================================
# 🔹 INTERFACE MODERNA COM MODO NOTURNO
# ============================================================

class ModernDarkUI:
    """Classe para gerenciar a interface moderna em modo noturno"""
    
    # Cores do tema escuro moderno
    COLORS = {
        'bg_primary': '#1a1a2e',      # Fundo principal escuro
        'bg_secondary': '#16213e',    # Fundo secundário
        'bg_tertiary': '#0f3460',     # Fundo terciário (cards)
        'accent': '#e94560',          # Cor de destaque (vermelho moderno)
        'accent_hover': '#ff577f',    # Cor de destaque no hover
        'text_primary': '#eaeaea',    # Texto principal
        'text_secondary': '#b8b8b8',  # Texto secundário
        'success': '#00d9ff',         # Cor de sucesso/info
        'border': '#2d3748',          # Cor de borda
        'input_bg': '#0f1419',        # Fundo de inputs
    }
    
    @staticmethod
    def apply_theme(root):
        """Aplica o tema escuro moderno à janela principal"""
        root.configure(bg=ModernDarkUI.COLORS['bg_primary'])
        
        # Estilo para ttk widgets
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuração do Frame
        style.configure('Dark.TFrame',
                       background=ModernDarkUI.COLORS['bg_primary'])
        
        # Configuração do Label
        style.configure('Dark.TLabel',
                       background=ModernDarkUI.COLORS['bg_primary'],
                       foreground=ModernDarkUI.COLORS['text_primary'],
                       font=('Segoe UI', 10))
        
        style.configure('Title.TLabel',
                       background=ModernDarkUI.COLORS['bg_primary'],
                       foreground=ModernDarkUI.COLORS['accent'],
                       font=('Segoe UI', 16, 'bold'))
        
        style.configure('Status.TLabel',
                       background=ModernDarkUI.COLORS['bg_secondary'],
                       foreground=ModernDarkUI.COLORS['success'],
                       font=('Segoe UI', 9),
                       padding=10,
                       relief='flat')
        
        # Configuração do Entry
        style.configure('Dark.TEntry',
                       fieldbackground=ModernDarkUI.COLORS['input_bg'],
                       background=ModernDarkUI.COLORS['input_bg'],
                       foreground=ModernDarkUI.COLORS['text_primary'],
                       bordercolor=ModernDarkUI.COLORS['border'],
                       lightcolor=ModernDarkUI.COLORS['border'],
                       darkcolor=ModernDarkUI.COLORS['border'],
                       insertcolor=ModernDarkUI.COLORS['text_primary'],
                       borderwidth=2,
                       relief='flat')
        
        # Configuração do Button
        style.configure('Accent.TButton',
                       background=ModernDarkUI.COLORS['accent'],
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('Segoe UI', 10, 'bold'),
                       padding=(20, 12))
        
        style.map('Accent.TButton',
                 background=[('active', ModernDarkUI.COLORS['accent_hover']),
                           ('disabled', '#555555')])
        
        return style


def on_run():
    url = entry_url.get().strip()
    if not url:
        messagebox.showerror("Erro", "Insira a URL da wiki/base.")
        return

    pasta = filedialog.askdirectory(title="Escolha a pasta de saída")
    if not pasta:
        return

    btn_run.config(state="disabled")
    status_var.set("⏳ Baixando conteúdo...")
    root.update()

    try:
        pdf_path, total = coletar_e_gerar_pdf(url, pasta)
        status_var.set("✅ Concluído!")
        messagebox.showinfo("Sucesso", f"PDF gerado com {total} tópicos:\n\n{pdf_path}")
    except Exception as e:
        messagebox.showerror("Erro", str(e))
        status_var.set("❌ Erro")
    finally:
        btn_run.config(state="normal")


# ============================================================
# 🔹 CRIAÇÃO DA JANELA PRINCIPAL
# ============================================================

root = tk.Tk()
root.title("Wiki → PDF | Modo Noturno")
root.geometry("800x500")
root.resizable(False, False)

# Aplicar tema moderno
style = ModernDarkUI.apply_theme(root)

# Frame principal com padding
main_frame = ttk.Frame(root, padding=30, style='Dark.TFrame')
main_frame.pack(fill="both", expand=True)

# Título da aplicação
title_label = ttk.Label(main_frame, 
                       text="📚 Wiki → PDF Converter", 
                       style='Title.TLabel')
title_label.pack(pady=(0, 10))

subtitle_label = ttk.Label(main_frame,
                          text="HelpNDoc • GitLab Wiki • Zoho Desk",
                          style='Dark.TLabel',
                          font=('Segoe UI', 9))
subtitle_label.pack(pady=(0, 30))

# Frame para a URL com espaçamento
url_frame = ttk.Frame(main_frame, style='Dark.TFrame')
url_frame.pack(fill="x", pady=10)

url_label = ttk.Label(url_frame, 
                     text="🔗 URL da Wiki/Base de Conhecimento:", 
                     style='Dark.TLabel')
url_label.pack(anchor="w", pady=(0, 8))

# Entry customizado para URL
entry_url = ttk.Entry(url_frame, 
                     width=70, 
                     style='Dark.TEntry',
                     font=('Segoe UI', 10))
entry_url.pack(fill="x", ipady=8)
entry_url.insert(0, Config.DEFAULT_URL)

# Espaçamento
spacer1 = ttk.Frame(main_frame, style='Dark.TFrame', height=30)
spacer1.pack()

# Botão principal com estilo moderno
btn_run = ttk.Button(main_frame, 
                    text="🚀 Baixar e Gerar PDF", 
                    command=on_run,
                    style='Accent.TButton')
btn_run.pack(pady=20, ipadx=30, ipady=10)

# Espaçamento
spacer2 = ttk.Frame(main_frame, style='Dark.TFrame', height=20)
spacer2.pack()

# Frame de status com fundo diferenciado
status_frame = ttk.Frame(main_frame, style='Dark.TFrame')
status_frame.pack(fill="x", pady=(10, 0))

# Label de status com estilo
status_var = tk.StringVar(value="✓ Pronto para processar")
status_label = ttk.Label(status_frame, 
                        textvariable=status_var, 
                        style='Status.TLabel')
status_label.pack(fill="x")

# Informações adicionais no rodapé
footer_frame = ttk.Frame(main_frame, style='Dark.TFrame')
footer_frame.pack(side="bottom", fill="x", pady=(20, 0))

footer_text = ttk.Label(footer_frame,
                       text="💡 Suporta detecção automática do tipo de documentação",
                       style='Dark.TLabel',
                       font=('Segoe UI', 8),
                       foreground=ModernDarkUI.COLORS['text_secondary'])
footer_text.pack()

# Customização adicional para messagebox (quando possível)
root.option_add('*Dialog.msg.font', 'Segoe UI 10')

root.mainloop()
