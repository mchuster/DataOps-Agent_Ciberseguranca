import sqlite3
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src" / "database"))

from init_db import CAMINHO_DB, conectar  # noqa: E402
from seed_data import ANOMALIAS_ESPERADAS  # noqa: E402

resultados = []


def checar(nome: str, condicao: bool, detalhe: str = "") -> None:
    resultados.append(condicao)
    print(f"[{'OK' if condicao else 'FALHA'}] {nome} {detalhe}")


def escalar(conexao: sqlite3.Connection, sql: str):
    return conexao.execute(sql).fetchone()[0]


def main() -> int:
    checar("arquivo dataops.db existe", CAMINHO_DB.exists())
    if not CAMINHO_DB.exists():
        print("Rode primeiro: python src/database/init_db.py && python src/database/seed_data.py")
        return 1

    with conectar() as conexao:
        checar("integridade do arquivo", escalar(conexao, "PRAGMA integrity_check") == "ok")

        for tabela in ("clientes", "produtos", "pedidos"):
            total = escalar(conexao, f"SELECT COUNT(*) FROM {tabela}")
            checar(f"{tabela} tem 50+ linhas", total >= 50, f"({total})")

        checar("JOIN pedidos-clientes funciona", escalar(conexao, "SELECT COUNT(*) FROM pedidos p JOIN clientes c ON p.cliente_id = c.id") > 0)

        checar("clientes_sem_email", escalar(conexao, "SELECT COUNT(*) FROM clientes WHERE email IS NULL") > 0)
        checar("produtos_preco_zero", escalar(conexao, "SELECT COUNT(*) FROM produtos WHERE preco = 0") > 0)
        checar("pedidos_valor_negativo", escalar(conexao, "SELECT COUNT(*) FROM pedidos WHERE valor_total < 0") > 0)
        checar("pedidos_data_futura", escalar(conexao, "SELECT COUNT(*) FROM pedidos WHERE data_pedido > date('now')") > 0)
        checar("emails_duplicados", escalar(conexao, "SELECT COUNT(*) FROM clientes WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1") > 0)

        try:
            conexao.execute("INSERT INTO pedidos (cliente_id, data_pedido, valor_total) VALUES (?, ?, ?)", (9999, "2024-01-01", 100))
            checar("insercao com cliente_id inexistente foi recusada", False)
        except sqlite3.IntegrityError:
            checar("insercao com cliente_id inexistente foi recusada", True)

    total_ok = sum(resultados)
    print(f"\n{total_ok}/{len(resultados)} verificacoes aprovadas")
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())