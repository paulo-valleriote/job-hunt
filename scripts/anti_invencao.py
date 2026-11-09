#!/usr/bin/env python3
"""Checagem anti-invenção do /curriculo (sempre ligada; não há opção de desativar).

  anti_invencao.py checar <pasta> --perfil <profile_truth.md>
      lê <pasta>/resume.json, compara cada fato com o perfil, grava <pasta>/anti_invencao.md
      exit 0 = tudo com respaldo; 1 = há fato sem respaldo (bloqueia a entrega); 2 = erro de uso

Camada determinística (esta): campos atômicos (empresa, cargo, instituição, curso, certificação,
tecnologia, idioma), anos das datas e, nos textos livres (resumo, destaques), números e termos
próprios (capitalizados no meio da frase, siglas, com dígitos). A leitura semântica de cada
afirmação é a 2ª camada, feita pelo modelo no /curriculo (ver .claude/commands/curriculo.md).
Camada de omissão (determinística): tudo o que o perfil afirma sobre a carreira tem de estar no resume.json.
Experiências (`### Empresa — Cargo (AAAA-MM a AAAA-MM|atual)`): empresa, cargo e período; formação
(`Curso — Instituição — situação`): a instituição; certificações (`Nome — emissor — ...`): o nome, sem o
qualificador entre parênteses. Não cobre o curso da formação nem o escopo de cada cargo, e não há omissão
"por relevância": todo item do perfil tem de aparecer. Perfil sem essa estrutura: exit 2 (erro de uso).

Camada de termos proibidos (determinística): os termos da seção `## Termos proibidos` do perfil, um por linha,
não podem aparecer em nenhum texto do resume.json. Comparação normalizada (acento, caixa) e por palavra
inteira ("Go" não casa com "Google"). Seção ausente ou vazia gera aviso, sem bloquear.

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


class PerfilSemEstrutura(Exception):
    """O perfil não tem a estrutura que a checagem de omissão precisa (erro de uso, exit 2)."""


EXPERIENCIA_RE = re.compile(r"^###\s+(.+?)\s+—\s+(.+?)\s*\(([^()]*)\)\s*$")
PERIODO_RE = re.compile(r"^(\d{4}-\d{2})\s+a\s+(\d{4}-\d{2}|atual|presente)$", re.I)
VALORES_ATUAL = ("", "present", "current", "atual", "presente")


def _sem_comentarios(texto):
    """Tira comentários HTML (inclusive os de várias linhas), que não contam como fato nem como termo."""
    return re.sub(r"<!--.*?-->", "", str(texto), flags=re.S)


def _secoes(perfil_texto):
    """{título normalizado: linhas} para cada '## Título'. Ignora comentários HTML e linhas vazias."""
    secoes, atual = {}, None
    for bruta in _sem_comentarios(perfil_texto).splitlines():
        if bruta.startswith("## "):
            atual = _norm(bruta[3:])
            secoes.setdefault(atual, [])
            continue
        linha = bruta.strip()
        if atual is not None and linha:
            secoes[atual].append(linha)
    return secoes


def _item(linha):
    return linha[2:].strip() if linha.startswith("- ") else linha


def _periodo_ok(w, ini, fim):
    sd, ed = str(w.get("startDate") or ""), str(w.get("endDate") or "")
    if fim.lower() in ("atual", "presente"):
        ok_fim = _norm(ed) in VALORES_ATUAL
    else:
        ok_fim = ed.startswith(fim)
    return sd.startswith(ini) and ok_fim


def omissoes(resume, perfil_texto):
    """Itens do perfil (experiências, formação, certificações) que não constam no resume.json."""
    secoes = _secoes(perfil_texto)
    linhas = [l.strip() for l in _sem_comentarios(perfil_texto).splitlines() if l.strip()]
    exp = [m for m in (EXPERIENCIA_RE.match(l) for l in linhas) if m]
    if not exp:
        raise PerfilSemEstrutura("nenhuma experiência no formato '### Empresa — Cargo (AAAA-MM a AAAA-MM)'")
    for secao in ("formacao", "certificacoes"):
        if secao not in secoes:
            raise PerfilSemEstrutura(f"seção '## {secao}' ausente (esperado '## Formação' e '## Certificações')")
    formacao = [_item(l) for l in secoes["formacao"]]
    certificacoes = [_item(l) for l in secoes["certificacoes"]]
    for item in formacao + certificacoes:
        if " — " not in item:
            raise PerfilSemEstrutura(f"item sem separador ' — ': '{item}' (formato: 'Nome — Instituição — situação')")

    achados = []
    works = resume.get("work") or []
    for m in exp:
        empresa, cargo, datas = m.group(1), m.group(2), m.group(3)
        fato = f"{empresa} — {cargo} ({datas})"
        da_empresa = [w for w in works if _norm(w.get("name", "")) == _norm(empresa)]
        do_cargo = [w for w in da_empresa if _norm(w.get("position", "")) == _norm(cargo)]
        p = PERIODO_RE.match(datas.strip())
        if not da_empresa:
            motivo = "empresa não consta no resume.json"
        elif not do_cargo:
            motivo = f"cargo '{cargo}' não consta em '{empresa}' no resume.json"
        elif p and not any(_periodo_ok(w, p.group(1), p.group(2)) for w in do_cargo):
            motivo = f"período ({datas}) não confere com o resume.json"
        else:
            continue
        achados.append({"campo": "omissao.work", "fato": fato, "motivo": motivo})

    for item in formacao:
        instituicao = re.split(r"\s+—\s+", item)[1].strip()
        if not any(_norm(e.get("institution", "")) == _norm(instituicao) for e in resume.get("education") or []):
            achados.append({"campo": "omissao.education", "fato": item,
                            "motivo": f"instituição '{instituicao}' não consta no resume.json"})

    nomes = {_norm(re.sub(r"\s*\([^()]*\)\s*$", "", str(c.get("name", "")))) for c in resume.get("certificates") or []}
    for item in certificacoes:
        nome = re.split(r"\s+—\s+", item)[0].strip()
        if _norm(nome) not in nomes:
            achados.append({"campo": "omissao.certificates", "fato": item,
                            "motivo": "certificação não consta no resume.json"})
    return achados


def _textos(obj, campo=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _textos(v, f"{campo}.{k}" if campo else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _textos(v, f"{campo}[{i}]")
    elif isinstance(obj, str):
        yield campo, obj


def termos_proibidos(resume, perfil_texto):
    """(achados, avisos): termos da seção '## Termos proibidos' que aparecem em algum texto do resume.json."""
    secao = _secoes(perfil_texto).get("termos proibidos")
    termos = [_item(l) for l in secao or [] if _item(l)]
    avisos = []
    if secao is None:
        avisos.append("seção '## Termos proibidos' ausente no perfil: termos proibidos não checados")
    elif not termos:
        avisos.append("seção '## Termos proibidos' vazia: termos proibidos não checados")
    achados = []
    for campo, texto in _textos(resume):
        t = _norm(texto)
        for termo in termos:
            if re.search(r"(?<![a-z0-9])" + re.escape(_norm(termo)) + r"(?![a-z0-9])", t):
                achados.append({"campo": campo, "fato": texto, "motivo": f"termo proibido '{termo}'"})
    return achados, avisos


def _lista(itens, vazio):
    return [f"- `{x['campo']}`: {x['fato']} — {x['motivo']}" for x in itens] or [vazio]


def relatorio(achados, omissoes=(), proibidos=(), avisos=()):
    linhas = ["# Checagem anti-invenção", ""]
    if not (achados or omissoes or proibidos):
        linhas += ["Nenhum fato sem respaldo encontrado (camada determinística).", ""]
    linhas += ["## Sem respaldo", ""] + _lista(achados, "Nenhum.") + [""]
    linhas += ["## Omissões", "", "Itens do profile_truth.md que faltam no resume.json:", ""]
    linhas += _lista(omissoes, "Nenhuma.") + [""]
    linhas += ["## Termos proibidos", "", "Termos de `## Termos proibidos` do perfil que aparecem no resume.json:", ""]
    linhas += _lista(proibidos, "Nenhum.") + [""]
    if avisos:
        linhas += ["## Avisos", ""] + [f"- {x}" for x in avisos] + [""]
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
    texto = perfil.read_text(encoding="utf-8")
    try:
        om = omissoes(resume, texto)
    except PerfilSemEstrutura as e:
        print("ERRO: perfil sem a estrutura esperada:", e, file=sys.stderr); return 2
    achados = checar(resume, texto)
    proibidos, avisos = termos_proibidos(resume, texto)
    (pasta / "anti_invencao.md").write_text(relatorio(achados, om, proibidos, avisos), encoding="utf-8")
    for x in achados:
        print(f"SEM RESPALDO: {x['campo']}: {x['fato']} ({x['motivo']})", file=sys.stderr)
    for x in om:
        print(f"OMISSÃO: {x['fato']} ({x['motivo']})", file=sys.stderr)
    # o termo proibido não vai para o stderr (logs): ele fica só no anti_invencao.md, na pasta privada
    for x in proibidos:
        print(f"TERMO PROIBIDO em {x['campo']} (ver anti_invencao.md)", file=sys.stderr)
    for x in avisos:
        print("AVISO:", x, file=sys.stderr)
    return 1 if (achados or om or proibidos) else 0


if __name__ == "__main__":
    sys.exit(main())
