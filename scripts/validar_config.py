#!/usr/bin/env python3
"""Gate de configuração: recusa rodar com busca.yaml / vagas_excluidas.md incompletos.

Uso: python3 scripts/validar_config.py [--busca busca.yaml]
                                       [--excluidas private/perfil/vagas_excluidas.md]
Saída 0 se OK; 1 com mensagens "arquivo:linha: problema" no stderr.
Sem dependências externas (subconjunto simples de YAML)."""
import argparse, re, sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rebase as rb  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["cargos_alvo", "senioridade", "regime", "paises_fuso",
            "faixa_salarial_minima", "stack_desejada", "deal_breakers",
            "idiomas_aceitos"]
LISTS = {"cargos_alvo", "paises_fuso", "stack_desejada", "deal_breakers", "idiomas_aceitos"}

EXAMPLE_RE = re.compile(r"^\s*(EXEMPLO|<.*>$|preencha)", re.I)
PLACEHOLDERS = [
    (re.compile(r"\bEmpresa [A-Z]\b"), 'placeholder "Empresa X"'),
    (re.compile(r"\bRecrutadora? [A-Z]\b"), 'placeholder "Recrutadora X"'),
    (re.compile(r"AAAA-MM-DD"), 'placeholder de data "AAAA-MM-DD"'),
]
MODALIDADE_RE = re.compile(r"\b(presencial|híbrido|hibrido)\b(?!\s*(em|\(|:|-|–|—)\s*[A-ZÀ-Ý])", re.I)


@dataclass
class Problem:
    path: Path
    line: int
    message: str

    def __str__(self):
        return f"{self.path}:{self.line}: {self.message}"


def _strip(v):
    return re.sub(r"\s+#.*$", "", v).strip().strip("\"'")


def _check_busca(path):
    probs = []
    if not path.is_file():
        return [Problem(path, 0, "arquivo não encontrado (copie busca.example.yaml para busca.yaml)")]
    keys, cur = {}, None
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = raw.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_]+):(.*)$", raw)
        if m and not raw.startswith(" "):
            cur = m.group(1)
            keys[cur] = {"line": n, "items": []}
            val = _strip(m.group(2))
            if val:
                keys[cur]["items"].append((n, val))
        elif s.startswith("- ") and cur:
            keys[cur]["items"].append((n, _strip(s[2:])))
    for k in REQUIRED:
        if k not in keys:
            probs.append(Problem(path, 0, f"campo obrigatório ausente: {k}"))
            continue
        info = keys[k]
        if not info["items"]:
            kind = "lista vazia" if k in LISTS else "campo vazio"
            probs.append(Problem(path, info["line"], f"{kind}: {k}"))
        for n, val in info["items"]:
            if not val or EXAMPLE_RE.match(val):
                probs.append(Problem(path, n, f"valor vazio ou de exemplo em {k}: {val!r}"))
    return probs


def _check_excluidas(path):
    if not path.is_file():
        return [Problem(path, 0, "arquivo não encontrado (rode make setup)")]
    probs = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        for rx, msg in PLACEHOLDERS:
            if rx.search(line):
                probs.append(Problem(path, n, msg))
        if MODALIDADE_RE.search(line):
            probs.append(Problem(path, n, "modalidade sem cidade (ex.: presencial em Curitiba)"))
    return probs


def validate(busca, excluidas):
    return _check_busca(Path(busca)) + _check_excluidas(Path(excluidas))


def _stack_desejada(path):
    """[(linha, nome)] dos itens de stack_desejada; a validação contra o /meta usa os nomes."""
    out, dentro = [], False
    if not path.is_file():
        return out
    for n, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if re.match(r"^stack_desejada:", raw):
            dentro = True
            continue
        if dentro and raw and not raw.startswith(" "):
            break
        if dentro and raw.strip().startswith("- "):
            out.append((n, _strip(raw.strip()[2:])))
    return out


def validar_rebase(busca, env, skills):
    """Token em private/rebase.env (TOKEN=) e stack_desejada traduzida contra os slugs do /meta.
    skills=None pula a checagem de stack (sem rede). O token nunca entra na mensagem."""
    probs = []
    if rb.ler_token(Path(env)) is None:
        probs.append(Problem(Path(env), 0, "token ausente: " + rb.mensagem_token_ausente()))
    if skills is not None:
        for n, nome in _stack_desejada(Path(busca)):
            slugs = rb.traduzir_stack([nome])
            slug = slugs[0] if slugs else ""
            if slug not in skills:
                probs.append(Problem(Path(busca), n,
                                     f"stack desconhecida no Rebase: {nome!r} (slug {slug!r}) "
                                     "não consta do /api/v1/meta"))
    return probs


def _skills(a):
    """Slugs do /meta: de --meta-json (teste offline) ou da API. Falha vira problema, não exceção."""
    if a.meta_json:
        salvo = Path(a.meta_json).read_text(encoding="utf-8")
        return rb.buscar_skills_meta(fetch=lambda url, headers=None: salvo)
    return rb.buscar_skills_meta()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    ap.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    ap.add_argument("--env", default=str(rb.ENV_ARQUIVO))
    ap.add_argument("--meta-json", default=None, help="resposta de /api/v1/meta salva (sem rede)")
    a = ap.parse_args(argv)
    probs = validate(a.busca, a.excluidas)
    try:
        skills = _skills(a)
    except Exception as e:  # sem /meta a stack não pode ser validada: diz isso e recusa
        skills = None
        probs.append(Problem(Path(a.busca), 0, f"não foi possível ler /api/v1/meta ({rb.motivo_da_falha(e)})"))
    probs += validar_rebase(a.busca, a.env, skills)
    for p in probs:
        print(p, file=sys.stderr)
    if probs:
        print(f"Configuração incompleta ({len(probs)} problema(s)). Corrija e rode de novo.", file=sys.stderr)
        return 1
    print("Configuração OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
