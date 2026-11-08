#!/usr/bin/env python3
"""Gate de configuração: recusa rodar com busca.yaml / vagas_excluidas.md incompletos.

Uso: python3 scripts/validar_config.py [--busca busca.yaml]
                                       [--excluidas private/perfil/vagas_excluidas.md]
Saída 0 se OK; 1 com mensagens "arquivo:linha: problema" no stderr.
Sem dependências externas (subconjunto simples de YAML)."""
import argparse, re, sys
from dataclasses import dataclass
from pathlib import Path

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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--busca", default=str(ROOT / "busca.yaml"))
    ap.add_argument("--excluidas", default=str(ROOT / "private/perfil/vagas_excluidas.md"))
    a = ap.parse_args(argv)
    probs = validate(a.busca, a.excluidas)
    for p in probs:
        print(p, file=sys.stderr)
    if probs:
        print(f"Configuração incompleta ({len(probs)} problema(s)). Corrija e rode de novo.", file=sys.stderr)
        return 1
    print("Configuração OK.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
