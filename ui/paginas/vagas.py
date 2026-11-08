import streamlit as st

import vagas_core as core


def _mostrar(r):
    nota = r["nota"]
    st.metric("Nota de aderência", f"{nota:g}/10" if nota is not None else "?")
    st.subheader("Motivos")
    st.markdown(r["motivos"])
    st.subheader("Lacunas")
    st.markdown(r["lacunas"])
    st.caption(f"Salvo em private/vagas/{r['arquivo']}")


def render():
    st.title("Vagas")
    busca = core.ultima_busca()
    st.subheader("Busca mais recente")
    if not busca:
        st.info("Nenhuma busca ainda. Rode /busca no terminal.")
    else:
        st.caption(f"{busca['data']}: {len(busca['vagas'])} vaga(s)")
        for v in busca["vagas"]:
            st.markdown(f"**{v['titulo']}** · {v['empresa']} · {v['data']}  \n{v['link']}  \n{v['trecho']}")
    st.subheader("Triar uma vaga")
    entrada = st.text_area("Link ou texto da vaga", height=160)
    if st.button("Triar", type="primary"):
        try:
            with st.spinner("Rodando /triagem via claude -p..."):
                st.session_state["triagem"] = core.triar(entrada)
        except ValueError as e:
            st.warning(str(e))
        except core.TriagemFalhou as e:
            st.error(f"A triagem não foi concluída:\n\n{e}")
    if "triagem" in st.session_state:
        _mostrar(st.session_state["triagem"])
