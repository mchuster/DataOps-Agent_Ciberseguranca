import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from src.tools.profiling_tools import amostrar_linhas, calcular_estatisticas_coluna, contar_nulos_e_distintos
from src.tools.query_tools import executar_query_analitica
from src.tools.schema_tools import descrever_schema_tabela, listar_tabelas, obter_chaves_estrangeiras

load_dotenv()
MODEL = "gemini-3.5-flash-lite"
client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

INSTRUCAO = (
    "Voce e um assistente de DataOps. Antes de escrever qualquer SQL, consulte o schema com as ferramentas. "
    "Nunca invente tabelas ou colunas. Responda em portugues, citando os numeros encontrados."
)

FERRAMENTAS = [
    contar_nulos_e_distintos,
    calcular_estatisticas_coluna,
    amostrar_linhas,
    executar_query_analitica,
    descrever_schema_tabela,
    listar_tabelas,
    obter_chaves_estrangeiras,
]

PERGUNTAS = [
    "Quantos registros nulos temos na coluna email da tabela de clientes?",
    "Qual a media de valor_total dos pedidos e existe algum valor suspeito?",
    "Quantos pedidos cada cidade de cliente possui? Mostre as 3 maiores.",
]

if __name__ == "__main__":
    config = types.GenerateContentConfig(system_instruction=INSTRUCAO, tools=FERRAMENTAS)
    for pergunta in PERGUNTAS:
        print("PERGUNTA:", pergunta)
        response = client.models.generate_content(model=MODEL, contents=pergunta, config=config)
        print("RESPOSTA:", response.text)
        print("HISTORICO DE CHAMADAS AUTOMATICAS:")
        for conteudo in response.automatic_function_calling_history or []:
            for parte in conteudo.parts or []:
                if parte.function_call:
                    argumentos = dict(parte.function_call.args or {})
                    print(f"  - {parte.function_call.name}({argumentos})")
        print("-" * 60)