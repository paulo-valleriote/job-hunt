import streamlit as st

import curriculos_core as core


def _mostrar(c):
    nota = c["nota"]
    st.metric("Nota", f"{nota:g}/10" if nota is not None else "sem nota")
    if c["pdf"]:
        st.download_button("Baixar PDF", c["pdf"].read_bytes(), file_name=c["pdf"].name,
                           mime="application/pdf", key=f"pdf-{c['nome']}")
    else:
        st.warning("PDF não gerado nesta pasta.")
    for titulo, chave in (("Cobertura (coverage_review.md)", "coverage"),
                          ("Relatório de nota (rating_report.md)", "rating"),
                          ("Anti-invenção", "anti_invencao")):
        if c[chave]:
            with st.expander(titulo):
                st.markdown(c[chave])
    st.caption("Leia o currículo antes de usar: a checagem não zera o risco de invenção.")


def render():
    st.title("Currículos")
    st.subheader("Gerar currículo")
    entrada = st.text_area("Link ou texto da vaga", height=160)
    if st.button("Gerar", type="primary"):
        try:
            with st.spinner("Rodando /curriculo via claude -p (pode demorar)..."):
                st.session_state["curriculo"] = core.gerar(entrada)
        except ValueError as e:
            st.warning(str(e))
        except core.GeracaoFalhou as e:
            st.error(f"A geração não foi concluída:\n\n{e}")
    if "curriculo" in st.session_state:
        st.success(f"Gerado: {st.session_state['curriculo']['nome']}")
    st.subheader("Gerados")
    itens = core.listar()
    if not itens:
        st.info("Nenhum currículo ainda.")
    for c in itens:
        n = c["nota"]
        with st.expander(f"{c['nome']} · {f'{n:g}/10' if n is not None else 'sem nota'}"):
            _mostrar(c)
