"""
Módulo de geração de relatório: cria um PDF formatado com as informações
da assinatura digital extraídas do arquivo .p7s.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT

from .signature_parser import SignatureReport, SignerInfo, format_cpf, format_cnpj


def _build_styles():
    """Cria estilos customizados para o relatório."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            spaceAfter=6 * mm,
            textColor=colors.HexColor("#1a365d"),
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=8 * mm,
            textColor=colors.HexColor("#4a5568"),
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            textColor=colors.HexColor("#2b6cb0"),
            borderPadding=(0, 0, 2, 0),
        )
    )

    styles.add(
        ParagraphStyle(
            "FieldLabel",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#718096"),
            spaceBefore=1 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            "FieldValue",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#1a202c"),
            spaceBefore=0,
            spaceAfter=2 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            "StatusOk",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#276749"),
        )
    )

    styles.add(
        ParagraphStyle(
            "StatusWarning",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#c53030"),
        )
    )

    return styles


def _make_info_table(data_pairs: list[tuple[str, str]]) -> Table:
    """Cria uma tabela de informações (campo: valor)."""
    table_data = []
    for label, value in data_pairs:
        if value:
            table_data.append([label, value])

    if not table_data:
        return None

    table = Table(table_data, colWidths=[55 * mm, 115 * mm])
    table.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TEXTCOLOR", (0, 0), (0, -1), colors.HexColor("#4a5568")),
                ("TEXTCOLOR", (1, 0), (1, -1), colors.HexColor("#1a202c")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#e2e8f0")),
                ("LINEBELOW", (0, -1), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return table


def generate_pdf_report(report: SignatureReport, filename: str = "") -> bytes:
    """
    Gera um relatório em PDF com as informações da assinatura.
    Retorna os bytes do PDF gerado.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )

    styles = _build_styles()
    elements = []

    # ---- Título ----
    elements.append(
        Paragraph("Relatório de Assinatura Digital", styles["ReportTitle"])
    )
    now = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    elements.append(
        Paragraph(f"Gerado em {now}", styles["ReportSubtitle"])
    )

    elements.append(
        HRFlowable(
            width="100%",
            thickness=1,
            color=colors.HexColor("#2b6cb0"),
            spaceAfter=5 * mm,
        )
    )

    # ---- Informações Gerais ----
    elements.append(
        Paragraph("Informações Gerais", styles["SectionHeader"])
    )

    general_data = [
        ("Arquivo:", filename or "Não informado"),
        ("Tipo de conteúdo:", report.tipo_conteudo or "N/A"),
        (
            "Conteúdo embutido:",
            "Sim (attached)" if report.conteudo_embutido else "Não (detached)",
        ),
        ("Total de signatários:", str(report.total_signatarios)),
    ]

    table = _make_info_table(general_data)
    if table:
        elements.append(table)

    # ---- Signatários ----
    for idx, signer in enumerate(report.signatarios, 1):
        elements.append(
            Paragraph(
                f"Signatário {idx}" + (f" — {signer.nome}" if signer.nome else ""),
                styles["SectionHeader"],
            )
        )

        # Dados pessoais
        signer_data = [
            ("Nome:", signer.nome),
            ("E-mail:", signer.email),
            ("Organização:", signer.organizacao),
            ("Unidade Org.:", signer.unidade_organizacional),
            ("País:", signer.pais),
            ("Estado:", signer.estado),
            ("Localidade:", signer.localidade),
        ]

        if signer.cpf:
            signer_data.append(("CPF:", format_cpf(signer.cpf)))
        if signer.cnpj:
            signer_data.append(("CNPJ:", format_cnpj(signer.cnpj)))

        table = _make_info_table(signer_data)
        if table:
            elements.append(table)
            elements.append(Spacer(1, 3 * mm))

        # Certificado
        elements.append(
            Paragraph("Certificado Digital", styles["SectionHeader"])
        )

        cert_data = [
            ("Emissor:", signer.emissor),
            ("Org. Emissora:", signer.emissor_organizacao),
            ("Nº Serial:", signer.numero_serial),
            ("Algoritmo:", signer.algoritmo_assinatura),
            ("Hash:", signer.algoritmo_hash),
            ("Válido de:", signer.validade_inicio),
            ("Válido até:", signer.validade_fim),
        ]

        table = _make_info_table(cert_data)
        if table:
            elements.append(table)

        # Status do certificado
        if signer.certificado_expirado:
            elements.append(
                Paragraph(
                    "⚠ Certificado EXPIRADO",
                    styles["StatusWarning"],
                )
            )
        else:
            elements.append(
                Paragraph(
                    "✓ Certificado dentro da validade",
                    styles["StatusOk"],
                )
            )

        elements.append(Spacer(1, 2 * mm))

        # Assinatura e Carimbo de Tempo
        ts_data = []
        if signer.data_assinatura:
            ts_data.append(("Data assinatura:", signer.data_assinatura))
        ts_data.append(
            (
                "Carimbo de tempo:",
                "Sim" if signer.tem_carimbo_tempo else "Não identificado",
            )
        )

        table = _make_info_table(ts_data)
        if table:
            elements.append(table)

        elements.append(
            HRFlowable(
                width="100%",
                thickness=0.5,
                color=colors.HexColor("#cbd5e0"),
                spaceBefore=4 * mm,
                spaceAfter=4 * mm,
            )
        )

    # ---- Cadeia de Certificação ----
    if report.certificados_cadeia:
        elements.append(
            Paragraph("Cadeia de Certificação", styles["SectionHeader"])
        )

        chain_header = [["#", "Certificado", "Emitido por"]]
        chain_rows = []
        for i, cert_info in enumerate(report.certificados_cadeia, 1):
            chain_rows.append(
                [str(i), cert_info.get("nome", ""), cert_info.get("emissor", "")]
            )

        chain_table = Table(
            chain_header + chain_rows,
            colWidths=[10 * mm, 80 * mm, 80 * mm],
        )
        chain_table.setStyle(
            TableStyle(
                [
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#edf2f7")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#2d3748")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 4),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(chain_table)

    # ---- Erros ----
    if report.erros:
        elements.append(Spacer(1, 5 * mm))
        elements.append(
            Paragraph("Avisos e Erros", styles["SectionHeader"])
        )
        for erro in report.erros:
            elements.append(
                Paragraph(f"• {erro}", styles["StatusWarning"])
            )

    # ---- Rodapé ----
    elements.append(Spacer(1, 10 * mm))
    elements.append(
        HRFlowable(
            width="100%",
            thickness=0.5,
            color=colors.HexColor("#cbd5e0"),
            spaceAfter=3 * mm,
        )
    )
    elements.append(
        Paragraph(
            "Relatório gerado automaticamente — P7S Reader v1.0",
            ParagraphStyle(
                "Footer",
                fontSize=8,
                textColor=colors.HexColor("#a0aec0"),
                alignment=TA_CENTER,
            ),
        )
    )

    doc.build(elements)
    return buffer.getvalue()


def generate_text_report(report: SignatureReport, filename: str = "") -> str:
    """
    Gera um relatório em texto simples com as informações da assinatura.
    """
    lines = []
    lines.append("=" * 60)
    lines.append("   RELATÓRIO DE ASSINATURA DIGITAL")
    lines.append("=" * 60)
    now = datetime.now().strftime("%d/%m/%Y às %H:%M:%S")
    lines.append(f"Gerado em: {now}")
    lines.append(f"Arquivo: {filename or 'Não informado'}")
    lines.append("")

    lines.append("-" * 40)
    lines.append("INFORMAÇÕES GERAIS")
    lines.append("-" * 40)
    lines.append(f"Tipo de conteúdo: {report.tipo_conteudo}")
    lines.append(
        f"Conteúdo embutido: {'Sim (attached)' if report.conteudo_embutido else 'Não (detached)'}"
    )
    lines.append(f"Total de signatários: {report.total_signatarios}")
    lines.append("")

    for idx, signer in enumerate(report.signatarios, 1):
        lines.append("-" * 40)
        lines.append(f"SIGNATÁRIO {idx}")
        lines.append("-" * 40)

        if signer.nome:
            lines.append(f"Nome: {signer.nome}")
        if signer.email:
            lines.append(f"E-mail: {signer.email}")
        if signer.organizacao:
            lines.append(f"Organização: {signer.organizacao}")
        if signer.cpf:
            lines.append(f"CPF: {format_cpf(signer.cpf)}")
        if signer.cnpj:
            lines.append(f"CNPJ: {format_cnpj(signer.cnpj)}")
        if signer.pais:
            lines.append(f"País: {signer.pais}")

        lines.append("")
        lines.append("Certificado:")
        lines.append(f"  Emissor: {signer.emissor}")
        lines.append(f"  Org. Emissora: {signer.emissor_organizacao}")
        lines.append(f"  Nº Serial: {signer.numero_serial}")
        lines.append(f"  Algoritmo: {signer.algoritmo_assinatura}")
        lines.append(f"  Hash: {signer.algoritmo_hash}")
        lines.append(f"  Válido de: {signer.validade_inicio}")
        lines.append(f"  Válido até: {signer.validade_fim}")
        lines.append(
            f"  Status: {'EXPIRADO' if signer.certificado_expirado else 'Válido'}"
        )

        if signer.data_assinatura:
            lines.append(f"  Data assinatura: {signer.data_assinatura}")
        lines.append(
            f"  Carimbo de tempo: {'Sim' if signer.tem_carimbo_tempo else 'Não identificado'}"
        )
        lines.append("")

    if report.certificados_cadeia:
        lines.append("-" * 40)
        lines.append("CADEIA DE CERTIFICAÇÃO")
        lines.append("-" * 40)
        for i, c in enumerate(report.certificados_cadeia, 1):
            lines.append(f"  {i}. {c.get('nome', '')} (emitido por: {c.get('emissor', '')})")
        lines.append("")

    if report.erros:
        lines.append("-" * 40)
        lines.append("AVISOS E ERROS")
        lines.append("-" * 40)
        for e in report.erros:
            lines.append(f"  ! {e}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("  Relatório gerado por P7S Reader v1.0")
    lines.append("=" * 60)

    return "\n".join(lines)
