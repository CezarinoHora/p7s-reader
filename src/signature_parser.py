"""
Módulo de análise de assinatura: extrai informações dos certificados
e signatários de um arquivo .p7s.
Suporte a certificados ICP-Brasil (CPF/CNPJ via OIDs específicos).
"""

from datetime import datetime, timezone
from dataclasses import dataclass, field
from asn1crypto import cms, x509, core

# OIDs específicos ICP-Brasil
ICP_BRASIL_CPF_OID = "2.16.76.1.3.1"
ICP_BRASIL_CNPJ_OID = "2.16.76.1.3.3"
ICP_BRASIL_NOME_RESPONSAVEL_OID = "2.16.76.1.3.2"
ICP_BRASIL_TITULO_ELEITOR_OID = "2.16.76.1.3.5"
ICP_BRASIL_CEI_OID = "2.16.76.1.3.6"
ICP_BRASIL_RG_OID = "2.16.76.1.3.4"


@dataclass
class SignerInfo:
    """Informações de um signatário."""
    nome: str = ""
    email: str = ""
    organizacao: str = ""
    unidade_organizacional: str = ""
    cpf: str = ""
    cnpj: str = ""
    pais: str = ""
    estado: str = ""
    localidade: str = ""

    # Informações do certificado
    emissor: str = ""
    emissor_organizacao: str = ""
    numero_serial: str = ""
    algoritmo_assinatura: str = ""
    algoritmo_hash: str = ""
    validade_inicio: str = ""
    validade_fim: str = ""
    certificado_expirado: bool = False

    # Informações extras ICP-Brasil
    nome_responsavel: str = ""
    rg: str = ""
    titulo_eleitor: str = ""

    # Timestamp
    data_assinatura: str = ""
    tem_carimbo_tempo: bool = False


@dataclass
class SignatureReport:
    """Relatório completo da assinatura."""
    arquivo_origem: str = ""
    tipo_conteudo: str = ""
    conteudo_embutido: bool = False
    total_signatarios: int = 0
    signatarios: list = field(default_factory=list)
    certificados_cadeia: list = field(default_factory=list)
    erros: list = field(default_factory=list)


def _extract_subject_field(subject, field_name: str) -> str:
    """Extrai um campo do subject do certificado."""
    try:
        value = subject.native.get(field_name, "")
        if isinstance(value, list):
            return ", ".join(str(v) for v in value)
        return str(value) if value else ""
    except Exception:
        return ""


def _extract_icp_brasil_info(cert: x509.Certificate, signer: SignerInfo):
    """Extrai informações específicas de certificados ICP-Brasil."""
    try:
        for ext in cert["tbs_certificate"]["extensions"]:
            oid = ext["extn_id"].dotted
            if oid == "2.16.76.1.3.1":  # Dados PF
                try:
                    raw_value = ext["extn_value"].parsed
                    if raw_value is None:
                        raw_value = ext["extn_value"]
                    raw_bytes = raw_value.native if hasattr(raw_value, 'native') else bytes(raw_value)
                    if isinstance(raw_bytes, bytes):
                        text = raw_bytes.decode("latin-1", errors="ignore")
                    else:
                        text = str(raw_bytes)
                    # CPF normalmente nos primeiros 8-11 caracteres após parsing
                    # O formato varia, tentamos extrair o CPF
                    import re
                    cpf_match = re.search(r'\d{11}', text)
                    if cpf_match:
                        signer.cpf = cpf_match.group(0)
                except Exception:
                    pass

            elif oid == "2.16.76.1.3.3":  # CNPJ
                try:
                    raw_value = ext["extn_value"].parsed
                    if raw_value is None:
                        raw_value = ext["extn_value"]
                    raw_bytes = raw_value.native if hasattr(raw_value, 'native') else bytes(raw_value)
                    if isinstance(raw_bytes, bytes):
                        text = raw_bytes.decode("latin-1", errors="ignore")
                    else:
                        text = str(raw_bytes)
                    import re
                    cnpj_match = re.search(r'\d{14}', text)
                    if cnpj_match:
                        signer.cnpj = cnpj_match.group(0)
                except Exception:
                    pass

    except Exception:
        pass  # Certificado pode não ter extensões ICP-Brasil

    # Tentar extrair CPF/CNPJ do campo Subject (common em ICP-Brasil)
    try:
        cn = _extract_subject_field(cert.subject, "common_name")
        if cn and not signer.cpf:
            import re
            cpf_match = re.search(r':(\d{11})(?:\D|$)', cn)
            if cpf_match:
                signer.cpf = cpf_match.group(1)
        if cn and not signer.cnpj:
            import re
            cnpj_match = re.search(r':(\d{14})(?:\D|$)', cn)
            if cnpj_match:
                signer.cnpj = cnpj_match.group(1)
    except Exception:
        pass


