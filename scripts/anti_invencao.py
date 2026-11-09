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

Currículo em inglês × perfil em português: a comparação é literal, então há (1) normalização de números
(2,800 = 2.800; 4.5% = 4,5%; 100k = 100 mil; 25+ = mais de 25), (2) um glossário EN -> PT em que o termo
em português TEM de constar no perfil (traduzir não cria fato novo), (3) composto com barra ou hífen
(Node.js/TypeScript, AI-agent-assisted) conferido por partes e plural/singular tolerado, e
(4) situação de certificação, "Nome (valid|expired [mm/aaaa]|in progress)", conferida na própria linha
do perfil: trocar válida por expirada, ou a data, é reprovado.
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path


def _canon_numeros(s):
    """Escreve números do mesmo jeito em EN e PT: milhar sem separador, decimal com ponto, 100k/100 mil
    = 100000 e 25+ = 25. Só reescreve formato; o valor continua tendo de constar no perfil."""
    def milhar(m):
        return m.group(0) if m.group(1) == "0" else m.group(1) + re.sub(r"[.,]", "", m.group(2))
    s = re.sub(r"(?<![\w.,])(\d{1,3})((?:[.,]\d{3})+)(?!\d)", milhar, s)
    s = re.sub(r"(?<![\w.,])(\d+),(\d{1,2})(?![\d,])", r"\1.\2", s)
    s = re.sub(r"(\d+)\s*mil\b", r"\g<1>000", s, flags=re.I)
    s = re.sub(r"(\d+)k\b", r"\g<1>000", s, flags=re.I)
    return re.sub(r"(?<![\w+])(\d+)\+(?!\+)", r"\1", s)


def _norm(s):
    s = unicodedata.normalize("NFKD", _canon_numeros(str(s))).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", s).strip()


# EN -> trechos em PT (normalizados) que TODOS têm de constar no perfil. Traduz o vocabulário, não
# inventa fato: sem o termo em português no perfil, o item continua reprovado.
GLOSSARIO = {
    "portuguese": ("portugues",), "english": ("ingles",), "spanish": ("espanhol",),
    "microservices": ("microsservicos",), "distributed systems": ("sistemas distribuidos",),
    "event-driven architecture": ("arquitetura orientada a eventos",),
    "asynchronous communication": ("comunicacao assincrona",), "rest apis": ("apis rest",),
    "unit tests": ("testes", "unitarios"), "integration tests": ("testes", "de integracao"),
    "e2e tests": ("testes", "e2e"), "regression tests": ("testes", "regressao"),
    "refactoring": ("refatoracao",), "test generation": ("geracao de testes",),
    "ai agent workflows": ("fluxos com agentes de ia",), "observability": ("observabilidade",),
    "authentication": ("autenticacao",), "databases": ("bancos de dados",),
    "computer systems": ("sistemas de computacao",),
    "full stack development": ("desenvolvimento full stack",),
    "technologist degree": ("tecnologo",),
    "technologist degree (in progress)": ("tecnologo", "em andamento"),
}
STATUS_CERT = {"valid": "valida", "expired": "expirada", "in progress": "em andamento"}


def _tokens(s):
    toks = {t.rstrip(".,;:") for t in re.findall(r"\w[\w+#./%-]*", _norm(s))}
    for t in list(toks):  # "sns/sqs" também vale como "sns" e "sqs"
        if re.search(r"[a-z]", t) and re.search(r"[/-]", t):
            toks.update(q for q in re.split(r"[/-]", t) if q)
    return toks


def _saliente(t, inicial):
    return (any(ch.isdigit() for ch in t) or any(ch.isupper() for ch in t[1:])
            or (not inicial and t[:1].isupper()))


def _salientes(texto):
    """Números e termos próprios de um texto livre (ignora a 1ª palavra de cada frase).
    Devolve (token, partes): token composto com / ou - (e letras) traz as partes salientes."""
    out = []
    for frase in re.split(r"(?<=[.!?])\s+|\n", _canon_numeros(str(texto))):
        for i, t in enumerate(re.findall(r"\w[\w+#./%-]*", frase)):
            t = t.rstrip(".,;:")
            if re.search(r"[A-Za-z]", t) and re.search(r"[/-]", t):
                partes = [p for j, p in enumerate(q for q in re.split(r"[/-]", t) if q)
                          if _saliente(p, i == 0 and j == 0)]
                if partes:
                    out.append((t, partes))
            elif _saliente(t, i == 0):
                out.append((t, [t]))
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
        yield "certificates.name", c.get("name", ""), "cert"
        yield "certificates.issuer", c.get("issuer", ""), "atomico"
        yield "certificates.date", c.get("date", ""), "ano"
    for l in r.get("languages") or []:
        yield "languages.language", l.get("language", ""), "atomico"
    for p in r.get("projects") or []:
        yield "projects.name", p.get("name", ""), "atomico"
        for h in p.get("highlights") or []:
            yield "projects.highlight", h, "livre"


def _traduz_ok(valor, perfil):
    """True se o termo (EN) tem tradução no glossário e todos os trechos em PT constam no perfil."""
    g = GLOSSARIO.get(_norm(valor))
    return bool(g) and all(x in perfil for x in g)


def _termo_ok(termo, palavras, perfil):
    n = _norm(termo).rstrip(".,;:")
    return (n in palavras or n + "s" in palavras or (n.endswith("s") and n[:-1] in palavras)
            or _traduz_ok(n, perfil))


def _cert_motivo(valor, perfil, linhas):
    """None se ok; senão o motivo. 'Nome (valid|expired mm/aaaa|in progress)' é conferido na linha do perfil."""
    m = re.match(r"^(.*?)\s*\(([^)]*)\)\s*$", str(valor))
    if not m:
        return None if _norm(valor) in perfil or _traduz_ok(valor, perfil) else "não consta no perfil"
    base, qual = _norm(m.group(1)), _norm(m.group(2))
    if base not in perfil:
        return "não consta no perfil"
    chave = next((k for k in STATUS_CERT if qual.startswith(k)), None)
    if chave is None:
        return f"qualificador '({m.group(2)})' não verificável no perfil"
    resto = qual[len(chave):].split()
    if any(base in l and STATUS_CERT[chave] in l and all(t in l for t in resto) for l in linhas):
        return None
    return f"situação '({m.group(2)})' não confere com a linha da certificação no perfil"


def checar(resume, perfil_texto):
    perfil = _norm(perfil_texto)
    palavras = _tokens(perfil_texto)
    linhas = [_norm(l) for l in str(perfil_texto).splitlines() if l.strip()]
    achados = []
    for campo, valor, modo in _fatos(resume):
        if not str(valor).strip():
            continue
        if modo == "atomico":
            if _norm(valor) not in perfil and not _traduz_ok(valor, perfil):
                achados.append({"campo": campo, "fato": str(valor), "motivo": "não consta no perfil"})
        elif modo == "cert":
            motivo = _cert_motivo(valor, perfil, linhas)
            if motivo:
                achados.append({"campo": campo, "fato": str(valor), "motivo": motivo})
        elif modo == "ano":
            for ano in re.findall(r"\d{4}", str(valor)):
                if ano not in palavras and ano not in perfil:
                    achados.append({"campo": campo, "fato": str(valor), "motivo": f"ano {ano} não consta no perfil"})
        else:
            for token, partes in _salientes(valor):
                if _norm(token).rstrip(".,;:") in palavras:
                    continue
                for t in partes:
                    if not _termo_ok(t, palavras, perfil):
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
