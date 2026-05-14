"""
Módulo de extração: lê arquivos .p7s (PKCS#7/CMS) e extrai o PDF embutido.
Suporta formatos DER (binário) e PEM (Base64).
"""

import base64
import re
from pathlib import Path
from asn1crypto import cms


def detect_format(raw_bytes: bytes) -> str:
    """Detecta se o arquivo é PEM (Base64) ou DER (binário)."""
    try:
        text = raw_bytes.decode("ascii", errors="ignore")
        if "-----BEGIN " in text:
            return "PEM"
    except Exception:
        pass
    return "DER"


def pem_to_der(pem_bytes: bytes) -> bytes:
    """Converte conteúdo PEM para DER."""
    text = pem_bytes.decode("ascii", errors="ignore")
    b64_lines = []
    inside = False
    for line in text.splitlines():
        if line.startswith("-----BEGIN "):
            inside = True
            continue
        if line.startswith("-----END "):
            inside = False
            continue
        if inside:
            b64_lines.append(line.strip())
    b64_data = "".join(b64_lines)
    return base64.b64decode(b64_data)


def load_p7s(file_path_or_bytes) -> bytes:
    """
    Carrega um arquivo .p7s a partir de um caminho ou bytes.
    Retorna os bytes DER do conteúdo PKCS#7.
    """
    if isinstance(file_path_or_bytes, (str, Path)):
        raw = Path(file_path_or_bytes).read_bytes()
    else:
        raw = file_path_or_bytes

    fmt = detect_format(raw)
    if fmt == "PEM":
        return pem_to_der(raw)
    return raw


def extract_pdf_from_p7s(file_path_or_bytes) -> bytes | None:
    """
    Extrai o conteúdo PDF embutido em um arquivo .p7s (attached signature).
    Retorna os bytes do PDF ou None se não houver conteúdo encapsulado.
    """
    der_bytes = load_p7s(file_path_or_bytes)

    try:
        content_info = cms.ContentInfo.load(der_bytes)
    except Exception as e:
        raise ValueError(f"Não foi possível ler a estrutura PKCS#7/CMS: {e}")

    content_type = content_info["content_type"].native
    if content_type != "signed_data":
        raise ValueError(
            f"Tipo de conteúdo inesperado: '{content_type}'. "
            f"Esperado: 'signed_data'."
        )

    signed_data = content_info["content"]

    encap_info = signed_data["encap_content_info"]
    encap_content = encap_info["content"]

    if encap_content is None:
        return None  # Assinatura detached — sem conteúdo embutido

    pdf_bytes = encap_content.native

    if isinstance(pdf_bytes, bytes):
        return pdf_bytes

    return None


def save_pdf(pdf_bytes: bytes, output_path: str | Path) -> Path:
    """Salva os bytes do PDF em um arquivo."""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(pdf_bytes)
    return output


def is_valid_pdf(data: bytes) -> bool:
    """Verifica se os bytes parecem ser um PDF válido."""
    return data[:5] == b"%PDF-"
