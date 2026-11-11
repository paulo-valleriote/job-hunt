"""Lista versionada de tokens de ATS (fontes_ats.json): empresa, ats, token e evidência.
Só entra token com evidência; sem evidência a entrada é recusada. Sem dado pessoal."""
import json, re, sys
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


class SemAprovacao(Exception):
    """Acréscimo sem aprovação explícita do usuário (flag --aprovado)."""


def acrescentar(entrada, aprovado, arquivo=ARQUIVO):
    """Grava uma entrada nova na lista só com aprovação explícita e se passar na validação.
    Recusa sem evidência, vínculo ou ATS inválidos, evidência que não seja https e duplicata."""
    if not aprovado:
        raise SemAprovacao("nenhuma entrada é gravada sem aprovação explícita do usuário")
    probs = validar_fontes([entrada])
    if str(entrada.get("evidencia_url") or "").strip() and not str(entrada["evidencia_url"]).startswith("https://"):
        probs.append("fonte: evidencia_url deve ser https")
    lista = json.loads(Path(arquivo).read_text(encoding="utf-8"))
    if any(e.get("ats") == entrada.get("ats") and e.get("token") == entrada.get("token") for e in lista):
        probs.append(f"fonte: já existe {entrada.get('ats')}/{entrada.get('token')}")
    if probs:
        raise ValueError("; ".join(probs))
    lista.append(entrada)
    Path(arquivo).write_text(json.dumps(lista, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return entrada


def main(argv=None):
    import argparse
    p = argparse.ArgumentParser(description="Lista de tokens de ATS (fontes_ats.json).")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("acrescentar", help="acrescenta uma entrada aprovada pelo usuário")
    a.add_argument("--json", required=True, help="entrada completa como objeto JSON")
    a.add_argument("--arquivo", default=str(ARQUIVO))
    a.add_argument("--aprovado", action="store_true", help="o usuário aprovou esta entrada")
    args = p.parse_args(argv)
    try:
        acrescentar(json.loads(args.json), aprovado=args.aprovado, arquivo=args.arquivo)
    except SemAprovacao as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 2
    except (ValueError, json.JSONDecodeError) as e:
        print(f"recusado: {e}", file=sys.stderr)
        return 1
    print("entrada acrescentada")
    return 0


if __name__ == "__main__":
    sys.exit(main())
