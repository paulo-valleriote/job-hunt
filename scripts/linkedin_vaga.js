// Leitura da página de uma vaga do LinkedIn (/jobs/view/<ID>/). SOMENTE LEITURA.
// Função pura: texto da página -> campos. No navegador roda por evaluate_script (format "script",
// sourcePath = este arquivo); nos testes, via `node scripts/linkedin_vaga.js < entrada.json`.
// O cabeçalho da vaga é o trecho entre o título e "Sobre a vaga". Tudo depois (inclusive o card
// lateral "Mais vagas", com datas de OUTRAS vagas) fica de fora: ler data fora dele dá data errada.

// Dentro de uma função para poder ser avaliado mais de uma vez na mesma página (script clássico).
(function () {
  const UNIDADES = { minuto: 0, hora: 0, dia: 1, semana: 7, "mês": 30, meses: 30, ano: 365 };

  function cabecalho(texto, titulo) {
    const fim = texto.search(/Sobre a vaga|About the job/);
    const ate = fim >= 0 ? texto.slice(0, fim) : texto;
    const ini = titulo ? ate.indexOf(titulo) : -1;
    return ate.slice(ini >= 0 ? ini + titulo.length : 0);  // sem o título: "(Remote)" no nome não é modalidade
  }

  function dataIso(d) {
    const p = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
  }

  function dataPublicacao(cab, agora) {
    const m = cab.match(/há\s+(\d+)\s+(minuto|hora|dia|semana|mês|meses|ano)s?/i);
    if (!m) return null;
    const n = Number(m[1]);
    const u = m[2].toLowerCase();
    const d = new Date(agora);
    if (u === "minuto") d.setMinutes(d.getMinutes() - n);
    else if (u === "hora") d.setHours(d.getHours() - n);
    else d.setDate(d.getDate() - n * UNIDADES[u]);
    return dataIso(d);
  }

  function tipoCandidatura(links) {
    if (links.some((s) => /^(Candidatura simplificada|Easy Apply)/i.test(s))) return "simplificada";
    if (links.some((s) => /^Candidatar-se|^Apply/i.test(s))) return "externa";
    return null;
  }

  const MODALIDADES = { remoto: /\b(Remoto|Remote)\b/i, hibrido: /\b(Híbrido|Hybrid)\b/i, presencial: /\b(Presencial|On-?site)\b/i };

  function modalidade(cab) {
    for (const [nome, re] of Object.entries(MODALIDADES)) if (re.test(cab)) return nome;
    return "";
  }

  // "<local> · <quando> · N candidaturas": o local é o que vem antes do primeiro "·" na linha da data.
  function local(cab) {
    const linha = cab.split("\n").find((l) => /\bhá\s+\d+/i.test(l));
    return linha && linha.includes("·") ? linha.split("·")[0].trim() : "";
  }

  // Descrição = entre "Sobre a vaga" e "Sobre a empresa" (texto institucional) ou "Mais vagas" (outras vagas).
  function descricao(texto) {
    const ini = texto.search(/Sobre a vaga|About the job/);
    if (ini < 0) return "";
    const resto = texto.slice(ini);
    const fim = resto.search(/\n(Sobre a empresa|About the company|Mais vagas|Vagas similares|Similar jobs|Ver mais vagas)/i);
    return fim >= 0 ? resto.slice(0, fim) : resto;
  }

  // Frases que, sozinhas, dizem onde a vaga aceita candidatos.
  const PISTAS = /LATAM|Latin America|Am[ée]rica Latina|worldwide|anywhere|authori[sz]ed to work|work authori[sz]ation|right to work|must (be located|reside|live)|only hire|based in the|visa|sponsor|time ?zone|fuso hor/i;
  // "Brasil"/"Brazil" só conta junto de um sinal de elegibilidade; sozinho é texto institucional.
  const PAIS = /\b(Brasil|Brazil)\b/i;
  const SINAL = /remot|candidat|resid|located|based|apply|hire|contrata|work from|morar|viver|only|apenas|somente/i;

  function pistas(texto) {
    const linhas = descricao(texto).split("\n").map((l) => l.trim()).filter(Boolean);
    return linhas.filter((l) => PISTAS.test(l) || (PAIS.test(l) && SINAL.test(l))).map((l) => l.slice(0, 180)).slice(0, 8);
  }

  const TITULO_REQUISITOS = /^(requisitos|o que (esperamos|buscamos|precisa)|requirements|qualifica|qualifications|what you|what we.re looking|what we are looking|looking for|pr[ée]-requisitos|you have|about you|who you are|sobre voc[êe]|must have|minimum)/i;

  // Até 4 linhas sob o primeiro título de requisitos da descrição; sem título, [] (nada de adivinhar).
  function requisitos(texto) {
    const linhas = descricao(texto).split("\n").map((l) => l.trim()).filter(Boolean);
    const i = linhas.findIndex((l) => l.length < 80 && TITULO_REQUISITOS.test(l));
    return i < 0 ? [] : linhas.slice(i + 1, i + 5).map((l) => l.slice(0, 120));
  }

  function extrair({ texto, links, titulo, agora }) {
    const cab = cabecalho(texto, titulo);
    const encerrada = /Não aceita mais candidaturas|No longer accepting/i.test(cab);
    return { data: dataPublicacao(cab, agora), candidatura: tipoCandidatura(links), modalidade: modalidade(cab),
             local: local(cab), status: encerrada ? "encerrada" : "aberta", pistas: pistas(texto), requisitos: requisitos(texto) };
  }

  if (typeof module !== "undefined" && require.main === module) {
    let entrada = "";
    process.stdin.on("data", (c) => (entrada += c));
    process.stdin.on("end", () => console.log(JSON.stringify(extrair(JSON.parse(entrada)))));
  } else if (typeof document !== "undefined") {
    return extrair({
      texto: document.body.innerText,
      links: [...document.querySelectorAll("main a, main button")].map((b) => (b.innerText || "").trim()),
      titulo: document.title.split("|")[0].trim(),
      agora: new Date(),
    });
  }
})();
