import json
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
LOG_FEEDBACK = RAIZ / "logs" / "feedback.jsonl"


def registrar_avaliacao(indice_mensagem: int, pergunta: str, resposta: str, tipo_feedback: str) -> None:
    """Registra avaliacao qualitativa do usuario em arquivo JSONL."""
    LOG_FEEDBACK.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "mensagem_idx": indice_mensagem,
        "pergunta": pergunta,
        "resposta": resposta,
        "feedback": tipo_feedback,
    }
    with open(LOG_FEEDBACK, "a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def exibir_botoes_feedback(indice: int, pergunta: str, resposta: str) -> None:
    """Renderiza botoes de like/dislike com icones vetoriais SVG abaixo da resposta do modelo."""
    col1, col2, _ = st.columns([1, 1, 16])
    with col1:
        if st.button("", icon=":material/thumb_up:", key=f"like_{indice}", help="Feedback positivo", type="tertiary"):
            registrar_avaliacao(indice, pergunta, resposta, "positivo")
            st.toast("Obrigado pelo feedback positivo!", icon=":material/thumb_up:")
    with col2:
        if st.button("", icon=":material/thumb_down:", key=f"dislike_{indice}", help="Feedback negativo", type="tertiary"):
            registrar_avaliacao(indice, pergunta, resposta, "negativo")
            st.toast("Feedback registrado. Vamos aprimorar!", icon=":material/thumb_down:")