def _parse_certificate(cert: x509.Certificate) -> SignerInfo:
    """Analisa um certificado X.509 e extrai as informações do signatário."""
    signer = SignerInfo()

    # Subject fields
    subject = cert.subject
    signer.nome = _extract_subject_field(subject, "common_name")
    signer.email = _extract_subject_field(subject, "email_address")
    signer.organizacao = _extract_subject_field(subject, "organization_name")
    signer.unidade_organizacional = _extract_subject_field(
        subject, "organizational_unit_name"
    )
    signer.pais = _extract_subject_field(subject, "country_name")
    signer.estado = _extract_subject_field(subject, "state_or_province_name")
    signer.localidade = _extract_subject_field(subject, "locality_name")

    # Issuer
    issuer = cert.issuer
    signer.emissor = _extract_subject_field(issuer, "common_name")
    signer.emissor_organizacao = _extract_subject_field(
        issuer, "organization_name"
    )

    # Serial number
    signer.numero_serial = format(cert.serial_number, "X")

    # Algoritmo
    try:
        signer.algoritmo_assinatura = cert["tbs_certificate"][
            "signature"
        ].hash_algo or ""
        sig_algo = cert["tbs_certificate"]["signature"]["algorithm"].native
        signer.algoritmo_assinatura = sig_algo if sig_algo else ""
    except Exception:
        signer.algoritmo_assinatura = "Não identificado"

    # Validade
    try:
        not_before = cert["tbs_certificate"]["validity"]["not_before"].native
        not_after = cert["tbs_certificate"]["validity"]["not_after"].native
        signer.validade_inicio = not_before.strftime("%d/%m/%Y %H:%M:%S")
        signer.validade_fim = not_after.strftime("%d/%m/%Y %H:%M:%S")

        now = datetime.now(timezone.utc)
        if not_after.tzinfo is None:
            not_after = not_after.replace(tzinfo=timezone.utc)
        signer.certificado_expirado = now > not_after
    except Exception:
        pass

    # Extrair dados ICP-Brasil
    _extract_icp_brasil_info(cert, signer)

    # Tentar extrair email da extensão SAN
    if not signer.email:
        try:
            san_ext = cert.subject_alt_name_value
            if san_ext:
                for name in san_ext:
                    if name.name == "rfc822_name":
                        signer.email = name.chosen.native
                        break
        except Exception:
            pass

    return signer


def _find_matching_cert(
    signer_info: cms.SignerInfo, certificates: list
) -> x509.Certificate | None:
    """Encontra o certificado correspondente ao signatário."""
    sid = signer_info["sid"]

    try:
        issuer_serial = sid.chosen
        if hasattr(issuer_serial, "__getitem__"):
            target_serial = issuer_serial["serial_number"].native
            for cert in certificates:
                if cert.serial_number == target_serial:
                    return cert
    except Exception:
        pass

    # Fallback: retorna o primeiro certificado se houver apenas um
    if len(certificates) == 1:
        return certificates[0]

    return None


def _check_timestamp(signer_info: cms.SignerInfo, signer: SignerInfo):
    """Verifica se há carimbo de tempo na assinatura."""
    try:
        # Verificar unsigned attributes para timestamp
        unsigned_attrs = signer_info["unsigned_attrs"]
        if unsigned_attrs is not None:
            for attr in unsigned_attrs:
                if attr["type"].native == "signature_time_stamp_token":
                    signer.tem_carimbo_tempo = True
                    break

        # Verificar signed attributes para signing time
        signed_attrs = signer_info["signed_attrs"]
        if signed_attrs is not None:
            for attr in signed_attrs:
                if attr["type"].native == "signing_time":
                    val = attr["values"][0].native
                    if isinstance(val, datetime):
                        signer.data_assinatura = val.strftime(
                            "%d/%m/%Y %H:%M:%S"
                        )
                    break
    except Exception:
        pass


def parse_p7s_signature(file_path_or_bytes) -> SignatureReport:
    """
    Analisa um arquivo .p7s e retorna um relatório completo da assinatura.
    """
    from .extractor import load_p7s

    report = SignatureReport()

    try:
        der_bytes = load_p7s(file_path_or_bytes)
        content_info = cms.ContentInfo.load(der_bytes)
    except Exception as e:
        report.erros.append(f"Erro ao ler o arquivo: {e}")
        return report

    report.tipo_conteudo = content_info["content_type"].native

    if report.tipo_conteudo != "signed_data":
        report.erros.append(
            f"Tipo inesperado: '{report.tipo_conteudo}'. Esperado: 'signed_data'."
        )
        return report

    signed_data = content_info["content"]

    # Verificar conteúdo embutido
    encap_content = signed_data["encap_content_info"]["content"]
    report.conteudo_embutido = encap_content is not None

    # Extrair certificados da cadeia
    certificates = []
    cert_set = signed_data["certificates"]
    if cert_set is not None:
        for cert_choice in cert_set:
            try:
                cert = cert_choice.chosen
                if isinstance(cert, x509.Certificate):
                    certificates.append(cert)
            except Exception:
                pass

    # Registrar certificados da cadeia
    for cert in certificates:
        try:
            cn = _extract_subject_field(cert.subject, "common_name")
            issuer_cn = _extract_subject_field(cert.issuer, "common_name")
            report.certificados_cadeia.append(
                {"nome": cn, "emissor": issuer_cn}
            )
        except Exception:
            pass

    # Analisar cada signatário
    signer_infos = signed_data["signer_infos"]
    report.total_signatarios = len(signer_infos)

    for si in signer_infos:
        cert = _find_matching_cert(si, certificates)
        if cert:
            signer = _parse_certificate(cert)
        else:
            signer = SignerInfo()
            signer.nome = "Certificado não encontrado na cadeia"
            report.erros.append(
                "Não foi possível localizar o certificado do signatário."
            )

        # Extrair algoritmo de hash do signer info
        try:
            hash_algo = si["digest_algorithm"]["algorithm"].native
            signer.algoritmo_hash = hash_algo if hash_algo else ""
        except Exception:
            pass

        # Verificar timestamp
        _check_timestamp(si, signer)

        report.signatarios.append(signer)

    return report


def format_cpf(cpf: str) -> str:
    """Formata CPF: 000.000.000-00"""
    if len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    return cpf


def format_cnpj(cnpj: str) -> str:
    """Formata CNPJ: 00.000.000/0000-00"""
    if len(cnpj) == 14:
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    return cnpj
