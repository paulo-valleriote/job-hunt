#!/usr/bin/env python3
"""Checagem anti-invenção do /curriculo (sempre ligada; não há opção de desativar).

  anti_invencao.py checar <pasta> --perfil <profile_truth.md>
      lê <pasta>/resume.json, compara cada fato com o perfil, grava <pasta>/anti_invencao.md
      exit 0 = tudo com respaldo; 1 = há fato sem respaldo (bloqueia a entrega); 2 = erro de uso

Camada determinística (esta): campos atômicos (empresa, cargo, instituição, curso, certificação,
tecnologia, idioma), anos das datas e, nos textos livres (resumo, destaques), números e termos
próprios (capitalizados no meio da frase, siglas, com dígitos). A leitura semântica de cada
afirmação é a 2ª camada, feita pelo modelo no /curriculo (ver .claude/commands/curriculo.md).
Limite: não valida identidade/contato (nome, e-mail, telefone, links) nem verbos/escopo.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path


def _norm(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


def _tokens(s):
    return {t.rstrip(".,;:") for t in re.findall(r"\w[\w+#./%-]*", _norm(s))}


def _salientes(texto):
    """Números e termos próprios de um texto livre (ignora a 1ª palavra de cada frase)."""
    out = []
    for frase in re.split(r"(?<=[.!?])\s+|\n", str(texto)):
        for i, t in enumerate(re.findall(r"\w[\w+#./%-]*", frase)):
            t = t.rstrip(".,;:")
            if (any(ch.isdigit() for ch in t) or any(ch.isupper() for ch in t[1:])
                    or (i > 0 and t[:1].isupper())):
                out.append(t)
    return out


def _fatos(r):
    """Gera (campo, valor, modo) com modo atomico|livre|ano."""
    b = r.get("basics") or {}
    yield "basics.label", b.get("label", ""), "livre"
    yield "basics.summary", b.get("summary", ""), "livre"
    for w in r.get("work") or []:
        for k in ("name", "position"):
            yield f"work.{k}", w.get(k, ""), "atomico"
        for k in ("startDate", "endDate"):
            yield f"work.{k}", w.get(k, ""), "ano"
        for h in w.get("highlights") or []:
            yield "work.highlight", h, "livre"
    for e in r.get("education") or []:
        for k in ("institution", "studyType", "area"):
            yield f"education.{k}", e.get(k, ""), "atomico"
        for k in ("startDate", "endDate"):
            yield f"education.{k}", e.get(k, ""), "ano"
    for s in r.get("skills") or []:
        for kw in s.get("keywords") or []:
            yield "skills.keyword", kw, "atomico"
    for c in r.get("certificates") or []:
        for k in ("name", "issuer"):
            yield f"certificates.{k}", c.get(k, ""), "atomico"
        yield "certificates.date", c.get("date", ""), "ano"
    for l in r.get("languages") or []:
        yield "languages.language", l.get("language", ""), "atomico"
    for p in r.get("projects") or []:
        yield "projects.name", p.get("name", ""), "atomico"
        for h in p.get("highlights") or []:
            yield "projects.highlight", h, "livre"


def checar(resume, perfil_texto):
    perfil = _norm(perfil_texto)
    palavras = _tokens(perfil_texto)
    achados = []
    for campo, valor, modo in _fatos(resume):
        if not str(valor).strip():
            continue
        if modo == "atomico":
            if _norm(valor) not in perfil:
                achados.append({"campo": campo, "fato": str(valor), "motivo": "não consta no perfil"})
        elif modo == "ano":
            for ano in re.findall(r"\d{4}", str(valor)):
                if ano not in palavras and ano not in perfil:
                    achados.append({"campo": campo, "fato": str(valor), "motivo": f"ano {ano} não consta no perfil"})
        else:
            for t in _salientes(valor):
                if _norm(t).rstrip(".,;:") not in palavras:
                    achados.append({"campo": campo, "fato": str(valor),
                                    "motivo": f"termo '{t}' não consta no perfil"})
    return achados


def relatorio(achados):
    if not achados:
        return "# Checagem anti-invenção\n\nNenhum fato sem respaldo encontrado (camada determinística).\n"
    linhas = ["# Checagem anti-invenção", "",
              f"{len(achados)} fato(s) sem respaldo no profile_truth.md. Corrija ou remova antes de entregar.", ""]
    linhas += [f"- `{x['campo']}`: {x['fato']} — {x['motivo']}" for x in achados]
    return "\n".join(linhas) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description="Checagem anti-invenção (sempre ligada)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("checar"); c.add_argument("pasta"); c.add_argument("--perfil", required=True)
    a = ap.parse_args(argv)
    pasta, perfil = Path(a.pasta), Path(a.perfil)
    if not (pasta / "resume.json").is_file() or not perfil.is_file():
        print("ERRO: resume.json ou perfil não encontrado", file=sys.stderr); return 2
    try:
        resume = json.loads((pasta / "resume.json").read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print("ERRO: resume.json inválido:", e, file=sys.stderr); return 2
    achados = checar(resume, perfil.read_text(encoding="utf-8"))
    (pasta / "anti_invencao.md").write_text(relatorio(achados), encoding="utf-8")
    for x in achados:
        print(f"SEM RESPALDO: {x['campo']}: {x['fato']} ({x['motivo']})", file=sys.stderr)
    return 1 if achados else 0


if __name__ == "__main__":
    sys.exit(main())
