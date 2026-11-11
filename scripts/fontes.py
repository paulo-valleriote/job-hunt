"""Lista versionada de tokens de ATS (fontes_ats.json): empresa, ats, token e evidência.
Só entra token com evidência; sem evidência a entrada é recusada. Sem dado pessoal."""
import json, re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARQUIVO = ROOT / "fontes_ats.json"
ATS = ("greenhouse", "lever", "ashby")
# pagina_oficial: a página de carreiras da empresa aponta o ATS; conteudo_das_vagas: confirmado
# só pelo conteúdo das vagas (localização e empresa batem).
VINCULOS = ("pagina_oficial", "conteudo_das_vagas")
CHAVES = {"empresa", "ats", "token", "evidencia_url", "verificado_em", "vinculo"}


def validar_fontes(entradas):
    """Problemas da lista; lista vazia = utilizável."""
    probs = []
    for i, e in enumerate(entradas, 1):
        probs += [f"fonte {i}: chave desconhecida ({k!r})" for k in e if k not in CHAVES]
        probs += [f"fonte {i}: falta {k}" for k in sorted(CHAVES) if not str(e.get(k) or "").strip()]
        if e.get("ats") not in ATS:
            probs.append(f"fonte {i}: ats inválido ({e.get('ats')!r}); aceitos: " + ", ".join(ATS))
        if e.get("vinculo") not in VINCULOS:
            probs.append(f"fonte {i}: vinculo inválido ({e.get('vinculo')!r}); aceitos: " + ", ".join(VINCULOS))
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(e.get("verificado_em") or "")):
            probs.append(f"fonte {i}: verificado_em deve ser AAAA-MM-DD ({e.get('verificado_em')!r})")
        elif not _data_valida(e["verificado_em"]):
            probs.append(f"fonte {i}: verificado_em não é data ({e['verificado_em']!r})")
    return probs


def _data_valida(s):
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def carregar_fontes(arquivo=ARQUIVO):
    """Lê a lista; levanta ValueError com todos os problemas se houver algum."""
    entradas = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    probs = validar_fontes(entradas)
    if probs:
        raise ValueError("; ".join(probs))
    return entradas
