import asyncio
import streamlit as st
import pandas as pd
from src.agent.dataops_agent import DataOpsAgent

st.set_page_config(page_title="DataOps Agent", layout="wide")

def renderizar_trace(trace: list[dict]) -> None:
    with st.expander(f"Rastro de ferramentas ({len(trace)} chamadas)", expanded=False):
        for passo in trace:
            st.markdown(f"**Turno {passo['turno']}: `{passo['ferramenta']}`** ({passo['tempo_ms']} ms)")
            # mostre os argumentos com st.json(passo["argumentos"])
            st.json(passo["argumentos"])

            guardrail = passo.get("guardrail")
            if guardrail is not None:
                # se guardrail["aprovada"], use st.success("Aprovado pelo guardrail");
                # senao st.error(f"Bloqueado pelo guardrail: {guardrail['motivo']}")
                if guardrail["aprovada"]:
                    st.success("Aprovado pelo guardrail")
                else:
                    st.error(f"Bloqueado pelo guardrail: {guardrail['motivo']}")

            if passo.get("query_sql"):
                st.code(passo["query_sql"], language="sql")

            if not passo["sucesso"]:
                erro = passo["resultado"].get("erro") if isinstance(passo["resultado"], dict) else passo["resultado"]
                st.warning(f"A ferramenta retornou erro: {erro}")
            st.divider()


def renderizar_dados(trace: list[dict]) -> None:
    """Mostra a tabela da ULTIMA consulta analitica bem-sucedida do turno."""
    consultas = [
        p for p in trace
        if p["ferramenta"] == "executar_query_analitica" and p["sucesso"] and isinstance(p["resultado"], dict)
    ]
    if not consultas:
        return
    resultado = consultas[-1]["resultado"]
    # monte um DataFrame com pd.DataFrame(resultado["linhas"]) e exiba com st.dataframe(..., width="stretch")
    st.dataframe(pd.DataFrame(resultado["linhas"]), width="stretch")

def inicializar_estado() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []      # o que aparece na tela: {"role", "content", "trace"}
    if "historico_llm" not in st.session_state:
        st.session_state.historico_llm = []  # a memoria do modelo (types.Content)


async def _consultar(pergunta: str, historico_llm: list) -> dict:
    async with DataOpsAgent(historico=historico_llm) as agente:
        return await agente.perguntar(pergunta)


def perguntar_ao_agente(pergunta: str) -> dict:
    """O Streamlit e sincrono: abrimos o agente (e o servidor MCP) a cada pergunta e fechamos ao final."""
    return asyncio.run(_consultar(pergunta, st.session_state.historico_llm))

def renderizar_mensagem(mensagem: dict) -> None:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])
        if mensagem.get("trace"):
            renderizar_dados(mensagem["trace"])
            renderizar_trace(mensagem["trace"])


def main() -> None:
    st.title("DataOps Agent")
    st.caption("Assistente de auditoria de dados: somente leitura, com rastreabilidade de cada ferramenta.")
    inicializar_estado()

    # redesenhe o historico: percorra st.session_state.messages e chame renderizar_mensagem em cada uma
    for mensagem in st.session_state.messages:
        renderizar_mensagem(mensagem)

    pergunta = st.chat_input("Pergunte algo sobre os dados...")
    if pergunta:
        # acrescente {"role": "user", "content": pergunta} ao estado e renderize a mensagem do usuario
        msg_usuario = {"role": "user", "content": pergunta}
        st.session_state.messages.append(msg_usuario)
        renderizar_mensagem(msg_usuario)

        with st.spinner("Consultando o agente..."):
            try:
                saida = perguntar_ao_agente(pergunta)
                resposta = {"role": "assistant", "content": saida["resposta"], "trace": saida["trace"]}
            except Exception as erro:
                resposta = {"role": "assistant", "content": f"Nao consegui concluir: {erro}", "trace": []}

        # acrescente "resposta" ao estado e renderize a mensagem do assistente
        st.session_state.messages.append(resposta)
        renderizar_mensagem(resposta)


if __name__ == "__main__":
    main()