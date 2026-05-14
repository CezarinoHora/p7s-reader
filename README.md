# 🔐 P7S Reader

Aplicação para leitura de arquivos `.p7s` (documentos assinados digitalmente), com extração de PDF, visualização e geração de relatório de assinatura.

## Funcionalidades

- **Extração de PDF** — Extrai o documento PDF embutido em arquivos `.p7s` (assinatura attached)
- **Visualização** — Visualize o PDF diretamente no navegador
- **Análise de Assinatura** — Exibe informações detalhadas do(s) signatário(s), certificado(s), cadeia de certificação
- **Suporte ICP-Brasil** — Extração de CPF/CNPJ de certificados brasileiros
- **Relatório** — Gera relatórios formatados em PDF ou TXT
- **Formatos** — Suporta `.p7s` nos formatos DER (binário) e PEM (Base64)

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
   - **Visualizar PDF** — Veja e baixe o documento extraído
   - **Assinatura Digital** — Analise os dados do signatário e certificado
   - **Relatório** — Gere e baixe relatórios em PDF ou TXT

## Estrutura do Projeto

```
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
