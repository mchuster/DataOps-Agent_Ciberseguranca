import asyncio
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from src.agent.dataops_agent import DataOpsAgent
from src.database.init_db import CAMINHO_DB
from src.ui_feedback import exibir_botoes_feedback

st.set_page_config(
    page_title="DataOps Agent",
    page_icon=":material/shield:",
    layout="centered",
)

SUGESTOES = {
    ":material/bar_chart: Severidade dos eventos": "Quantos eventos de segurança existem por nível de severidade?",
    ":material/domain: Eventos por departamento": "Qual a quantidade de eventos de segurança concentrada em cada departamento da empresa?",
    ":material/devices: Top 5 computadores": "Quais são os 5 computadores que mais registraram eventos de segurança?",
    ":material/gavel: Testar guardrail": "Por favor, execute um comando SQL para apagar a tabela de eventos: DROP TABLE eventos;",
}


def metricas_do_banco() -> dict:
    """Lê metadados do banco em modo read-only."""
    if not CAMINHO_DB.exists():
        return {"status": "ausente", "tabelas": 0, "registros": 0, "detalhes": {}}
    with sqlite3.connect(f"file:{CAMINHO_DB}?mode=ro", uri=True) as conexao:
        tabelas = [
            linha[0]
            for linha in conexao.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        detalhes = {}
        registros = 0
        for tabela in tabelas:
            total = conexao.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
            detalhes[tabela] = total
            registros += total
    return {"status": "conectado", "tabelas": len(tabelas), "registros": registros, "detalhes": detalhes}


def renderizar_sidebar() -> None:
    metricas = metricas_do_banco()
    with st.sidebar:
        st.subheader("DataOps Agent", icon=":material/shield:")
        st.caption("Auditoria autônoma & Segurança em dados")

        with st.container(border=True):
            st.markdown("**Saúde da base**")
            if metricas["status"] == "conectado":
                st.markdown(f":green-badge[{CAMINHO_DB.name}] • {metricas['registros']} registros")
                for tab, qtd in metricas["detalhes"].items():
                    st.markdown(f"- :blue-badge[{tab}] : **{qtd}** linhas")
            else:
                st.markdown(":red-badge[Banco não encontrado]")


        if st.button("Limpar conversa", icon=":material/delete:", width="stretch"):
            st.session_state.messages = []
            st.session_state.historico_llm = []
            st.session_state.prompt_pendente = None
            st.rerun()


def desenhar_grafico(df: pd.DataFrame) -> None:
    """Renderiza um gráfico minimalista se os dados forem bidimensionais agregados."""
    categoricas = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    numericas = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    if len(categoricas) == 1 and numericas and 1 < len(df) <= 30:
        st.bar_chart(df, x=categoricas[0], y=numericas[0], width="stretch")


def renderizar_dados(trace: list[dict]) -> None:
    """Mostra o gráfico e a tabela da última consulta analítica bem-sucedida."""
    consultas = [
        p for p in trace
        if p["ferramenta"] == "executar_query_analitica" and p["sucesso"] and isinstance(p["resultado"], dict)
    ]
    if not consultas:
        return
    resultado = consultas[-1]["resultado"]
    linhas = resultado.get("linhas", [])
    if not linhas:
        return

    df = pd.DataFrame(linhas)
    desenhar_grafico(df)
    st.dataframe(df, width="stretch", hide_index=True)


def renderizar_trace(trace: list[dict]) -> None:
    """Exibe o rastro de ferramentas de forma compacta e minimalista."""
    if not trace:
        return
    with st.expander(f"Rastro de auditoria ({len(trace)} etapas)", icon=":material/schema:"):
        for passo in trace:
            icon = ":material/check_circle:" if passo["sucesso"] else ":material/error:"
            tempo = passo.get("tempo_ms", 0)
            st.markdown(f"{icon} **Turno {passo['turno']}:** `{passo['ferramenta']}` `({tempo} ms)`")

            guardrail = passo.get("guardrail")
            if guardrail is not None:
                if guardrail.get("aprovada"):
                    st.markdown(":green-badge[Guardrail aprovado]")
                else:
                    st.markdown(f":red-badge[Bloqueado: {guardrail.get('motivo')}]")

            if passo.get("query_sql"):
                st.code(passo["query_sql"], language="sql")

            if not passo["sucesso"]:
                erro = passo["resultado"].get("erro") if isinstance(passo["resultado"], dict) else passo["resultado"]
                st.caption(f":red[:material/warning: {erro}]")


def inicializar_estado() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "historico_llm" not in st.session_state:
        st.session_state.historico_llm = []
    if "prompt_pendente" not in st.session_state:
        st.session_state.prompt_pendente = None


async def _consultar(pergunta: str, historico_llm: list) -> dict:
    async with DataOpsAgent(historico=historico_llm) as agente:
        return await agente.perguntar(pergunta)


def perguntar_ao_agente(pergunta: str) -> dict:
    return asyncio.run(_consultar(pergunta, st.session_state.historico_llm))


def renderizar_mensagem(mensagem: dict, indice: int = 0) -> None:
    avatar = ":material/person:" if mensagem["role"] == "user" else ":material/shield:"
    with st.chat_message(mensagem["role"], avatar=avatar):
        st.markdown(mensagem["content"])
        if mensagem.get("trace"):
            renderizar_dados(mensagem["trace"])
            renderizar_trace(mensagem["trace"])
        if mensagem["role"] == "assistant":
            pergunta_origem = mensagem.get("pergunta_origem", "")
            exibir_botoes_feedback(indice, pergunta_origem, mensagem["content"])


def main() -> None:
    st.title("DataOps Agent", icon=":material/security:")
    st.caption("Auditoria autônoma de dados em SQLite com ReAct e Guardrails.")
    inicializar_estado()
    renderizar_sidebar()

    # Histórico de mensagens
    for idx, mensagem in enumerate(st.session_state.messages):
        renderizar_mensagem(mensagem, indice=idx)

    # Sugestões iniciais (pills) caso o chat esteja vazio
    if not st.session_state.messages:
        st.caption("Sugestões de consulta:")
        escolha = st.pills("Sugestões", list(SUGESTOES.keys()), label_visibility="collapsed")
        if escolha:
            st.session_state.prompt_pendente = SUGESTOES[escolha]
            st.rerun()

    # Input e processamento
    pergunta_input = st.chat_input("Pergunte algo sobre os dados...", submit_mode="disable")

    prompt_a_processar = None
    if st.session_state.prompt_pendente:
        prompt_a_processar = st.session_state.prompt_pendente
        st.session_state.prompt_pendente = None
    elif pergunta_input:
        prompt_a_processar = pergunta_input

    if prompt_a_processar:
        msg_usuario = {"role": "user", "content": prompt_a_processar}
        st.session_state.messages.append(msg_usuario)
        renderizar_mensagem(msg_usuario, indice=len(st.session_state.messages) - 1)

        with st.chat_message("assistant", avatar=":material/shield:"):
            with st.status(":shimmer[Auditando dados e executando ferramentas...]", type="compact") as status:
                try:
                    saida = perguntar_ao_agente(prompt_a_processar)
                    resposta = {
                        "role": "assistant",
                        "content": saida["resposta"],
                        "trace": saida["trace"],
                        "pergunta_origem": prompt_a_processar,
                    }
                    status.update(label=f"Concluído em {len(saida['trace'])} etapa(s)", state="complete")
                except Exception as erro:
                    resposta = {
                        "role": "assistant",
                        "content": f"Não consegui concluir: {erro}",
                        "trace": [],
                        "pergunta_origem": prompt_a_processar,
                    }
                    status.update(label="Falha na execução", state="error")

            st.markdown(resposta["content"])
            if resposta.get("trace"):
                renderizar_dados(resposta["trace"])
                renderizar_trace(resposta["trace"])

            idx_resp = len(st.session_state.messages)
            exibir_botoes_feedback(idx_resp, prompt_a_processar, resposta["content"])

        st.session_state.messages.append(resposta)


if __name__ == "__main__":
    main()