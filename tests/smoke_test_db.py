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

        for tabela in ("usuarios", "dispositivos", "eventos"):
            total = escalar(conexao, f"SELECT COUNT(*) FROM {tabela}")
            checar(f"{tabela} tem 50+ linhas", total >= 50, f"({total})")

        checar(
            "JOIN eventos-usuarios funciona",
            escalar(conexao, "SELECT COUNT(*) FROM eventos e JOIN usuarios u ON e.usuario_id = u.id") > 0,
        )
        checar(
            "JOIN eventos-dispositivos funciona",
            escalar(conexao, "SELECT COUNT(*) FROM eventos e JOIN dispositivos d ON e.dispositivo_id = d.id") > 0,
        )

        checar("emails_nulos", escalar(conexao, "SELECT COUNT(*) FROM usuarios WHERE email IS NULL") == ANOMALIAS_ESPERADAS["emails_nulos"])
        checar("emails_duplicados", escalar(conexao, "SELECT COUNT(*) FROM usuarios WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1") > 0)
        checar("departamentos_vazios", escalar(conexao, "SELECT COUNT(*) FROM usuarios WHERE departamento = ''") == ANOMALIAS_ESPERADAS["departamentos_vazios"])
        checar("ips_dispositivos_duplicados", escalar(conexao, "SELECT COUNT(*) FROM dispositivos GROUP BY ip HAVING COUNT(*) > 1") > 0)
        checar("severidades_invalidas", escalar(conexao, "SELECT COUNT(*) FROM eventos WHERE severidade = 'invalida'") == ANOMALIAS_ESPERADAS["severidades_invalidas"])
        checar("datas_eventos_futuras", escalar(conexao, "SELECT COUNT(*) FROM eventos WHERE data_evento > date('now')") == ANOMALIAS_ESPERADAS["datas_eventos_futuras"])
        checar("ips_origem_vazios", escalar(conexao, "SELECT COUNT(*) FROM eventos WHERE ip_origem = ''") == ANOMALIAS_ESPERADAS["ips_origem_vazios"])

        try:
            conexao.execute(
                "INSERT INTO dispositivos (usuario_id, hostname, sistema_operacional, ip, criado_em) "
                "VALUES (?, ?, ?, ?, ?)",
                (99999, "host-fake", "Linux", "10.0.0.99", "2026-01-01"),
            )
            checar("insercao com usuario_id inexistente foi recusada", False)
        except sqlite3.IntegrityError:
            checar("insercao com usuario_id inexistente foi recusada", True)

    total_ok = sum(resultados)
    print(f"\n{total_ok}/{len(resultados)} verificacoes aprovadas")
    return 0 if all(resultados) else 1


if __name__ == "__main__":
    sys.exit(main())