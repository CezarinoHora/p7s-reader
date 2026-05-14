# 🔐 P7S Reader

## 🚀 Leitura, extração e análise de documentos `.p7s` em uma interface simples

O **P7S Reader** é uma aplicação desenvolvida para facilitar a leitura de arquivos `.p7s` (documentos assinados digitalmente), permitindo extrair o PDF embutido, visualizar o conteúdo e gerar relatórios com informações da assinatura digital.

## 💡 Inspiração do Projeto

Esta aplicação nasceu a partir de um desafio real identificado no ambiente de trabalho da **SEFAZ-MT**, dentro do contexto de uma solução de **Automação em andamento via ServiceNow**.

A necessidade prática era tornar mais simples, rápida e acessível a análise de documentos assinados digitalmente no formato `.p7s`, reduzindo etapas manuais e apoiando fluxos de automação que dependem da extração e validação dessas informações.

## ✨ Principais Destaques

- **📄 Extração de PDF** - Extrai o documento PDF embutido em arquivos `.p7s` (assinatura attached)
- **👁️ Visualização integrada** - Permite visualizar o PDF diretamente no navegador
- **🔎 Análise da assinatura digital** - Exibe dados do(s) signatário(s), certificado(s) e cadeia de certificação
- **🇧🇷 Suporte ICP-Brasil** - Extrai CPF/CNPJ de certificados brasileiros quando disponíveis
- **🧾 Geração de relatório** - Cria relatórios formatados em PDF ou TXT
- **🧩 Compatibilidade de formatos** - Suporta `.p7s` nos formatos DER (binário) e PEM (Base64)

## Pré-requisitos

- Python 3.10 ou superior

## Instalação

```bash
# 1. Clone ou copie o projeto
cd p7s-reader

# 2. Crie um ambiente virtual (recomendado)
python -m venv venv

# No Linux/Mac:
source venv/bin/activate

# No Windows:
venv\Scripts\activate

# 3. Instale as dependências
pip install -r requirements.txt
```

## Como Executar

```bash
streamlit run app.py
```

A aplicação abrirá no navegador em `http://localhost:8501`.

## Como Usar

1. Clique em **"Browse files"** na barra lateral
2. Selecione um arquivo `.p7s`
3. Navegue pelas abas:
   - **Visualizar PDF** - Veja e baixe o documento extraído
   - **Assinatura Digital** - Analise os dados do signatário e certificado
   - **Relatório** - Gere e baixe relatórios em PDF ou TXT

## Estrutura do Projeto

```text
p7s-reader/
├── app.py                       # Interface Streamlit (ponto de entrada)
├── requirements.txt             # Dependências
├── README.md
├── src/
│   ├── __init__.py
│   ├── extractor.py             # Extração do PDF do .p7s
│   ├── signature_parser.py      # Análise da assinatura digital
│   └── report_generator.py      # Geração de relatórios
└── output/                      # Diretório para arquivos gerados
```

## Notas Importantes

- **Assinatura Detached**: Se o `.p7s` não contiver o PDF embutido (assinatura detached), a extração não será possível. Nesse caso, o PDF original deve ser fornecido separadamente.
- **Validação de Revogação**: A verificação CRL/OCSP (se o certificado foi revogado) não está implementada nesta versão.
- **ICP-Brasil**: A extração de CPF/CNPJ depende das extensões específicas presentes no certificado.

## Dependências

| Pacote | Uso |
|---|---|
| `streamlit` | Interface web |
| `asn1crypto` | Parsing da estrutura PKCS#7/CMS |
| `cryptography` | Suporte criptográfico |
| `PyMuPDF` | Manipulação de PDF |
| `reportlab` | Geração de relatórios em PDF |
| `Pillow` | Processamento de imagens |

## Licença

Este projeto está licenciado sob a licença MIT. Consulte o arquivo `LICENSE` para mais detalhes.
