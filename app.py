"""
P7S Reader — Aplicação Streamlit
Lê arquivos .p7s, extrai o PDF embutido, visualiza e gera relatórios de assinatura.
"""

import streamlit as st
import base64
import tempfile
from pathlib import Path

from src.extractor import extract_pdf_from_p7s, is_valid_pdf
from src.signature_parser import (
    parse_p7s_signature,
    format_cpf,
    format_cnpj,
)
from src.report_generator import generate_pdf_report, generate_text_report

# ──────────────────────────────────────────────
# Configuração da página
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="P7S Reader",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# Sistema de Tema Claro/Escuro
# ──────────────────────────────────────────────
def get_theme_colors():
    """Retorna cores baseadas no tema atual"""
    # Detecta tema do navegador/usuário
    is_dark = st.session_state.get("theme_dark", False)
    
    if is_dark:
        return {
            "bg_primary": "#0f172a",
            "bg_secondary": "#1e293b",
            "bg_tertiary": "#334155",
            "text_primary": "#f1f5f9",
            "text_secondary": "#cbd5e1",
            "accent": "#6366f1",
            "accent_light": "#818cf8",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border": "#475569",
            "card_bg": "#1e293b",
            "sidebar_bg": "#0f172a",
        }
    else:
        return {
            "bg_primary": "#ffffff",
            "bg_secondary": "#f8fafc",
            "bg_tertiary": "#e2e8f0",
            "text_primary": "#1e293b",
            "text_secondary": "#64748b",
            "accent": "#6366f1",
            "accent_light": "#818cf8",
            "success": "#10b981",
            "warning": "#f59e0b",
            "error": "#ef4444",
            "border": "#cbd5e1",
            "card_bg": "#f8fafc",
            "sidebar_bg": "#f1f5f9",
        }

# Inicializar estado de tema
if "theme_dark" not in st.session_state:
    st.session_state.theme_dark = False

colors = get_theme_colors()

