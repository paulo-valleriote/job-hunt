# job-hunt

Assistente local para buscar vagas, triar contra o seu perfil, gerar currículo sob medida (PDF) e registrar candidaturas. Roda no Claude Code com a sua assinatura, sem chave de API. Construído por cima do [meu-emprego-novo](https://github.com/R238Company/meu-emprego-novo), clonado em `vendor/` sem modificações.

> **O envio das candidaturas é sempre manual.** Nada aqui envia currículo, mensagem ou formulário em seu nome.

> **Sem backup.** Não existe cópia de segurança. `private/` (perfil, vagas, currículos e tracker) é a **única cópia** do que for gerado. Se o disco ou o WSL se perder, os dados vão junto. Copie `private/` por conta própria, quando e para onde quiser.

## Setup do zero

Pré-requisitos: WSL2/Linux, `python3` e o CLI `claude` (Claude Code).

1. `make setup`: clona o upstream em `vendor/`, cria o `venv`, instala as dependências (`requirements.txt`), cria `private/` e copia uma única vez seus dados da origem. Nunca sobrescreve o que já existe. Pode ser repetido.
   - A origem padrão é `/mnt/e/busca-vagas/privado`. Para outra pasta: `JOBHUNT_SOURCE_DIR=/caminho make setup`.
   - Copia `perfil/profile_truth.md`, `perfil/resume.pdf`, `perfil/vagas_excluidas.md` e `perfil/tracker.csv` (este vira `private/tracker.csv`). O que faltar na origem é pulado, com aviso.
2. Instale o LaTeX (o assistente nunca roda `sudo`; rode você, com o `!` na frente se estiver dentro do Claude Code):

   ```
   sudo apt install -y texlive-latex-recommended texlive-latex-extra texlive-fonts-recommended texlive-fonts-extra texlive-lang-portuguese lmodern
   ```

   Esta é a lista usada pelo `make doctor`. Ela ainda precisa ser confirmada compilando o exemplo do upstream; se o doctor apontar pacote faltando, ajuste conforme o erro.
3. `make doctor`: confere `python3`, `claude`, `pdflatex`, `private/`, placeholders nos arquivos de configuração e se o exemplo do upstream compila em PDF. Cada item faltante vem com o comando para corrigir. Termina com "Ambiente pronto." quando está tudo certo.

## O que você precisa preencher

`/busca` e `/triagem` **recusam rodar** enquanto estes arquivos tiverem placeholders. Teste com `make check-config`.

- **`busca.yaml`** (na raiz, ignorado pelo git): `cp busca.example.yaml busca.yaml` e troque cada valor `EXEMPLO ...`. Campos: `cargos_alvo`, `senioridade`, `regime`, `paises_fuso`, `faixa_salarial_minima`, `stack_desejada`, `deal_breakers`, `idiomas_aceitos`. Os comentários do modelo explicam cada um.
- **`private/perfil/vagas_excluidas.md`**: empresas, recrutadores e origens que você quer evitar, com datas reais. Troque "Empresa A", "Recrutadora C", "AAAA-MM-DD" e similares do modelo pelos seus dados.
- **`private/perfil/profile_truth.md`**: a única fonte de fatos sobre você. Currículos e triagens só afirmam o que está aqui.

## Fluxo diário

Dentro do Claude Code, na pasta do projeto:

1. **`/busca`**: busca no LinkedIn **pelo navegador** (extensão Claude in Chrome conectada com `/chrome`, e você logado no LinkedIn) as vagas publicadas desde a última busca. Abre cada uma para conferir a data, se ainda aceita candidaturas, o tipo de candidatura e os requisitos principais. Grava de 10 a 20 vagas, sem classificar, em `private/vagas/AAAA-MM-DD-busca.md`, separadas em candidatura simplificada e externa, com numeração contínua e a lista do que foi descartado e por quê. As URLs de busca só levam cargo, local e regime, nunca dados pessoais.
2. **`/triagem <link ou texto da vaga>`**: compara a vaga com o perfil e salva nota de aderência, motivos e lacunas em `private/vagas/`. Se o link não abrir, cole o texto da vaga.
3. **`/curriculo <link ou texto da vaga> [--en|--pt]`**: gera o currículo em PDF em `private/curriculos/<data>-<empresa>-<cargo>/`. O idioma é detectado pela vaga; `--en` ou `--pt` força. Cada currículo passa por um avaliador separado (nota 1 a 10), é revisado até a nota 8,5 (no máximo 3 revisões) e entrega a versão de melhor nota. Também grava `coverage_review.md` (lacunas), `rating_report.md` (histórico de notas) e `anti_invencao.md`. Se a cota da assinatura apertar: `JOBHUNT_MAX_REVISOES=1`.
4. **Envio manual**: você revisa o currículo e envia a candidatura pelo site da empresa. A checagem anti-invenção reduz o risco, mas não o zera: leia o PDF inteiro antes de usar.
5. **`/enviei <empresa> | <vaga> [| link]`**: registra a candidatura que você já enviou em `private/tracker.csv`, apontando o currículo gerado quando houver, sem duplicar a vaga.

## Interface local (opcional)

`make ui` abre a interface Streamlit, só em `localhost`. Cada tela chama os mesmos comandos e scripts; tudo o que ela faz também funciona pelos comandos.

- **Vagas**: as vagas buscadas e triadas.
- **Currículos**: lista os currículos gerados, mostra PDF, nota, `coverage_review.md` e `rating_report.md`, e tem botão de gerar (chama o `/curriculo`).
- **Tracker**: tabela editável do `private/tracker.csv`, que continua sendo a fonte de verdade e abre no Excel.

## Golpes e segurança

Resumo de `docs/08-golpes-e-seguranca.md` do upstream (em `vendor/meu-emprego-novo/meu-emprego-novo-pipeline/docs/`):

- **Nunca baixe nem execute código** de uma "entrevista técnica". Faça testes só em plataformas conhecidas, no navegador.
- **Nunca preencha número de documento** (CPF, RG, passaporte) em formulário de candidatura. Só na contratação, por canal oficial.
- **Pedido de pagamento**, taxa, curso ou "kit" antes de contratar é golpe.
- **Desconfie** de e-mail de domínio gratuito ou diferente do site da empresa, recrutador sem histórico, vaga que não está no site oficial, urgência e proposta boa demais.
- **Conversa que migra para app de mensagens** com pedido de dados ou ações: confirme a identidade por canal oficial.
- Não peça ao assistente para executar código recebido de terceiros.

Dentro do projeto: nada de `private/` em commits, logs compartilhados ou consultas externas.

## Testes

`make test`, `make test-doctor`, `make test-config`, `make test-busca`, `make test-triagem`, `make test-curriculo`, `make test-avaliador`, `make test-anti-invencao`, `make test-enviei`, `make test-ui`.
