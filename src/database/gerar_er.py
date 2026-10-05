from init_db import conectar

TIPOS = {"INTEGER": "int", "TEXT": "string", "REAL": "float", "DATETIME": "datetime"}


def listar_tabelas(conexao) -> list[str]:
    linhas = conexao.execute(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [linha["name"] for linha in linhas]


def gerar_mermaid() -> str:
    saida = ["erDiagram"]
    relacoes = []
    with conectar() as conexao:
        for tabela in listar_tabelas(conexao):
            saida.append(f"    {tabela} {{")
            for coluna in conexao.execute(f"PRAGMA table_info({tabela})"):
                tipo = TIPOS.get(coluna["type"].upper(), "string")
                pk = " PK" if coluna["pk"] == 1 else ""
                saida.append(f"        {tipo} {coluna['name']}{pk}")
            saida.append("    }")
            for linha in conexao.execute(f"PRAGMA foreign_key_list({tabela})"):
                relacoes.append(f"    {linha['table']} ||--o{{ {tabela} : \"{linha['from']}\"")
    return "\n".join(saida + relacoes)


if __name__ == "__main__":
    print(gerar_mermaid())