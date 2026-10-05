import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
CAMINHO_DB = RAIZ / "data" / "dataops.db"


def conectar(caminho: Path = CAMINHO_DB) -> sqlite3.Connection:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(caminho)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON;")
    return conexao


DDL = """
CREATE TABLE IF NOT EXISTS usuarios (
    id           INTEGER PRIMARY KEY,
    nome         TEXT NOT NULL,
    email        TEXT,
    departamento TEXT NOT NULL,
    cargo        TEXT NOT NULL,
    criado_em    DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS dispositivos (
    id                  INTEGER PRIMARY KEY,
    usuario_id          INTEGER NOT NULL,
    hostname            TEXT NOT NULL,
    sistema_operacional TEXT NOT NULL,
    ip                  TEXT NOT NULL,
    criado_em           DATETIME NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

CREATE TABLE IF NOT EXISTS eventos (
    id             INTEGER PRIMARY KEY,
    usuario_id     INTEGER NOT NULL,
    dispositivo_id INTEGER NOT NULL,
    tipo_evento    TEXT NOT NULL,
    severidade     TEXT NOT NULL,
    ip_origem      TEXT NOT NULL,
    data_evento    DATETIME NOT NULL,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (dispositivo_id) REFERENCES dispositivos(id)
);

CREATE INDEX IF NOT EXISTS idx_dispositivos_usuario
    ON dispositivos(usuario_id);

CREATE INDEX IF NOT EXISTS idx_eventos_usuario
    ON eventos(usuario_id);

CREATE INDEX IF NOT EXISTS idx_eventos_dispositivo
    ON eventos(dispositivo_id);

CREATE INDEX IF NOT EXISTS idx_eventos_tipo_severidade
    ON eventos(tipo_evento, severidade);

CREATE INDEX IF NOT EXISTS idx_eventos_data
    ON eventos(data_evento);

CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL,
    email     TEXT,
    cidade    TEXT NOT NULL,
    criado_em DATETIME NOT NULL
);

CREATE TABLE IF NOT EXISTS produtos (
    id        INTEGER PRIMARY KEY,
    nome      TEXT NOT NULL,
    categoria TEXT NOT NULL,
    preco     REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS pedidos (
    id          INTEGER PRIMARY KEY,
    cliente_id  INTEGER NOT NULL,
    produto_id  INTEGER NOT NULL,
    quantidade  INTEGER NOT NULL,
    valor_total REAL NOT NULL,
    data_pedido DATETIME NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (produto_id) REFERENCES produtos(id)
);

CREATE INDEX IF NOT EXISTS idx_pedidos_cliente
    ON pedidos(cliente_id);

CREATE INDEX IF NOT EXISTS idx_pedidos_produto
    ON pedidos(produto_id);

CREATE INDEX IF NOT EXISTS idx_pedidos_data
    ON pedidos(data_pedido);
"""


def criar_tabelas(conexao: sqlite3.Connection) -> None:
    conexao.executescript(DDL)
    conexao.commit()


def resetar_banco() -> None:
    """Apaga o arquivo do banco (se existir) para recomecar do zero."""
    if CAMINHO_DB.exists():
        CAMINHO_DB.unlink()


if __name__ == "__main__":
    resetar_banco()
    with conectar() as conexao:
        criar_tabelas(conexao)
        tabelas = conexao.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        print("Tabelas criadas:", [linha["name"] for linha in tabelas])
        print(
            "Chaves estrangeiras ativas:",
            conexao.execute("PRAGMA foreign_keys").fetchone()[0],
        )
