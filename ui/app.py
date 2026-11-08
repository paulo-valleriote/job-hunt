"""Entrada da UI: `make ui` (Streamlit só em localhost). Navegação pronta para as 3 telas."""
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))
from paginas import vagas, curriculos, tracker  # noqa: E402

st.set_page_config(page_title="Job Hunt", layout="wide")
st.navigation([
    st.Page(vagas.render, title="Vagas", icon="🔎", url_path="vagas", default=True),
    st.Page(curriculos.render, title="Currículos", icon="📄", url_path="curriculos"),
    st.Page(tracker.render, title="Tracker", icon="📋", url_path="tracker"),
]).run()
