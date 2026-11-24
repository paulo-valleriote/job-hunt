# 16: `/triagem` lê a página markdown do Rebase

**What to build:** no `/triagem` de uma vaga do Rebase (com `Atribuição` do Rebase ou link `rebasedev.com.br/jobs/…`), o anúncio é lido primeiro pela página markdown pública do catálogo (`<url>.md`, sem token). Se ela falhar, a triagem tenta o link do ATS e, por último, pede o texto colado, como hoje. Se a página disser que a vaga foi encerrada, a triagem avisa com destaque no topo e segue.

- Muda só o passo 2 do `.claude/commands/triagem.md`. O `scripts/triagem.py` não muda.
- `.claude/settings.json` ganha `WebFetch(domain:rebasedev.com.br)`.

Fonte: `.scratch/rebase-jobs/spec.md`, histórias 38–40 e seção "Instruções e regras".

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] O passo 2 do `triagem.md` define a ordem: página `.md` do Rebase, depois o link do ATS, depois o texto colado
- [ ] Vaga encerrada gera um aviso de destaque no topo da triagem, sem interromper
- [ ] O `settings.json` libera `WebFetch(domain:rebasedev.com.br)`
- [ ] `scripts/triagem.py` não muda