# ──────────────────────────────────────────────
# CSS customizado — Design Moderno
# ──────────────────────────────────────────────
st.markdown(
    f"""
    <style>
    :root {{
        --primary: {colors['accent']};
        --primary-light: {colors['accent_light']};
        --text-primary: {colors['text_primary']};
        --text-secondary: {colors['text_secondary']};
        --bg-primary: {colors['bg_primary']};
        --bg-secondary: {colors['bg_secondary']};
        --bg-tertiary: {colors['bg_tertiary']};
        --success: {colors['success']};
        --warning: {colors['warning']};
        --error: {colors['error']};
        --border: {colors['border']};
    }}
    
    * {{
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    
    .main-title {{
        font-size: 2.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, var(--primary), var(--primary-light));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }}
    
    .subtitle {{
        font-size: 1.1rem;
        color: var(--text-secondary);
        margin-top: 0.5rem;
        margin-bottom: 2rem;
        font-weight: 500;
    }}
    
    .status-ok {{
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(16, 185, 129, 0.05));
        color: {colors['success']};
        padding: 0.75rem 1.25rem;
        border-radius: 0.75rem;
        font-weight: 600;
        border-left: 4px solid {colors['success']};
        border: 1px solid rgba(16, 185, 129, 0.2);
        border-left: 4px solid {colors['success']};
    }}
    
    .status-warning {{
        background: linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(245, 158, 11, 0.05));
        color: {colors['warning']};
        padding: 0.75rem 1.25rem;
        border-radius: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(245, 158, 11, 0.2);
        border-left: 4px solid {colors['warning']};
    }}
    
    .status-info {{
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(99, 102, 241, 0.05));
        color: var(--primary);
        padding: 0.75rem 1.25rem;
        border-radius: 0.75rem;
        font-weight: 600;
        border: 1px solid var(--border);
        border-left: 4px solid var(--primary);
    }}
    
    .info-card {{
        background-color: {colors['card_bg']};
        border: 1.5px solid var(--border);
        border-radius: 1rem;
        padding: 1.5rem;
        margin-bottom: 1.25rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
    }}
    
    .info-card:hover {{
        border-color: var(--primary);
        box-shadow: 0 10px 25px -5px rgba(99, 102, 241, 0.1);
        transform: translateY(-2px);
    }}
    
    .info-card h3 {{
        color: var(--text-primary);
        margin-top: 0;
        margin-bottom: 0.5rem;
        font-size: 1.2rem;
        font-weight: 700;
    }}
    
    .info-card p {{
        color: var(--text-secondary);
        margin-bottom: 0;
        font-size: 0.95rem;
        line-height: 1.5;
    }}
    
    .field-label {{
        font-size: 0.75rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.4rem;
        font-weight: 700;
    }}
    
    .field-value {{
        font-size: 1.05rem;
        color: var(--text-primary);
        font-weight: 600;
        word-break: break-word;
    }}
    
    /* Sidebar */
    div[data-testid="stSidebar"] {{
        background-color: {colors['sidebar_bg']};
        border-right: 1px solid var(--border);
    }}
    
    /* Badges e componentes */
    .badge {{
        display: inline-block;
        padding: 0.4rem 0.8rem;
        background-color: var(--primary);
        color: white;
        border-radius: 0.5rem;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 0.5rem;
        margin-bottom: 0.5rem;
    }}
    
    /* Divider */
    hr {{
        border: none;
        height: 1px;
        background: var(--border);
        margin: 2rem 0;
    }}
    
    /* Buttons */
    .stButton > button {{
        border-radius: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        border: none;
        transition: all 0.3s ease;
    }}
    
    .stButton > button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 10px 20px -5px rgba(99, 102, 241, 0.3);
    }}
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 1rem;
    }}
    
    .stTabs [role="tab"] {{
        padding: 0.75rem 1.5rem;
        border-radius: 0.75rem;
        font-weight: 600;
        color: var(--text-secondary);
        border: 2px solid transparent;
    }}
    
    .stTabs [role="tab"][aria-selected="true"] {{
        color: var(--primary);
        border-bottom: 3px solid var(--primary);
        background-color: transparent;
    }}
    
    /* Expander */
    .streamlit-expanderHeader {{
        background-color: {colors['card_bg']};
        border: 1px solid var(--border);
        border-radius: 0.75rem;
        font-weight: 600;
        color: var(--text-primary);
    }}
    
    .streamlit-expanderHeader:hover {{
        background-color: {colors['bg_tertiary']};
        border-color: var(--primary);
    }}
    
    /* Inputs */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stFileUploader > div > div {{
        border-radius: 0.75rem;
        border: 1.5px solid var(--border);
        background-color: {colors['bg_secondary']};
        color: var(--text-primary);
    }}
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus {{
        border-color: var(--primary);
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1);
    }}
    
    /* Metrics */
    .stMetric {{
        background-color: {colors['card_bg']};
        padding: 1.5rem;
        border-radius: 1rem;
        border: 1px solid var(--border);
    }}
    
    .stMetric label {{
        color: var(--text-secondary);
        font-size: 0.9rem;
        font-weight: 600;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# Estado da sessão
# ──────────────────────────────────────────────
if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None
if "sig_report" not in st.session_state:
    st.session_state.sig_report = None
if "filename" not in st.session_state:
    st.session_state.filename = ""
if "raw_file_bytes" not in st.session_state:
    st.session_state.raw_file_bytes = None
if "action" not in st.session_state:
    st.session_state.action = None  # "extract_pdf", "analyze", "report"


# ──────────────────────────────────────────────
# Sidebar — Upload e ações
# ──────────────────────────────────────────────
with st.sidebar:
    # Header da Sidebar
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.markdown("## 🔐 P7S Reader")
        st.markdown("Leitor de assinaturas digitais")
    with col_header2:
        # Toggle de Tema
        theme_icon = "🌙" if not st.session_state.theme_dark else "☀️"
        if st.button(theme_icon, help="Alternar tema", use_container_width=True):
            st.session_state.theme_dark = not st.session_state.theme_dark
            st.rerun()
    
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "📁 Envie um arquivo .p7s",
        type=["p7s"],
        help="Arquivo PKCS#7/CMS com assinatura digital (formato .p7s)",
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        st.session_state.filename = uploaded_file.name
        st.session_state.raw_file_bytes = file_bytes
        
        # Status básico
        st.markdown("**Status do Arquivo:**")
        st.markdown(
            f'<div class="status-info">✓ {uploaded_file.name} carregado</div>',
            unsafe_allow_html=True,
        )
        
        if st.button("🗑️ Limpar arquivo", use_container_width=True):
            st.session_state.raw_file_bytes = None
            st.session_state.filename = ""
            st.session_state.pdf_bytes = None
            st.session_state.sig_report = None
            st.session_state.action = None
            st.rerun()
    else:
        if st.session_state.raw_file_bytes is not None:
            # Se havia arquivo carregado anteriormente
            st.markdown("**Status do Arquivo:**")
            st.markdown(
                f'<div class="status-info">✓ {st.session_state.filename} carregado</div>',
                unsafe_allow_html=True,
            )
            if st.button("🗑️ Limpar arquivo", use_container_width=True):
                st.session_state.raw_file_bytes = None
                st.session_state.filename = ""
                st.session_state.pdf_bytes = None
                st.session_state.sig_report = None
                st.session_state.action = None
                st.rerun()

    st.markdown("---")
    
    # Funcionalidades
    st.markdown("### ✨ Funcionalidades")
    st.markdown(
        """
        - 📄 Extração de PDF
        - 🔍 Análise de assinatura
        - 📊 Geração de relatórios
        - 🇧🇷 Suporte ICP-Brasil
        """
    )
    
    st.markdown("---")
    
    # Info footer
    st.markdown(
        """
        <div style="font-size: 0.85rem; color: var(--text-secondary); text-align: center;">
        <p><strong>P7S Reader</strong> v1.0</p>
        <p>Validação de assinaturas digitais com suporte a certificados brasileiros</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ──────────────────────────────────────────────
# Área principal — Interface baseada em Cards
# ──────────────────────────────────────────────
logo_col_left, logo_col_center, logo_col_right = st.columns([1, 2, 1])
with logo_col_center:
    st.image("assets/logocezarhora.png", width=420)

st.markdown('<p class="main-title">🔐 P7S Reader</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="subtitle">Leitura, extração e análise de documentos `.p7s` em uma interface simples - Desenvolvido por CezarHora®</p>',
    unsafe_allow_html=True,
)

# Se não há arquivo carregado
if st.session_state.raw_file_bytes is None:
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            """
            <div class="info-card">
                <h3>📄 Extração de PDF</h3>
                <p>Extraia automaticamente o documento PDF embutido em arquivos .p7s assinados digitalmente com segurança.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            """
            <div class="info-card">
                <h3>🔍 Análise Completa</h3>
                <p>Visualize informações detalhadas do signatário, certificado digital, cadeia de certificação e validade.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            """
            <div class="info-card">
                <h3>📊 Relatórios</h3>
                <p>Gere relatórios profissionais em PDF ou TXT com todos os dados da assinatura digital.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    
    st.markdown("---")
    
    # Empty state
    st.markdown(
        """
        <div style="text-align: center; padding: 3rem 1rem;">
        <h3 style="color: var(--text-secondary); margin-bottom: 1rem;">👈 Envie um arquivo .p7s para começar</h3>
        <p style="color: var(--text-secondary); font-size: 0.95rem;">
        Formatos suportados: <strong>.p7s DER (binário)</strong> e <strong>.p7s PEM (Base64)</strong>
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
else:
    # Arquivo carregado — Mostrar cards como botões
    
    # Botão voltar/reset (sempre disponível)
    col_reset1, col_reset2 = st.columns([0.8, 0.2])
    with col_reset2:
        if st.button("↩️ Voltar", use_container_width=True):
            st.session_state.action = None
            st.session_state.pdf_bytes = None
            st.session_state.sig_report = None
            st.rerun()
    
    st.markdown("---")
    
    # Se nenhuma ação foi selecionada, mostrar os 3 cards como botões
    if st.session_state.action is None:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Card 1: Extração de PDF
            st.markdown(
                """
                <div class="info-card" style="cursor: pointer;">
                    <h3>📄 Extração de PDF</h3>
                    <p>Extraia o documento PDF embutido no arquivo .p7s.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Extrair PDF", use_container_width=True, key="btn_extract"):
                st.session_state.action = "extract_pdf"
                st.rerun()
        
        with col2:
            # Card 2: Análise de Assinatura
            st.markdown(
                """
                <div class="info-card" style="cursor: pointer;">
                    <h3>🔍 Análise Completa</h3>
                    <p>Analise a assinatura digital e certificado do documento.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Analisar", use_container_width=True, key="btn_analyze"):
                st.session_state.action = "analyze"
                st.rerun()
        
        with col3:
            # Card 3: Gerar Relatório
            st.markdown(
                """
                <div class="info-card" style="cursor: pointer;">
                    <h3>📊 Relatórios</h3>
                    <p>Gere relatórios em PDF ou TXT com os dados da assinatura.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button("Gerar Relatório", use_container_width=True, key="btn_report"):
                st.session_state.action = "report"
                st.rerun()
    
    # ── Ação 1: Extração de PDF ──
    elif st.session_state.action == "extract_pdf":
        st.markdown("### 📄 Extração de PDF")
        st.markdown("---")
        
        with st.spinner("⏳ Extraindo PDF do arquivo .p7s..."):
            try:
                pdf_data = extract_pdf_from_p7s(st.session_state.raw_file_bytes)
                if pdf_data and is_valid_pdf(pdf_data):
                    st.session_state.pdf_bytes = pdf_data
                    st.success("✓ PDF extraído com sucesso!")
                elif pdf_data:
                    st.session_state.pdf_bytes = pdf_data
                    st.warning("⚠️ Conteúdo extraído, mas pode não ser um PDF válido")
                else:
                    st.error("❌ Falha ao extrair conteúdo do arquivo")
                    st.session_state.action = None
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Erro ao extrair PDF: {e}")
                st.session_state.action = None
                st.rerun()
        
        if st.session_state.pdf_bytes:
            pdf_b = st.session_state.pdf_bytes
            
            col_down1, col_down2 = st.columns([4, 1])
            with col_down1:
                st.markdown("**Documento PDF Extraído**")
            with col_down2:
                st.download_button(
                    label="⬇️ Baixar",
                    data=pdf_b,
                    file_name=st.session_state.filename.replace(".p7s", ".pdf"),
                    mime="application/pdf",
                    use_container_width=True,
                )
            
            st.markdown("---")
            
            if is_valid_pdf(pdf_b):
                # Renderizar PDF
                b64_pdf = base64.b64encode(pdf_b).decode("utf-8")
                pdf_display = (
                    f'<iframe src="data:application/pdf;base64,{b64_pdf}" '
                    f'width="100%" height="800" type="application/pdf" '
                    f'style="border: 1px solid var(--border); border-radius: 0.75rem;"></iframe>'
                )
                st.markdown(pdf_display, unsafe_allow_html=True)
            else:
                st.warning(
                    "⚠️ O conteúdo extraído não parece ser um PDF válido. "
                    "Pode ser outro tipo de documento."
                )
                st.download_button(
                    label="⬇️ Baixar conteúdo extraído",
                    data=pdf_b,
                    file_name=st.session_state.filename.replace(".p7s", ".bin"),
                    mime="application/octet-stream",
                    key="download_bin",
                    use_container_width=True,
                )
    
    # ── Ação 2: Análise de Assinatura ──
    elif st.session_state.action == "analyze":
        st.markdown("### 🔍 Análise da Assinatura Digital")
        st.markdown("---")
        
        with st.spinner("⏳ Analisando assinatura do arquivo .p7s..."):
            try:
                report = parse_p7s_signature(st.session_state.raw_file_bytes)
                st.session_state.sig_report = report
                st.success("✓ Assinatura analisada com sucesso!")
            except Exception as e:
                st.error(f"❌ Erro ao analisar assinatura: {e}")
                st.session_state.action = None
                st.rerun()
        
        if st.session_state.sig_report:
            report = st.session_state.sig_report
            
            st.markdown("#### 📋 Resumo da Assinatura")
            
            # Status geral — Cards
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.metric("👥 Signatários", report.total_signatarios)
            with col_b:
                conteudo_tipo = "✓ Embutido" if report.conteudo_embutido else "🔗 Detached"
                st.metric("📦 Conteúdo", conteudo_tipo)
            with col_c:
                st.metric("📄 Tipo", report.tipo_conteudo or "N/A")
            
            st.markdown("---")
            
            # Detalhes de cada signatário
            st.markdown("#### 🖊️ Informações dos Signatários")
            
            for idx, signer in enumerate(report.signatarios, 1):
                with st.expander(
                    f"👤 Signatário #{idx} — {signer.nome or 'Não identificado'}",
                    expanded=(idx == 1),
                ):
                    # Dados pessoais
                    st.markdown("**👤 Dados Pessoais**")
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(
                            f'<div class="field-label">Nome Completo</div>'
                            f'<div class="field-value">{signer.nome or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">E-mail</div>'
                            f'<div class="field-value">{signer.email or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Organização</div>'
                            f'<div class="field-value">{signer.organizacao or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                    with c2:
                        cpf_display = format_cpf(signer.cpf) if signer.cpf else "—"
                        cnpj_display = format_cnpj(signer.cnpj) if signer.cnpj else "—"
                        st.markdown(
                            f'<div class="field-label">CPF (ICP-Brasil)</div>'
                            f'<div class="field-value">{cpf_display}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">CNPJ (ICP-Brasil)</div>'
                            f'<div class="field-value">{cnpj_display}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Unidade Org.</div>'
                            f'<div class="field-value">{signer.unidade_organizacional or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                    
                    st.markdown("---")
                    
                    # Certificado
                    st.markdown("**🔐 Certificado Digital**")
                    c3, c4 = st.columns(2)
                    with c3:
                        st.markdown(
                            f'<div class="field-label">Emissor</div>'
                            f'<div class="field-value">{signer.emissor or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Org. Emissora</div>'
                            f'<div class="field-value">{signer.emissor_organizacao or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Número Serial</div>'
                            f'<div class="field-value" style="font-family:monospace;font-size:0.85rem;">'
                            f"{signer.numero_serial or '—'}</div>",
                            unsafe_allow_html=True,
                        )
                    with c4:
                        st.markdown(
                            f'<div class="field-label">Algoritmo de Assinatura</div>'
                            f'<div class="field-value">{signer.algoritmo_assinatura or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Algoritmo Hash</div>'
                            f'<div class="field-value">{signer.algoritmo_hash or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                        st.markdown(
                            f'<div class="field-label">Válido de</div>'
                            f'<div class="field-value">{signer.validade_inicio or "—"}</div>',
                            unsafe_allow_html=True,
                        )
                    
                    # Validade
                    st.markdown("---")
                    st.markdown("**⏰ Validade do Certificado**")
                    
                    st.markdown(
                        f'<div class="field-label">Válido até</div>'
                        f'<div class="field-value">{signer.validade_fim or "—"}</div>',
                        unsafe_allow_html=True,
                    )
                    
                    if signer.certificado_expirado:
                        st.markdown(
                            '<div class="status-warning">⚠️ Certificado EXPIRADO</div>',
                            unsafe_allow_html=True,
                        )
                    else:
                        st.markdown(
                            '<div class="status-ok">✓ Certificado dentro da validade</div>',
                            unsafe_allow_html=True,
                        )
                    
                    # Timestamp
                    st.markdown("---")
                    st.markdown("**⏱️ Assinatura**")
                    
                    if signer.data_assinatura:
                        st.markdown(
                            f'<div class="field-label">Data da Assinatura</div>'
                            f'<div class="field-value">{signer.data_assinatura}</div>',
                            unsafe_allow_html=True,
                        )
                    
                    carimbo_status = "✓ Presente" if signer.tem_carimbo_tempo else "✗ Não identificado"
                    st.markdown(
                        f'<div class="field-label">Carimbo de Tempo</div>'
                        f'<div class="field-value">{carimbo_status}</div>',
                        unsafe_allow_html=True,
                    )
            
            # Cadeia de certificação
            if report.certificados_cadeia:
                st.markdown("---")
                st.markdown("#### 🔗 Cadeia de Certificação")
                chain_data = []
                for i, c in enumerate(report.certificados_cadeia, 1):
                    chain_data.append(
                        {
                            "#": i,
                            "Certificado": c.get("nome", ""),
                            "Emitido por": c.get("emissor", ""),
                        }
                    )
                st.dataframe(chain_data, use_container_width=True, hide_index=True)
            
            # Erros
            if report.erros:
                st.markdown("---")
                st.markdown("#### ⚠️ Avisos e Alertas")
                for erro in report.erros:
                    st.warning(f"ℹ️ {erro}")
    
    # ── Ação 3: Gerar Relatório ──
    elif st.session_state.action == "report":
        st.markdown("### 📊 Geração de Relatório")
        st.markdown("---")
        
        with st.spinner("⏳ Analisando arquivo para gerar relatório..."):
            try:
                if st.session_state.sig_report is None:
                    report = parse_p7s_signature(st.session_state.raw_file_bytes)
                    st.session_state.sig_report = report
                else:
                    report = st.session_state.sig_report
                st.success("✓ Arquivo analisado! Agora gere o relatório.")
            except Exception as e:
                st.error(f"❌ Erro ao analisar arquivo: {e}")
                st.session_state.action = None
                st.rerun()
        
        if st.session_state.sig_report:
            report = st.session_state.sig_report
            
            st.markdown("Exporte um relatório completo com todas as informações da assinatura digital.")
            st.markdown("---")
            
            col_fmt1, col_fmt2 = st.columns(2)
            
            with col_fmt1:
                st.markdown(
                    """
                    <div class="info-card">
                        <h3>📄 Relatório em PDF</h3>
                        <p>Relatório formatado e profissional em PDF, pronto para impressão ou compartilhamento.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🔄 Gerar Relatório PDF", type="primary", use_container_width=True, key="btn_pdf"):
                    with st.spinner("⏳ Gerando PDF..."):
                        try:
                            pdf_report = generate_pdf_report(
                                report, st.session_state.filename
                            )
                            st.download_button(
                                label="⬇️ Baixar Relatório PDF",
                                data=pdf_report,
                                file_name=f"relatorio_{st.session_state.filename.replace('.p7s', '')}.pdf",
                                mime="application/pdf",
                                key="download_report_pdf",
                                use_container_width=True,
                            )
                            st.success("✓ Relatório PDF gerado com sucesso!")
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar relatório PDF: {e}")
            
            with col_fmt2:
                st.markdown(
                    """
                    <div class="info-card">
                        <h3>📝 Relatório em Texto</h3>
                        <p>Relatório em texto simples (.txt), compatível com qualquer leitor de texto.</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("🔄 Gerar Relatório TXT", use_container_width=True, key="btn_txt"):
                    with st.spinner("⏳ Gerando texto..."):
                        try:
                            txt_report = generate_text_report(
                                report, st.session_state.filename
                            )
                            st.download_button(
                                label="⬇️ Baixar Relatório TXT",
                                data=txt_report.encode("utf-8"),
                                file_name=f"relatorio_{st.session_state.filename.replace('.p7s', '')}.txt",
                                mime="text/plain",
                                key="download_report_txt",
                                use_container_width=True,
                            )
                            st.success("✓ Relatório TXT gerado com sucesso!")
                            
                            # Preview do relatório
                            with st.expander("👁️ Pré-visualização do relatório", expanded=False):
                                st.code(txt_report, language=None)
                        except Exception as e:
                            st.error(f"❌ Erro ao gerar relatório TXT: {e}")
