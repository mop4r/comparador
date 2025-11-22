# Wiki → PDF Converter - Modo Noturno

Uma interface moderna em modo noturno para converter documentação de wikis e bases de conhecimento em PDFs consolidados.

## 🎨 Características da Interface

- **Modo Noturno Moderno**: Interface escura elegante com paleta de cores cuidadosamente selecionada
- **Design Limpo**: Layout minimalista e intuitivo
- **Cores Vibrantes**: Destaques em vermelho moderno (#e94560) que contrastam perfeitamente com o fundo escuro
- **Tipografia Clara**: Uso de Segoe UI para melhor legibilidade
- **Feedback Visual**: Mensagens de status com ícones e cores indicativas

## 🎯 Paleta de Cores

- **Fundo Principal**: `#1a1a2e` - Azul escuro profundo
- **Fundo Secundário**: `#16213e` - Azul marinho escuro
- **Cor de Destaque**: `#e94560` - Vermelho moderno vibrante
- **Texto Principal**: `#eaeaea` - Branco suave
- **Cor de Sucesso**: `#00d9ff` - Ciano brilhante

## 📦 Requisitos

```bash
pip install selenium beautifulsoup4 requests pdfkit
```

Também necessário:
- **Chrome** + **ChromeDriver** compatível
- **wkhtmltopdf** (https://wkhtmltopdf.org/downloads.html)
- **Python 3.7+** com tkinter

## 🚀 Como Usar

1. Execute o script:
```bash
python3 wiki_to_pdf_dark.py
```

2. Cole a URL da wiki/base de conhecimento no campo de entrada

3. Clique em "🚀 Baixar e Gerar PDF"

4. Escolha a pasta de destino

5. Aguarde o processamento

## 🔍 Fontes Suportadas

- **HelpNDoc**: Documentação NetPACS / NetRIS
- **GitLab Wiki**: Wikis públicas do GitLab
- **Zoho Desk**: Base de conhecimento (requer login manual)

A detecção é automática baseada na URL fornecida.

## 📸 Preview

![Dark Mode Interface](https://github.com/user-attachments/assets/9481c17c-34fd-41c4-a320-88f19a5ac7b0)

## ✨ Melhorias Implementadas

### Interface Original vs. Nova Interface

**Antes:**
- Interface padrão do tkinter (cinza básico)
- Layout simples sem estilização
- Sem feedback visual claro

**Depois:**
- Tema escuro moderno completo
- Espaçamento e padding otimizados
- Ícones emoji para melhor identificação visual
- Estados de hover em botões
- Mensagens de status com cores indicativas
- Tipografia moderna e legível
- Layout responsivo e bem organizado

## 🛠️ Arquitetura

O código está organizado em módulos funcionais:

- **Coletores de Conteúdo**: Funções específicas para cada tipo de fonte
- **Gerador de PDF**: Função unificada para criar PDFs com índice
- **Interface Moderna**: Classe `ModernDarkUI` para gerenciar o tema
- **Detector Automático**: Identifica o tipo de fonte pela URL

## 📝 Notas

- O script mantém toda a funcionalidade original
- Apenas a interface foi modernizada
- Compatível com Windows, Linux e macOS
- Para Zoho Desk, é necessário fazer login manualmente quando solicitado

## 🎨 Customização

Para alterar as cores, edite a classe `ModernDarkUI.COLORS`:

```python
COLORS = {
    'bg_primary': '#1a1a2e',
    'accent': '#e94560',
    # ... outras cores
}
```

## 📄 Licença

Este projeto mantém a licença do repositório original.
