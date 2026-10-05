# Dicionario de Dados: Ciberseguranca - Eventos

Trio: Mateus Huster, Deric Gabriel , Leonardo Wingert |  Banco: data/dataops.db (SQLite)

## Tabela: usuarios

Descricao: uma linha por usuario cadastrado na organizacao.

| Coluna       | Tipo     | Restricoes  | Descricao                                |
| ------------ | -------- | ----------- | ---------------------------------------- |
| id           | INTEGER  | PRIMARY KEY | Identificador do usuario                 |
| nome         | TEXT     | NOT NULL    | Nome completo do usuario                 |
| email        | TEXT     | NOT NULL    | E-mail corporativo do usuario            |
| departamento | TEXT     | NOT NULL    | Departamento ao qual o usuario pertence  |
| cargo        | TEXT     | NOT NULL    | Cargo exercido pelo usuario              |
| criado_em    | DATETIME | NOT NULL    | Data de cadastro do usuario (AAAA-MM-DD) |

## Tabela: dispositivos

Descricao: uma linha por dispositivo utilizado pelos usuarios da organizacao.

| Coluna              | Tipo     | Restricoes                           | Descricao                                    |
| ------------------- | -------- | ------------------------------------ | -------------------------------------------- |
| id                  | INTEGER  | PRIMARY KEY                          | Identificador do dispositivo                 |
| usuario_id          | INTEGER  | NOT NULL, FOREIGN KEY -> usuarios.id | Usuario responsavel pelo dispositivo         |
| hostname            | TEXT     | NOT NULL                             | Nome do dispositivo na rede                  |
| sistema_operacional | TEXT     | NOT NULL                             | Sistema operacional instalado                |
| ip                  | TEXT     | NOT NULL                             | Endereco IP atribuido ao dispositivo         |
| criado_em           | DATETIME | NOT NULL                             | Data de cadastro do dispositivo (AAAA-MM-DD) |

## Tabela: eventos

Descricao: uma linha por evento de seguranca registrado em um dispositivo.

| Coluna         | Tipo     | Restricoes                               | Descricao                           |
| -------------- | -------- | ---------------------------------------- | ----------------------------------- |
| id             | INTEGER  | PRIMARY KEY                              | Identificador do evento             |
| usuario_id     | INTEGER  | NOT NULL, FOREIGN KEY -> usuarios.id     | Usuario relacionado ao evento       |
| dispositivo_id | INTEGER  | NOT NULL, FOREIGN KEY -> dispositivos.id | Dispositivo que registrou o evento  |
| tipo_evento    | TEXT     | NOT NULL                                 | Tipo do evento de seguranca         |
| severidade     | TEXT     | NOT NULL                                 | Nivel de severidade do evento       |
| ip_origem      | TEXT     | NOT NULL                                 | Endereco IP que originou o evento   |
| data_evento    | DATETIME | NOT NULL                                 | Data e hora em que o evento ocorreu |

## Relacionamentos

* usuarios 1 --- N dispositivos
* usuarios 1 --- N eventos
* dispositivos 1 --- N eventos

## Perguntas de negocio que o assistente precisara responder

1. Qual tipo de evento de seguranca ocorre com maior frequencia?
2. Qual dispositivo registrou a maior quantidade de eventos?
3. Qual usuario possui a maior quantidade de eventos de alta severidade?
4. Qual departamento concentra a maior quantidade de eventos de seguranca?
5. Quais dispositivos registraram eventos de mais de um tipo?

## Anomalias que planejamos injetar (para o agente encontrar)

* 5 eventos com severidade invalida
* 4 dispositivos com IP duplicado
* 3 eventos com data futura
* 5 eventos com IP de origem vazio
* 4 usuarios com departamento vazio
