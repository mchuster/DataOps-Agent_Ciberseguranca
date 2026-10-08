import random
from datetime import date, timedelta

if __package__ in (None, ""):
    from init_db import CAMINHO_DB, conectar, criar_tabelas, resetar_banco
else:
    from .init_db import CAMINHO_DB, conectar, criar_tabelas, resetar_banco

SEMENTE = 42
QUANTIDADE_USUARIOS = 80
QUANTIDADE_DISPOSITIVOS = 60
QUANTIDADE_EVENTOS = 150

ANOMALIAS_ESPERADAS = {
    "emails_nulos": 6,
    "emails_duplicados": 3,
    "departamentos_vazios": 4,
    "ips_dispositivos_duplicados": 4,
    "severidades_invalidas": 5,
    "datas_eventos_futuras": 3,
    "ips_origem_vazios": 5,
}

DEPARTAMENTOS = ("TI", "Financeiro", "Recursos Humanos", "Operacoes", "Juridico")
CARGOS = ("Analista", "Especialista", "Coordenador", "Tecnico")
SISTEMAS_OPERACIONAIS = ("Linux", "Windows", "macOS")
TIPOS_EVENTO = ("login_falhou", "malware", "acesso_negado", "phishing", "anomalia")
SEVERIDADES = ("baixa", "media", "alta", "critica")


def gerar_dados() -> tuple[list[tuple], list[tuple], list[tuple]]:
    """Gera dados determinísticos, incluindo as anomalias esperadas."""
    aleatorio = random.Random(SEMENTE)
    hoje = date.today()

    usuarios = []
    for usuario_id in range(1, QUANTIDADE_USUARIOS + 1):
        email = None if usuario_id <= 6 else f"usuario{usuario_id}@empresa.local"
        if usuario_id in (7, 8, 9):
            email = "duplicado@empresa.local"
        departamento = "" if usuario_id <= 4 else aleatorio.choice(DEPARTAMENTOS)
        usuarios.append(
            (
                usuario_id,
                f"Usuario {usuario_id:03d}",
                email,
                departamento,
                aleatorio.choice(CARGOS),
                (hoje - timedelta(days=aleatorio.randint(1, 900))).isoformat(),
            )
        )

    dispositivos = []
    for dispositivo_id in range(1, QUANTIDADE_DISPOSITIVOS + 1):
        ip = f"10.0.{(dispositivo_id - 1) // 254}.{(dispositivo_id - 1) % 254 + 1}"
        if dispositivo_id > QUANTIDADE_DISPOSITIVOS - 4:
            ip = "10.0.0.10"
        dispositivos.append(
            (
                dispositivo_id,
                aleatorio.randint(1, QUANTIDADE_USUARIOS),
                f"host-{dispositivo_id:03d}",
                aleatorio.choice(SISTEMAS_OPERACIONAIS),
                ip,
                (hoje - timedelta(days=aleatorio.randint(1, 700))).isoformat(),
            )
        )

    eventos = []
    for evento_id in range(1, QUANTIDADE_EVENTOS + 1):
        data_evento = hoje - timedelta(days=aleatorio.randint(0, 365))
        if evento_id > QUANTIDADE_EVENTOS - 3:
            data_evento = hoje + timedelta(days=aleatorio.randint(1, 30))
        severidade = aleatorio.choice(SEVERIDADES)
        if evento_id > QUANTIDADE_EVENTOS - 5:
            severidade = "invalida"
        ip_origem = f"192.168.{aleatorio.randint(0, 20)}.{aleatorio.randint(1, 254)}"
        if evento_id > QUANTIDADE_EVENTOS - 5:
            ip_origem = ""
        eventos.append(
            (
                evento_id,
                aleatorio.randint(1, QUANTIDADE_USUARIOS),
                aleatorio.randint(1, QUANTIDADE_DISPOSITIVOS),
                aleatorio.choice(TIPOS_EVENTO),
                severidade,
                ip_origem,
                data_evento.isoformat(),
            )
        )

    return usuarios, dispositivos, eventos


def inserir_dados() -> None:
    resetar_banco()
    usuarios, dispositivos, eventos = gerar_dados()
    with conectar() as conexao:
        criar_tabelas(conexao)
        conexao.executemany(
            "INSERT INTO usuarios "
            "(id, nome, email, departamento, cargo, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            usuarios,
        )
        conexao.executemany(
            "INSERT INTO dispositivos "
            "(id, usuario_id, hostname, sistema_operacional, ip, criado_em) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            dispositivos,
        )
        conexao.executemany(
            "INSERT INTO eventos "
            "(id, usuario_id, dispositivo_id, tipo_evento, severidade, ip_origem, data_evento) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            eventos,
        )
        conexao.commit()
        consultas_contagem = {
            "usuarios": "SELECT COUNT(*) FROM usuarios",
            "dispositivos": "SELECT COUNT(*) FROM dispositivos",
            "eventos": "SELECT COUNT(*) FROM eventos",
        }
        for tabela, consulta in consultas_contagem.items():
            total = conexao.execute(consulta).fetchone()[0]
            print(f"{tabela}: {total}")
    print(f"Banco populado em: {CAMINHO_DB}")


if __name__ == "__main__":
    inserir_dados()
