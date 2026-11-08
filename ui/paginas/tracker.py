import pandas as pd
import streamlit as st

import curriculos_core as core


def render():
    st.title("Tracker")
    lido = core.ler_tracker()
    if lido is None:
        st.info("private/tracker.csv não existe. Rode make setup.")
        return
    cab, linhas = lido
    st.caption("private/tracker.csv é a fonte de verdade e abre no Excel. Novas linhas: edite aqui ou use /enviei.")
    df = pd.DataFrame(linhas, columns=cab).fillna("")
    editado = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)
    if st.button("Salvar", type="primary"):
        core.salvar_tracker(core.PRIVATE, cab, editado.to_dict("records"))
        st.success("Tracker salvo.")
