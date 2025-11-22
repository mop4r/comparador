#!/usr/bin/env python3
"""
Teste da Interface Moderna em Modo Noturno
Versão simplificada para demonstração visual
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

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
    """Função de demonstração"""
    url = entry_url.get().strip()
    if not url:
        messagebox.showerror("Erro", "Insira a URL da wiki/base.")
        return

    pasta = filedialog.askdirectory(title="Escolha a pasta de saída")
    if not pasta:
        return

    btn_run.config(state="disabled")
    status_var.set("⏳ Processando...")
    root.update()
    
    # Simula processamento
    root.after(1000, lambda: status_var.set("✅ Concluído!"))
    root.after(1100, lambda: btn_run.config(state="normal"))
    root.after(1200, lambda: messagebox.showinfo("Sucesso", f"PDF seria gerado na pasta:\n\n{pasta}"))


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
entry_url.insert(0, "https://desk.animati.com.br/agent/animati/support-team/base-de-conhecimento/page#Solutions")

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

# Auto-close após captura de screenshot (para automação)
root.after(2000, lambda: None)  # Mantém janela aberta por 2 segundos

root.mainloop()
