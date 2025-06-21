"""
Sistema de Gerenciamento de Dados Agrícolas
Implementação de operações CRUD para o banco de dados agrícola

Este script implementa operações CRUD (Create, Read, Update, Delete) para
manipular dados agrícolas em um banco Oracle existente.

Autor: FarmTech Solutions
Data: Maio 2025
"""

import oracledb
import csv
import os
import logging
import sys
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional, Union

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agricola_db.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# --- EXCEÇÕES PERSONALIZADAS ---
class DatabaseError(Exception):
    """Exceção base para erros de banco de dados."""
    pass


class ValidationError(Exception):
    """Exceção para erros de validação de dados."""
    pass


class AgricolaDatabaseManager:
    """
    Classe responsável pelo gerenciamento do banco de dados agrícola.
    Implementa operações CRUD e funções de análise de dados.
    """

    def __init__(self):
        """
        Inicializa o gerenciador de banco de dados Oracle.
        """
        # Configurações de conexão Oracle
        self.host = "localhost"
        self.port = 1522
        self.service_name = "ORCLPDB"
        self.user = "RCOSTA"
        self.password = "Rcosta@1980"

        self.conn = None
        self.cursor = None

    def connect(self):
        """Estabelece conexão com o banco de dados Oracle."""
        try:
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            self.conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)
            self.cursor = self.conn.cursor()
            logger.info("Conexão com o banco de dados estabelecida com sucesso")
        except oracledb.DatabaseError as e:
            error, = e.args
            logger.error(f"Erro Oracle (ORA-{error.code}): {error.message}")
            raise DatabaseError(f"Falha na conexão com o banco de dados (ORA-{error.code})") from e

    def disconnect(self):
        """Fecha a conexão com o banco de dados."""
        if self.conn:
            if self.cursor:
                self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Conexão com o banco de dados encerrada")

    def executar_sql(
            self,
            sql: str,
            params: Optional[List[Any]] = None,
            operacao: str = 'insert'
    ) -> Union[int, List[Dict[str, Any]], Dict[str, Any], None]:
        """
        Executa operações SQL no banco de dados com tratamento de erros.

        Args:
            sql (str): Comando SQL a ser executado.
            params (Optional[List[Any]]): Lista de parâmetros para o comando SQL.
            operacao (str): Tipo de operação ('insert', 'select_one', 'select_all', 'update', 'delete').

        Returns:
            Union[int, List[Dict[str, Any]], Dict[str, Any], None]:
                - Para 'select_all': Lista de dicionários com os resultados
                - Para 'select_one': Um dicionário com o resultado
                - Para outros: Número de linhas afetadas ou None

        Raises:
            DatabaseError: Em caso de falha na execução SQL.
        """
        try:
            if params is None:
                params = []

            if operacao in ('insert', 'update', 'delete'):
                self.cursor.execute(sql, params)
                affected_rows = self.cursor.rowcount
                self.conn.commit()
                logger.info(f"Operação realizada: {sql.split()[0]}, linhas afetadas: {affected_rows}")
                return affected_rows

            elif operacao == 'select_one':
                self.cursor.execute(sql, params)
                row = self.cursor.fetchone()
                if row:
                    columns = [desc[0] for desc in self.cursor.description]
                    return dict(zip(columns, row))
                return None

            elif operacao == 'select_all':
                self.cursor.execute(sql, params)
                rows = self.cursor.fetchall()
                if rows:
                    columns = [desc[0] for desc in self.cursor.description]
                    return [dict(zip(columns, row)) for row in rows]
                return []

        except oracledb.DatabaseError as e:
            error, = e.args
            logger.error(f"Erro Oracle (ORA-{error.code}): {error.message}")
            self.conn.rollback()
            raise DatabaseError(f"Falha no banco de dados (ORA-{error.code})") from e

    def import_csv_data(self, csv_dir: str):
        """
        Importa dados de arquivos CSV para o banco de dados.

        Args:
            csv_dir: Diretório contendo os arquivos CSV
        """
        self.connect()

        # Ordem de importação para respeitar as chaves estrangeiras
        tables = [
            "t_culturas",
            "t_sensores",
            "t_medicoes",
            "t_sugestoes",
            "t_aplicacoes"
        ]

        for table in tables:
            csv_file = os.path.join(csv_dir, f"{table}.csv")
            if not os.path.exists(csv_file):
                logger.warning(f"Arquivo não encontrado: {csv_file}")
                continue

            with open(csv_file, 'r') as f:
                csv_reader = csv.reader(f)
                headers = next(csv_reader)  # Lê o cabeçalho

                # Prepara a instrução SQL de inserção
                placeholders = ', '.join([f':{i + 1}' for i in range(len(headers))])
                insert_query = f"INSERT INTO {table.upper()} ({', '.join(headers)}) VALUES ({placeholders})"

                # Insere os dados
                for row in csv_reader:
                    try:
                        # Converte a lista de valores para uma lista de parâmetros posicionais
                        self.executar_sql(insert_query, row, 'insert')
                    except DatabaseError as e:
                        logger.error(f"Erro ao inserir dados em {table}: {e}")
                        logger.error(f"Dados: {row}")

            logger.info(f"Dados importados com sucesso para a tabela {table.upper()}")

        self.disconnect()

    # Operações CRUD para T_CULTURAS

    def create_cultura(self, desc_cultura: str, tamanho_cultura: float, data_prev_colheita: str = None) -> int:
        """
        Insere uma nova cultura no banco de dados.

        Args:
            desc_cultura: Descrição da cultura
            tamanho_cultura: Tamanho da cultura em hectares
            data_prev_colheita: Data prevista para colheita (opcional, formato YYYY-MM-DD)

        Returns:
            ID da cultura inserida
        """
        self.connect()

        try:
            # Obtém o próximo código de cultura
            self.cursor.execute("SELECT NVL(MAX(cod_cultura), 0) + 1 FROM T_CULTURAS")
            new_cod = self.cursor.fetchone()[0]

            # Insere a nova cultura com tratamento adequado para a data
            if data_prev_colheita is not None:
                sql = """
                INSERT INTO T_CULTURAS (
                    cod_cultura, desc_cultura, tamanho_cultura, data_prev_colheita
                ) VALUES (
                    :1, :2, :3, TO_DATE(:4, 'YYYY-MM-DD')
                )
                """
                params = [new_cod, desc_cultura, tamanho_cultura, data_prev_colheita]
            else:
                sql = """
                INSERT INTO T_CULTURAS (
                    cod_cultura, desc_cultura, tamanho_cultura, data_prev_colheita
                ) VALUES (
                    :1, :2, :3, NULL
                )
                """
                # CORREÇÃO: Remover o parâmetro data_prev_colheita quando for NULL
                params = [new_cod, desc_cultura, tamanho_cultura]

            self.executar_sql(sql, params, 'insert')
            logger.info(f"Nova cultura inserida com ID: {new_cod}")

            return new_cod

        except Exception as e:
            logger.error(f"Erro ao criar cultura: {e}")
            raise
        finally:
            self.disconnect()

    def read_cultura(self, cod_cultura: int = None) -> List[Dict[str, Any]]:
        """
        Recupera dados de culturas do banco de dados.

        Args:
            cod_cultura: Código da cultura (opcional, se não fornecido retorna todas)

        Returns:
            Lista de dicionários com os dados das culturas
        """
        self.connect()

        try:
            if cod_cultura is not None:
                sql = "SELECT cod_cultura, desc_cultura, tamanho_cultura, TO_CHAR(data_prev_colheita, 'YYYY-MM-DD') as data_prev_colheita FROM T_CULTURAS WHERE cod_cultura = :1"
                params = [cod_cultura]
                result = self.executar_sql(sql, params, 'select_all')
            else:
                sql = "SELECT cod_cultura, desc_cultura, tamanho_cultura, TO_CHAR(data_prev_colheita, 'YYYY-MM-DD') as data_prev_colheita FROM T_CULTURAS"
                result = self.executar_sql(sql, [], 'select_all')

            return result

        except Exception as e:
            logger.error(f"Erro ao ler cultura(s): {e}")
            return []
        finally:
            self.disconnect()

    def update_cultura(self, cod_cultura: int, desc_cultura: str = None,
                       tamanho_cultura: float = None, data_prev_colheita: str = None) -> bool:
        """
        Atualiza dados de uma cultura existente.

        Args:
            cod_cultura: Código da cultura a ser atualizada
            desc_cultura: Nova descrição da cultura (opcional)
            tamanho_cultura: Novo tamanho da cultura (opcional)
            data_prev_colheita: Nova data prevista para colheita (opcional, formato YYYY-MM-DD)

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Constrói a consulta SQL dinamicamente com base nos parâmetros fornecidos
            update_fields = []
            params = []
            param_index = 1

            if desc_cultura is not None:
                update_fields.append(f"desc_cultura = :{param_index}")
                params.append(desc_cultura)
                param_index += 1

            if tamanho_cultura is not None:
                update_fields.append(f"tamanho_cultura = :{param_index}")
                params.append(tamanho_cultura)
                param_index += 1

            if data_prev_colheita is not None:
                update_fields.append(f"data_prev_colheita = TO_DATE(:{param_index}, 'YYYY-MM-DD')")
                params.append(data_prev_colheita)
                param_index += 1
            elif data_prev_colheita == "":  # Caso especial para limpar a data
                update_fields.append("data_prev_colheita = NULL")
                # Não adiciona parâmetro para NULL

            if not update_fields:
                logger.warning("Nenhum campo fornecido para atualização")
                return False

            # Adiciona o código da cultura como último parâmetro
            params.append(cod_cultura)

            sql = f"UPDATE T_CULTURAS SET {', '.join(update_fields)} WHERE cod_cultura = :{param_index}"

            affected_rows = self.executar_sql(sql, params, 'update')
            success = affected_rows > 0

            if success:
                logger.info(f"Cultura {cod_cultura} atualizada com sucesso")
            else:
                logger.warning(f"Nenhuma cultura encontrada com o código {cod_cultura}")

            return success

        except Exception as e:
            logger.error(f"Erro ao atualizar cultura: {e}")
            return False
        finally:
            self.disconnect()

    def delete_cultura(self, cod_cultura: int) -> bool:
        """
        Remove uma cultura do banco de dados.

        Args:
            cod_cultura: Código da cultura a ser removida

        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Verifica se existem sensores associados a esta cultura
            sql_check_sensores = "SELECT COUNT(*) FROM T_SENSORES WHERE cod_cultura = :1"
            self.cursor.execute(sql_check_sensores, [cod_cultura])
            if self.cursor.fetchone()[0] > 0:
                logger.warning(
                    f"Não é possível excluir a cultura {cod_cultura} pois existem sensores associados a ela.")
                return False

            # Verifica se existem aplicações associadas a esta cultura
            sql_check_aplicacoes = "SELECT COUNT(*) FROM T_APLICACOES WHERE cod_cultura = :1"
            self.cursor.execute(sql_check_aplicacoes, [cod_cultura])
            if self.cursor.fetchone()[0] > 0:
                logger.warning(
                    f"Não é possível excluir a cultura {cod_cultura} pois existem aplicações associadas a ela.")
                return False

            # Remove a cultura
            sql = "DELETE FROM T_CULTURAS WHERE cod_cultura = :1"
            affected_rows = self.executar_sql(sql, [cod_cultura], 'delete')
            success = affected_rows > 0

            if success:
                logger.info(f"Cultura {cod_cultura} removida com sucesso")
            else:
                logger.warning(f"Nenhuma cultura encontrada com o código {cod_cultura}")

            return success

        except Exception as e:
            logger.error(f"Erro ao excluir cultura: {e}")
            return False
        finally:
            self.disconnect()

    # Operações CRUD para T_SENSORES

    def create_sensor(self, nm_sensor: str, tipo_sensor: str, objetivo_sensor: str,
                      fab_sensor: str, modelo_sensor: str, data_instalacao: str,
                      latitude_instalacao: float, longitude_instalacao: float,
                      valor_minimo: float, valor_maximo: float, unidade: str,
                      cod_cultura: int) -> int:
        """
        Insere um novo sensor no banco de dados.

        Args:
            nm_sensor: Nome do sensor
            tipo_sensor: Tipo do sensor (2 caracteres)
            objetivo_sensor: Objetivo do sensor
            fab_sensor: Fabricante do sensor
            modelo_sensor: Modelo do sensor
            data_instalacao: Data de instalação (formato YYYY-MM-DD)
            latitude_instalacao: Latitude da instalação
            longitude_instalacao: Longitude da instalação
            valor_minimo: Valor mínimo de leitura
            valor_maximo: Valor máximo de leitura
            unidade: Unidade de medida (2 caracteres)
            cod_cultura: Código da cultura associada

        Returns:
            ID do sensor inserido
        """
        self.connect()

        try:
            # Obtém o próximo código de sensor
            self.cursor.execute("SELECT NVL(MAX(cod_sensor), 0) + 1 FROM T_SENSORES")
            new_cod = self.cursor.fetchone()[0]

            # Insere o novo sensor com tratamento adequado para a data
            if data_instalacao is not None:
                sql = """
                INSERT INTO T_SENSORES (
                    cod_sensor, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor, 
                    modelo_sensor, data_instalacao, latitude_instalacao, longitude_instalacao, 
                    valor_minimo, valor_maximo, unidade, cod_cultura
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, TO_DATE(:7, 'YYYY-MM-DD'), :8, :9, :10, :11, :12, :13
                )
                """
                params = [
                    new_cod, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor,
                    modelo_sensor, data_instalacao, latitude_instalacao, longitude_instalacao,
                    valor_minimo, valor_maximo, unidade, cod_cultura
                ]
            else:
                sql = """
                INSERT INTO T_SENSORES (
                    cod_sensor, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor, 
                    modelo_sensor, data_instalacao, latitude_instalacao, longitude_instalacao, 
                    valor_minimo, valor_maximo, unidade, cod_cultura
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, NULL, :7, :8, :9, :10, :11, :12
                )
                """
                params = [
                    new_cod, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor,
                    modelo_sensor, latitude_instalacao, longitude_instalacao,
                    valor_minimo, valor_maximo, unidade, cod_cultura
                ]

            self.executar_sql(sql, params, 'insert')
            logger.info(f"Novo sensor inserido com ID: {new_cod}")

            return new_cod

        except Exception as e:
            logger.error(f"Erro ao criar sensor: {e}")
            raise
        finally:
            self.disconnect()

    def read_sensor(self, cod_sensor: int = None) -> List[Dict[str, Any]]:
        """
        Recupera dados de sensores do banco de dados.

        Args:
            cod_sensor: Código do sensor (opcional, se não fornecido retorna todos)

        Returns:
            Lista de dicionários com os dados dos sensores
        """
        self.connect()

        try:
            if cod_sensor is not None:
                sql = """
                SELECT cod_sensor, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor, 
                       modelo_sensor, TO_CHAR(data_instalacao, 'YYYY-MM-DD') as data_instalacao, 
                       latitude_instalacao, longitude_instalacao, valor_minimo, valor_maximo, 
                       unidade, cod_cultura 
                FROM T_SENSORES 
                WHERE cod_sensor = :1
                """
                params = [cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            else:
                sql = """
                SELECT cod_sensor, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor, 
                       modelo_sensor, TO_CHAR(data_instalacao, 'YYYY-MM-DD') as data_instalacao, 
                       latitude_instalacao, longitude_instalacao, valor_minimo, valor_maximo, 
                       unidade, cod_cultura 
                FROM T_SENSORES
                """
                result = self.executar_sql(sql, [], 'select_all')

            return result

        except Exception as e:
            logger.error(f"Erro ao ler sensor(es): {e}")
            return []
        finally:
            self.disconnect()

    def update_sensor(self, cod_sensor: int, **kwargs) -> bool:
        """
        Atualiza dados de um sensor existente.

        Args:
            cod_sensor: Código do sensor a ser atualizado
            **kwargs: Pares chave-valor com os campos a serem atualizados

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Campos válidos para atualização
            valid_fields = [
                'nm_sensor', 'tipo_sensor', 'objetivo_sensor', 'fab_sensor',
                'modelo_sensor', 'data_instalacao', 'latitude_instalacao',
                'longitude_instalacao', 'valor_minimo', 'valor_maximo',
                'unidade', 'cod_cultura'
            ]

            # Filtra apenas os campos válidos
            update_fields = []
            params = []
            param_index = 1

            for field, value in kwargs.items():
                if field in valid_fields and value is not None:
                    # Tratamento especial para campos de data
                    if field == 'data_instalacao':
                        update_fields.append(f"{field} = TO_DATE(:{param_index}, 'YYYY-MM-DD')")
                    else:
                        update_fields.append(f"{field} = :{param_index}")
                    params.append(value)
                    param_index += 1
                elif field in valid_fields and value == "":  # Caso especial para limpar campos
                    if field == 'data_instalacao':
                        update_fields.append(f"{field} = NULL")
                        # Não adiciona parâmetro para NULL

            if not update_fields:
                logger.warning("Nenhum campo válido fornecido para atualização")
                return False

            # Adiciona o código do sensor como último parâmetro
            params.append(cod_sensor)

            sql = f"UPDATE T_SENSORES SET {', '.join(update_fields)} WHERE cod_sensor = :{param_index}"

            affected_rows = self.executar_sql(sql, params, 'update')
            success = affected_rows > 0

            if success:
                logger.info(f"Sensor {cod_sensor} atualizado com sucesso")
            else:
                logger.warning(f"Nenhum sensor encontrado com o código {cod_sensor}")

            return success

        except Exception as e:
            logger.error(f"Erro ao atualizar sensor: {e}")
            return False
        finally:
            self.disconnect()

    def delete_sensor(self, cod_sensor: int) -> bool:
        """
        Remove um sensor do banco de dados.

        Args:
            cod_sensor: Código do sensor a ser removido

        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Verifica se existem medições associadas a este sensor
            sql_check = "SELECT COUNT(*) FROM T_MEDICOES WHERE cod_sensor = :1"
            self.cursor.execute(sql_check, [cod_sensor])
            if self.cursor.fetchone()[0] > 0:
                logger.warning(f"Não é possível excluir o sensor {cod_sensor} pois existem medições associadas a ele.")
                return False

            # Remove o sensor
            sql = "DELETE FROM T_SENSORES WHERE cod_sensor = :1"
            affected_rows = self.executar_sql(sql, [cod_sensor], 'delete')
            success = affected_rows > 0

            if success:
                logger.info(f"Sensor {cod_sensor} removido com sucesso")
            else:
                logger.warning(f"Nenhum sensor encontrado com o código {cod_sensor}")

            return success

        except Exception as e:
            logger.error(f"Erro ao excluir sensor: {e}")
            return False
        finally:
            self.disconnect()

    # Operações CRUD para T_MEDICOES

    def create_medicao(self, data_hora_medicao: str, valor_medicao: float,
                       un_medicao: str, cod_sensor: int) -> int:
        """
        Insere uma nova medição no banco de dados.

        Args:
            data_hora_medicao: Data e hora da medição (formato YYYY-MM-DD HH24:MI:SS)
            valor_medicao: Valor da medição
            un_medicao: Unidade de medida (2 caracteres)
            cod_sensor: Código do sensor associado

        Returns:
            ID da medição inserida
        """
        self.connect()

        try:
            # Obtém o próximo código de medição
            self.cursor.execute("SELECT NVL(MAX(cod_medicao), 0) + 1 FROM T_MEDICOES")
            new_cod = self.cursor.fetchone()[0]

            # Insere a nova medição com tratamento adequado para a data
            if data_hora_medicao is not None:
                sql = """
                INSERT INTO T_MEDICOES (
                    cod_medicao, data_hora_medicao, valor_medicao, un_medicao, cod_sensor
                ) VALUES (
                    :1, TO_TIMESTAMP(:2, 'YYYY-MM-DD HH24:MI:SS'), :3, :4, :5
                )
                """
                params = [
                    new_cod, data_hora_medicao, valor_medicao, un_medicao, cod_sensor
                ]
            else:
                sql = """
                INSERT INTO T_MEDICOES (
                    cod_medicao, data_hora_medicao, valor_medicao, un_medicao, cod_sensor
                ) VALUES (
                    :1, NULL, :2, :3, :4
                )
                """
                params = [
                    new_cod, valor_medicao, un_medicao, cod_sensor
                ]

            self.executar_sql(sql, params, 'insert')
            logger.info(f"Nova medição inserida com ID: {new_cod}")

            return new_cod

        except Exception as e:
            logger.error(f"Erro ao criar medição: {e}")
            raise
        finally:
            self.disconnect()

    def read_medicao(self, cod_medicao: int = None, cod_sensor: int = None) -> List[Dict[str, Any]]:
        """
        Recupera dados de medições do banco de dados.

        Args:
            cod_medicao: Código da medição (opcional)
            cod_sensor: Código do sensor (opcional)

        Returns:
            Lista de dicionários com os dados das medições
        """
        self.connect()

        try:
            base_sql = """
            SELECT cod_medicao, TO_CHAR(data_hora_medicao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_medicao, 
                   valor_medicao, un_medicao, cod_sensor 
            FROM T_MEDICOES
            """

            if cod_medicao is not None and cod_sensor is not None:
                sql = f"{base_sql} WHERE cod_medicao = :1 AND cod_sensor = :2"
                params = [cod_medicao, cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            elif cod_medicao is not None:
                sql = f"{base_sql} WHERE cod_medicao = :1"
                params = [cod_medicao]
                result = self.executar_sql(sql, params, 'select_all')
            elif cod_sensor is not None:
                sql = f"{base_sql} WHERE cod_sensor = :1"
                params = [cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            else:
                sql = base_sql
                result = self.executar_sql(sql, [], 'select_all')

            return result

        except Exception as e:
            logger.error(f"Erro ao ler medição(ões): {e}")
            return []
        finally:
            self.disconnect()

    def update_medicao(self, cod_medicao: int, cod_sensor: int,
                       data_hora_medicao: str = None, valor_medicao: float = None,
                       un_medicao: str = None) -> bool:
        """
        Atualiza dados de uma medição existente.

        Args:
            cod_medicao: Código da medição a ser atualizada
            cod_sensor: Código do sensor associado
            data_hora_medicao: Nova data e hora da medição (opcional, formato YYYY-MM-DD HH24:MI:SS)
            valor_medicao: Novo valor da medição (opcional)
            un_medicao: Nova unidade de medida (opcional)

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Constrói a consulta SQL dinamicamente com base nos parâmetros fornecidos
            update_fields = []
            params = []
            param_index = 1

            if data_hora_medicao is not None:
                update_fields.append(f"data_hora_medicao = TO_TIMESTAMP(:{param_index}, 'YYYY-MM-DD HH24:MI:SS')")
                params.append(data_hora_medicao)
                param_index += 1
            elif data_hora_medicao == "":  # Caso especial para limpar a data
                update_fields.append("data_hora_medicao = NULL")
                # Não adiciona parâmetro para NULL

            if valor_medicao is not None:
                update_fields.append(f"valor_medicao = :{param_index}")
                params.append(valor_medicao)
                param_index += 1

            if un_medicao is not None:
                update_fields.append(f"un_medicao = :{param_index}")
                params.append(un_medicao)
                param_index += 1

            if not update_fields:
                logger.warning("Nenhum campo fornecido para atualização")
                return False

            # Adiciona os códigos como últimos parâmetros
            params.append(cod_medicao)
            params.append(cod_sensor)

            sql = f"UPDATE T_MEDICOES SET {', '.join(update_fields)} WHERE cod_medicao = :{param_index} AND cod_sensor = :{param_index + 1}"

            affected_rows = self.executar_sql(sql, params, 'update')
            success = affected_rows > 0

            if success:
                logger.info(f"Medição {cod_medicao} do sensor {cod_sensor} atualizada com sucesso")
            else:
                logger.warning(f"Nenhuma medição encontrada com o código {cod_medicao} e sensor {cod_sensor}")

            return success

        except Exception as e:
            logger.error(f"Erro ao atualizar medição: {e}")
            return False
        finally:
            self.disconnect()

    def delete_medicao(self, cod_medicao: int, cod_sensor: int) -> bool:
        """
        Remove uma medição do banco de dados.

        Args:
            cod_medicao: Código da medição a ser removida
            cod_sensor: Código do sensor associado

        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Verifica se existem sugestões associadas a esta medição
            sql_check = "SELECT COUNT(*) FROM T_SUGESTOES WHERE cod_medicao = :1 AND cod_sensor = :2"
            self.cursor.execute(sql_check, [cod_medicao, cod_sensor])
            if self.cursor.fetchone()[0] > 0:
                logger.warning(
                    f"Não é possível excluir a medição {cod_medicao} do sensor {cod_sensor} pois existem sugestões associadas a ela.")
                return False

            # Remove a medição
            sql = "DELETE FROM T_MEDICOES WHERE cod_medicao = :1 AND cod_sensor = :2"
            affected_rows = self.executar_sql(sql, [cod_medicao, cod_sensor], 'delete')
            success = affected_rows > 0

            if success:
                logger.info(f"Medição {cod_medicao} do sensor {cod_sensor} removida com sucesso")
            else:
                logger.warning(f"Nenhuma medição encontrada com o código {cod_medicao} e sensor {cod_sensor}")

            return success

        except Exception as e:
            logger.error(f"Erro ao excluir medição: {e}")
            return False
        finally:
            self.disconnect()

    # Operações CRUD para T_SUGESTOES

    def create_sugestao(self, cod_medicao: int, objetivo_sugestao: str,
                        data_hora_sugestao: str, valor_sugestao: float,
                        un_sugestao: str, cod_sensor: int) -> int:
        """
        Insere uma nova sugestão no banco de dados.

        Args:
            cod_medicao: Código da medição associada
            objetivo_sugestao: Objetivo da sugestão
            data_hora_sugestao: Data e hora da sugestão (formato YYYY-MM-DD HH24:MI:SS)
            valor_sugestao: Valor da sugestão
            un_sugestao: Unidade de medida (2 caracteres)
            cod_sensor: Código do sensor associado

        Returns:
            ID da sugestão inserida
        """
        self.connect()

        try:
            # Obtém o próximo código de sugestão
            self.cursor.execute("SELECT NVL(MAX(cod_sugestao), 0) + 1 FROM T_SUGESTOES")
            new_cod = self.cursor.fetchone()[0]

            # Insere a nova sugestão com tratamento adequado para a data
            if data_hora_sugestao is not None:
                sql = """
                INSERT INTO T_SUGESTOES (
                    cod_medicao, cod_sugestao, objetivo_sugestao, data_hora_sugestao, 
                    valor_sugestao, un_sugestao, cod_sensor
                ) VALUES (
                    :1, :2, :3, TO_TIMESTAMP(:4, 'YYYY-MM-DD HH24:MI:SS'), :5, :6, :7
                )
                """
                params = [
                    cod_medicao, new_cod, objetivo_sugestao, data_hora_sugestao,
                    valor_sugestao, un_sugestao, cod_sensor
                ]
            else:
                sql = """
                INSERT INTO T_SUGESTOES (
                    cod_medicao, cod_sugestao, objetivo_sugestao, data_hora_sugestao, 
                    valor_sugestao, un_sugestao, cod_sensor
                ) VALUES (
                    :1, :2, :3, NULL, :4, :5, :6
                )
                """
                params = [
                    cod_medicao, new_cod, objetivo_sugestao,
                    valor_sugestao, un_sugestao, cod_sensor
                ]

            self.executar_sql(sql, params, 'insert')
            logger.info(f"Nova sugestão inserida com ID: {new_cod}")

            return new_cod

        except Exception as e:
            logger.error(f"Erro ao criar sugestão: {e}")
            raise
        finally:
            self.disconnect()

    def read_sugestao(self, cod_sugestao: int = None, cod_medicao: int = None,
                      cod_sensor: int = None) -> List[Dict[str, Any]]:
        """
        Recupera dados de sugestões do banco de dados.

        Args:
            cod_sugestao: Código da sugestão (opcional)
            cod_medicao: Código da medição (opcional)
            cod_sensor: Código do sensor (opcional)

        Returns:
            Lista de dicionários com os dados das sugestões
        """
        self.connect()

        try:
            base_sql = """
            SELECT cod_medicao, cod_sugestao, objetivo_sugestao, 
                   TO_CHAR(data_hora_sugestao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_sugestao, 
                   valor_sugestao, un_sugestao, cod_sensor 
            FROM T_SUGESTOES
            """

            if cod_sugestao is not None and cod_medicao is not None and cod_sensor is not None:
                sql = f"{base_sql} WHERE cod_sugestao = :1 AND cod_medicao = :2 AND cod_sensor = :3"
                params = [cod_sugestao, cod_medicao, cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            elif cod_medicao is not None and cod_sensor is not None:
                sql = f"{base_sql} WHERE cod_medicao = :1 AND cod_sensor = :2"
                params = [cod_medicao, cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            elif cod_sugestao is not None:
                sql = f"{base_sql} WHERE cod_sugestao = :1"
                params = [cod_sugestao]
                result = self.executar_sql(sql, params, 'select_all')
            else:
                sql = base_sql
                result = self.executar_sql(sql, [], 'select_all')

            return result

        except Exception as e:
            logger.error(f"Erro ao ler sugestão(ões): {e}")
            return []
        finally:
            self.disconnect()

    def update_sugestao(self, cod_sugestao: int, cod_medicao: int, cod_sensor: int,
                        objetivo_sugestao: str = None, data_hora_sugestao: str = None,
                        valor_sugestao: float = None, un_sugestao: str = None) -> bool:
        """
        Atualiza dados de uma sugestão existente.

        Args:
            cod_sugestao: Código da sugestão a ser atualizada
            cod_medicao: Código da medição associada
            cod_sensor: Código do sensor associado
            objetivo_sugestao: Novo objetivo da sugestão (opcional)
            data_hora_sugestao: Nova data e hora da sugestão (opcional, formato YYYY-MM-DD HH24:MI:SS)
            valor_sugestao: Novo valor da sugestão (opcional)
            un_sugestao: Nova unidade de medida (opcional)

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Constrói a consulta SQL dinamicamente com base nos parâmetros fornecidos
            update_fields = []
            params = []
            param_index = 1

            if objetivo_sugestao is not None:
                update_fields.append(f"objetivo_sugestao = :{param_index}")
                params.append(objetivo_sugestao)
                param_index += 1

            if data_hora_sugestao is not None:
                update_fields.append(f"data_hora_sugestao = TO_TIMESTAMP(:{param_index}, 'YYYY-MM-DD HH24:MI:SS')")
                params.append(data_hora_sugestao)
                param_index += 1
            elif data_hora_sugestao == "":  # Caso especial para limpar a data
                update_fields.append("data_hora_sugestao = NULL")
                # Não adiciona parâmetro para NULL

            if valor_sugestao is not None:
                update_fields.append(f"valor_sugestao = :{param_index}")
                params.append(valor_sugestao)
                param_index += 1

            if un_sugestao is not None:
                update_fields.append(f"un_sugestao = :{param_index}")
                params.append(un_sugestao)
                param_index += 1

            if not update_fields:
                logger.warning("Nenhum campo fornecido para atualização")
                return False

            # Adiciona os códigos como últimos parâmetros
            params.append(cod_sugestao)
            params.append(cod_medicao)
            params.append(cod_sensor)

            sql = f"""UPDATE T_SUGESTOES 
                   SET {', '.join(update_fields)} 
                   WHERE cod_sugestao = :{param_index} AND cod_medicao = :{param_index + 1} AND cod_sensor = :{param_index + 2}"""

            affected_rows = self.executar_sql(sql, params, 'update')
            success = affected_rows > 0

            if success:
                logger.info(f"Sugestão {cod_sugestao} atualizada com sucesso")
            else:
                logger.warning(f"Nenhuma sugestão encontrada com os códigos fornecidos")

            return success

        except Exception as e:
            logger.error(f"Erro ao atualizar sugestão: {e}")
            return False
        finally:
            self.disconnect()

    def delete_sugestao(self, cod_sugestao: int, cod_medicao: int, cod_sensor: int) -> bool:
        """
        Remove uma sugestão do banco de dados.

        Args:
            cod_sugestao: Código da sugestão a ser removida
            cod_medicao: Código da medição associada
            cod_sensor: Código do sensor associado

        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Verifica se existem aplicações associadas a esta sugestão
            sql_check = """SELECT COUNT(*) FROM T_APLICACOES 
                         WHERE cod_sugestao = :1 AND cod_medicao = :2 AND cod_sensor = :3"""
            self.cursor.execute(sql_check, [cod_sugestao, cod_medicao, cod_sensor])
            if self.cursor.fetchone()[0] > 0:
                logger.warning(
                    f"Não é possível excluir a sugestão {cod_sugestao} pois existem aplicações associadas a ela.")
                return False

            # Remove a sugestão
            sql = """DELETE FROM T_SUGESTOES 
                   WHERE cod_sugestao = :1 AND cod_medicao = :2 AND cod_sensor = :3"""
            affected_rows = self.executar_sql(sql, [cod_sugestao, cod_medicao, cod_sensor], 'delete')
            success = affected_rows > 0

            if success:
                logger.info(f"Sugestão {cod_sugestao} removida com sucesso")
            else:
                logger.warning(f"Nenhuma sugestão encontrada com os códigos fornecidos")

            return success

        except Exception as e:
            logger.error(f"Erro ao excluir sugestão: {e}")
            return False
        finally:
            self.disconnect()

    # Operações CRUD para T_APLICACOES

    def create_aplicacao(self, cod_medicao: int, cod_sugestao: int, cod_sensor: int,
                         cod_cultura: int, nm_produto_utilizado: str, valor_aplicacao: float,
                         un_aplicacao: str, data_hora_aplicacao: str,
                         nm_resp_aplicacao: str, documento_resp: str) -> int:
        """
        Insere uma nova aplicação no banco de dados.

        Args:
            cod_medicao: Código da medição associada
            cod_sugestao: Código da sugestão associada
            cod_sensor: Código do sensor associado
            cod_cultura: Código da cultura associada
            nm_produto_utilizado: Nome do produto utilizado
            valor_aplicacao: Valor da aplicação
            un_aplicacao: Unidade de medida (2 caracteres)
            data_hora_aplicacao: Data e hora da aplicação (formato YYYY-MM-DD HH24:MI:SS)
            nm_resp_aplicacao: Nome do responsável pela aplicação
            documento_resp: Documento do responsável

        Returns:
            ID da aplicação inserida
        """
        self.connect()

        try:
            # Obtém o próximo código de aplicação
            self.cursor.execute("SELECT NVL(MAX(cod_aplicacao), 0) + 1 FROM T_APLICACOES")
            new_cod = self.cursor.fetchone()[0]

            # Insere a nova aplicação com tratamento adequado para a data
            if data_hora_aplicacao is not None:
                sql = """
                INSERT INTO T_APLICACOES (
                    cod_medicao, cod_sugestao, cod_sensor, cod_cultura, cod_aplicacao,
                    nm_produto_utilizado, valor_aplicacao, un_aplicacao, data_hora_aplicacao,
                    nm_resp_aplicacao, documento_resp
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, TO_TIMESTAMP(:9, 'YYYY-MM-DD HH24:MI:SS'), :10, :11
                )
                """
                params = [
                    cod_medicao, cod_sugestao, cod_sensor, cod_cultura, new_cod,
                    nm_produto_utilizado, valor_aplicacao, un_aplicacao, data_hora_aplicacao,
                    nm_resp_aplicacao, documento_resp
                ]
            else:
                sql = """
                INSERT INTO T_APLICACOES (
                    cod_medicao, cod_sugestao, cod_sensor, cod_cultura, cod_aplicacao,
                    nm_produto_utilizado, valor_aplicacao, un_aplicacao, data_hora_aplicacao,
                    nm_resp_aplicacao, documento_resp
                ) VALUES (
                    :1, :2, :3, :4, :5, :6, :7, :8, NULL, :9, :10
                )
                """
                params = [
                    cod_medicao, cod_sugestao, cod_sensor, cod_cultura, new_cod,
                    nm_produto_utilizado, valor_aplicacao, un_aplicacao,
                    nm_resp_aplicacao, documento_resp
                ]

            self.executar_sql(sql, params, 'insert')
            logger.info(f"Nova aplicação inserida com ID: {new_cod}")

            return new_cod

        except Exception as e:
            logger.error(f"Erro ao criar aplicação: {e}")
            raise
        finally:
            self.disconnect()

    def read_aplicacao(self, cod_aplicacao: int = None, cod_medicao: int = None,
                       cod_sugestao: int = None, cod_sensor: int = None) -> List[Dict[str, Any]]:
        """
        Recupera dados de aplicações do banco de dados.

        Args:
            cod_aplicacao: Código da aplicação (opcional)
            cod_medicao: Código da medição (opcional)
            cod_sugestao: Código da sugestão (opcional)
            cod_sensor: Código do sensor (opcional)

        Returns:
            Lista de dicionários com os dados das aplicações
        """
        self.connect()

        try:
            base_sql = """
            SELECT cod_medicao, cod_sugestao, cod_sensor, cod_cultura, cod_aplicacao,
                   nm_produto_utilizado, valor_aplicacao, un_aplicacao, 
                   TO_CHAR(data_hora_aplicacao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_aplicacao,
                   nm_resp_aplicacao, documento_resp
            FROM T_APLICACOES
            """

            if cod_aplicacao is not None:
                sql = f"{base_sql} WHERE cod_aplicacao = :1"
                params = [cod_aplicacao]
                result = self.executar_sql(sql, params, 'select_all')
            elif cod_medicao is not None and cod_sugestao is not None and cod_sensor is not None:
                sql = f"{base_sql} WHERE cod_medicao = :1 AND cod_sugestao = :2 AND cod_sensor = :3"
                params = [cod_medicao, cod_sugestao, cod_sensor]
                result = self.executar_sql(sql, params, 'select_all')
            else:
                sql = base_sql
                result = self.executar_sql(sql, [], 'select_all')

            return result

        except Exception as e:
            logger.error(f"Erro ao ler aplicação(ões): {e}")
            return []
        finally:
            self.disconnect()

    def update_aplicacao(self, cod_aplicacao: int, cod_medicao: int, cod_sugestao: int,
                         cod_sensor: int, **kwargs) -> bool:
        """
        Atualiza dados de uma aplicação existente.

        Args:
            cod_aplicacao: Código da aplicação a ser atualizada
            cod_medicao: Código da medição associada
            cod_sugestao: Código da sugestão associada
            cod_sensor: Código do sensor associado
            **kwargs: Pares chave-valor com os campos a serem atualizados

        Returns:
            True se a atualização foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            # Campos válidos para atualização
            valid_fields = [
                'cod_cultura', 'nm_produto_utilizado', 'valor_aplicacao',
                'un_aplicacao', 'data_hora_aplicacao', 'nm_resp_aplicacao',
                'documento_resp'
            ]

            # Filtra apenas os campos válidos
            update_fields = []
            params = []
            param_index = 1

            for field, value in kwargs.items():
                if field in valid_fields and value is not None:
                    # Tratamento especial para campos de data
                    if field == 'data_hora_aplicacao':
                        update_fields.append(f"{field} = TO_TIMESTAMP(:{param_index}, 'YYYY-MM-DD HH24:MI:SS')")
                    else:
                        update_fields.append(f"{field} = :{param_index}")
                    params.append(value)
                    param_index += 1
                elif field in valid_fields and value == "":  # Caso especial para limpar campos
                    if field == 'data_hora_aplicacao':
                        update_fields.append(f"{field} = NULL")
                        # Não adiciona parâmetro para NULL

            if not update_fields:
                logger.warning("Nenhum campo válido fornecido para atualização")
                return False

            # Adiciona os códigos como últimos parâmetros
            params.append(cod_aplicacao)
            params.append(cod_medicao)
            params.append(cod_sugestao)
            params.append(cod_sensor)

            sql = f"""UPDATE T_APLICACOES 
                   SET {', '.join(update_fields)} 
                   WHERE cod_aplicacao = :{param_index} AND cod_medicao = :{param_index + 1} 
                   AND cod_sugestao = :{param_index + 2} AND cod_sensor = :{param_index + 3}"""

            affected_rows = self.executar_sql(sql, params, 'update')
            success = affected_rows > 0

            if success:
                logger.info(f"Aplicação {cod_aplicacao} atualizada com sucesso")
            else:
                logger.warning(f"Nenhuma aplicação encontrada com os códigos fornecidos")

            return success

        except Exception as e:
            logger.error(f"Erro ao atualizar aplicação: {e}")
            return False
        finally:
            self.disconnect()

    def delete_aplicacao(self, cod_aplicacao: int, cod_medicao: int = None,
                         cod_sugestao: int = None, cod_sensor: int = None) -> bool:
        """
        Remove uma aplicação do banco de dados.

        Args:
            cod_aplicacao: Código da aplicação a ser removida
            cod_medicao: Código da medição associada (opcional)
            cod_sugestao: Código da sugestão associada (opcional)
            cod_sensor: Código do sensor associado (opcional)

        Returns:
            True se a remoção foi bem-sucedida, False caso contrário
        """
        self.connect()

        try:
            if cod_medicao is not None and cod_sugestao is not None and cod_sensor is not None:
                sql = """DELETE FROM T_APLICACOES 
                       WHERE cod_aplicacao = :1 AND cod_medicao = :2 AND cod_sugestao = :3 AND cod_sensor = :4"""
                params = [cod_aplicacao, cod_medicao, cod_sugestao, cod_sensor]
            else:
                sql = "DELETE FROM T_APLICACOES WHERE cod_aplicacao = :1"
                params = [cod_aplicacao]

            affected_rows = self.executar_sql(sql, params, 'delete')
            success = affected_rows > 0

            if success:
                logger.info(f"Aplicação {cod_aplicacao} removida com sucesso")
            else:
                logger.warning(f"Nenhuma aplicação encontrada com os códigos fornecidos")

            return success

        except Exception as e:
            logger.error(f"Erro ao excluir aplicação: {e}")
            return False
        finally:
            self.disconnect()

    # Consultas analíticas

    def get_medicoes_by_cultura(self, cod_cultura: int) -> List[Dict[str, Any]]:
        """
        Recupera todas as medições associadas a uma cultura específica.

        Args:
            cod_cultura: Código da cultura

        Returns:
            Lista de dicionários com os dados das medições
        """
        self.connect()

        try:
            sql = """
            SELECT m.cod_medicao, TO_CHAR(m.data_hora_medicao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_medicao, 
                   m.valor_medicao, m.un_medicao, m.cod_sensor, 
                   s.nm_sensor, s.tipo_sensor, c.desc_cultura
            FROM T_MEDICOES m
            JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
            JOIN T_CULTURAS c ON s.cod_cultura = c.cod_cultura
            WHERE c.cod_cultura = :1
            ORDER BY m.data_hora_medicao DESC
            """

            result = self.executar_sql(sql, [cod_cultura], 'select_all')
            return result

        except Exception as e:
            logger.error(f"Erro ao recuperar medições por cultura: {e}")
            return []
        finally:
            self.disconnect()

    def get_aplicacoes_by_cultura(self, cod_cultura: int) -> List[Dict[str, Any]]:
        """
        Recupera todas as aplicações associadas a uma cultura específica.

        Args:
            cod_cultura: Código da cultura

        Returns:
            Lista de dicionários com os dados das aplicações
        """
        self.connect()

        try:
            sql = """
            SELECT a.cod_aplicacao, a.nm_produto_utilizado, a.valor_aplicacao, a.un_aplicacao,
                   TO_CHAR(a.data_hora_aplicacao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_aplicacao,
                   a.nm_resp_aplicacao, a.documento_resp, c.desc_cultura
            FROM T_APLICACOES a
            JOIN T_CULTURAS c ON a.cod_cultura = c.cod_cultura
            WHERE c.cod_cultura = :1
            ORDER BY a.data_hora_aplicacao DESC
            """

            result = self.executar_sql(sql, [cod_cultura], 'select_all')
            return result

        except Exception as e:
            logger.error(f"Erro ao recuperar aplicações por cultura: {e}")
            return []
        finally:
            self.disconnect()

    def get_sugestoes_by_sensor(self, cod_sensor: int) -> List[Dict[str, Any]]:
        """
        Recupera todas as sugestões associadas a um sensor específico.

        Args:
            cod_sensor: Código do sensor

        Returns:
            Lista de dicionários com os dados das sugestões
        """
        self.connect()

        try:
            sql = """
            SELECT s.cod_sugestao, s.objetivo_sugestao, 
                   TO_CHAR(s.data_hora_sugestao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_sugestao,
                   s.valor_sugestao, s.un_sugestao, s.cod_sensor, s.cod_medicao,
                   m.valor_medicao, TO_CHAR(m.data_hora_medicao, 'YYYY-MM-DD HH24:MI:SS') as data_hora_medicao
            FROM T_SUGESTOES s
            JOIN T_MEDICOES m ON s.cod_medicao = m.cod_medicao AND s.cod_sensor = m.cod_sensor
            WHERE s.cod_sensor = :1
            ORDER BY s.data_hora_sugestao DESC
            """

            result = self.executar_sql(sql, [cod_sensor], 'select_all')
            return result

        except Exception as e:
            logger.error(f"Erro ao recuperar sugestões por sensor: {e}")
            return []
        finally:
            self.disconnect()


def main():
    """Função principal para demonstração do funcionamento do sistema."""
    try:
        print("\n=== Sistema de Gerenciamento de Dados Agrícolas ===")
        print("Conectando ao banco de dados Oracle...")

        db = AgricolaDatabaseManager()

        # Demonstração de operações CRUD para todas as tabelas
        print("\n=== Demonstração de operações CRUD para todas as tabelas ===")

        # ===== CRUD para T_CULTURAS =====
        print("\n===== CRUD para T_CULTURAS =====")

        # 1. Create - Inserir uma nova cultura
        print("\n1. Create: Inserindo uma nova cultura")
        try:
            new_cultura_id = db.create_cultura("Trigo", 1200.50)
            print(f"  Nova cultura inserida com ID: {new_cultura_id}")

            # 2. Read - Recuperar dados de culturas
            print("\n2. Read: Recuperando dados de culturas")
            culturas = db.read_cultura()
            for cultura in culturas:
                print(
                    f"  ID: {cultura['COD_CULTURA']}, Descrição: {cultura['DESC_CULTURA']}, Tamanho: {cultura['TAMANHO_CULTURA']}")

            # 3. Update - Atualizar uma cultura
            print(f"\n3. Update: Atualizando a cultura {new_cultura_id}")
            success = db.update_cultura(new_cultura_id, tamanho_cultura=1500.75)
            print(f"  Atualização {'bem-sucedida' if success else 'falhou'}")

            # Verificar a atualização
            cultura_atualizada = db.read_cultura(new_cultura_id)[0]
            print(f"  Valor atualizado: Tamanho = {cultura_atualizada['TAMANHO_CULTURA']}")

            # Manter a cultura para uso nas outras tabelas
            cultura_id = new_cultura_id

            # ===== CRUD para T_SENSORES =====
            print("\n===== CRUD para T_SENSORES =====")

            # 1. Create - Inserir um novo sensor
            print("\n1. Create: Inserindo um novo sensor")
            new_sensor_id = db.create_sensor(
                nm_sensor="Sensor de Umidade",
                tipo_sensor="UM",
                objetivo_sensor="Medir umidade do solo",
                fab_sensor="SensorTech",
                modelo_sensor="ST-100",
                data_instalacao="2025-05-01",
                latitude_instalacao=-23.5505,
                longitude_instalacao=-46.6333,
                valor_minimo=1.0,
                valor_maximo=100.0,
                unidade="PC",
                cod_cultura=cultura_id
            )
            print(f"  Novo sensor inserido com ID: {new_sensor_id}")

            # 2. Read - Recuperar dados de sensores
            print("\n2. Read: Recuperando dados de sensores")
            sensores = db.read_sensor()
            for sensor in sensores:
                print(f"  ID: {sensor['COD_SENSOR']}, Nome: {sensor['NM_SENSOR']}, Tipo: {sensor['TIPO_SENSOR']}")

            # 3. Update - Atualizar um sensor
            print(f"\n3. Update: Atualizando o sensor {new_sensor_id}")
            success = db.update_sensor(new_sensor_id, valor_minimo=10.0, valor_maximo=90.0)
            print(f"  Atualização {'bem-sucedida' if success else 'falhou'}")

            # Verificar a atualização
            sensor_atualizado = db.read_sensor(new_sensor_id)[0]
            print(
                f"  Valores atualizados: Min = {sensor_atualizado['VALOR_MINIMO']}, Max = {sensor_atualizado['VALOR_MAXIMO']}")

            # Manter o sensor para uso nas outras tabelas
            sensor_id = new_sensor_id

            # ===== CRUD para T_MEDICOES =====
            print("\n===== CRUD para T_MEDICOES =====")

            # 1. Create - Inserir uma nova medição
            print("\n1. Create: Inserindo uma nova medição")
            new_medicao_id = db.create_medicao(
                data_hora_medicao="2025-05-19 10:30:00",
                valor_medicao=75.5,
                un_medicao="PC",
                cod_sensor=sensor_id
            )
            print(f"  Nova medição inserida com ID: {new_medicao_id}")

            # 2. Read - Recuperar dados de medições
            print("\n2. Read: Recuperando dados de medições")
            medicoes = db.read_medicao(cod_sensor=sensor_id)
            for medicao in medicoes:
                print(
                    f"  ID: {medicao['COD_MEDICAO']}, Valor: {medicao['VALOR_MEDICAO']} {medicao['UN_MEDICAO']}, Data: {medicao['DATA_HORA_MEDICAO']}")

            # 3. Update - Atualizar uma medição
            print(f"\n3. Update: Atualizando a medição {new_medicao_id}")
            success = db.update_medicao(new_medicao_id, sensor_id, valor_medicao=80.0)
            print(f"  Atualização {'bem-sucedida' if success else 'falhou'}")

            # Verificar a atualização
            medicao_atualizada = db.read_medicao(new_medicao_id)[0]
            print(f"  Valor atualizado: {medicao_atualizada['VALOR_MEDICAO']} {medicao_atualizada['UN_MEDICAO']}")

            # Manter a medição para uso nas outras tabelas
            medicao_id = new_medicao_id

            # ===== CRUD para T_SUGESTOES =====
            print("\n===== CRUD para T_SUGESTOES =====")

            # 1. Create - Inserir uma nova sugestão
            print("\n1. Create: Inserindo uma nova sugestão")
            new_sugestao_id = db.create_sugestao(
                cod_medicao=medicao_id,
                objetivo_sugestao="Irrigação recomendada",
                data_hora_sugestao="2025-05-19 11:00:00",
                valor_sugestao=20.0,
                un_sugestao="MM",
                cod_sensor=sensor_id
            )
            print(f"  Nova sugestão inserida com ID: {new_sugestao_id}")

            # 2. Read - Recuperar dados de sugestões
            print("\n2. Read: Recuperando dados de sugestões")
            sugestoes = db.read_sugestao(cod_sensor=sensor_id)
            for sugestao in sugestoes:
                print(
                    f"  ID: {sugestao['COD_SUGESTAO']}, Objetivo: {sugestao['OBJETIVO_SUGESTAO']}, Valor: {sugestao['VALOR_SUGESTAO']} {sugestao['UN_SUGESTAO']}")

            # 3. Update - Atualizar uma sugestão
            print(f"\n3. Update: Atualizando a sugestão {new_sugestao_id}")
            success = db.update_sugestao(new_sugestao_id, medicao_id, sensor_id, valor_sugestao=25.0)
            print(f"  Atualização {'bem-sucedida' if success else 'falhou'}")

            # Verificar a atualização
            sugestao_atualizada = db.read_sugestao(new_sugestao_id)[0]
            print(f"  Valor atualizado: {sugestao_atualizada['VALOR_SUGESTAO']} {sugestao_atualizada['UN_SUGESTAO']}")

            # Manter a sugestão para uso nas outras tabelas
            sugestao_id = new_sugestao_id

            # ===== CRUD para T_APLICACOES =====
            print("\n===== CRUD para T_APLICACOES =====")

            # 1. Create - Inserir uma nova aplicação
            print("\n1. Create: Inserindo uma nova aplicação")
            new_aplicacao_id = db.create_aplicacao(
                cod_medicao=medicao_id,
                cod_sugestao=sugestao_id,
                cod_sensor=sensor_id,
                cod_cultura=cultura_id,
                nm_produto_utilizado="Irrigador Automático",
                valor_aplicacao=22.5,
                un_aplicacao="MM",
                data_hora_aplicacao="2025-05-19 14:00:00",
                nm_resp_aplicacao="João Silva",
                documento_resp="12345678900"
            )
            print(f"  Nova aplicação inserida com ID: {new_aplicacao_id}")

            # 2. Read - Recuperar dados de aplicações
            print("\n2. Read: Recuperando dados de aplicações")
            aplicacoes = db.read_aplicacao(cod_aplicacao=new_aplicacao_id)
            for aplicacao in aplicacoes:
                print(
                    f"  ID: {aplicacao['COD_APLICACAO']}, Produto: {aplicacao['NM_PRODUTO_UTILIZADO']}, Valor: {aplicacao['VALOR_APLICACAO']} {aplicacao['UN_APLICACAO']}")

            # 3. Update - Atualizar uma aplicação
            print(f"\n3. Update: Atualizando a aplicação {new_aplicacao_id}")
            success = db.update_aplicacao(
                new_aplicacao_id, medicao_id, sugestao_id, sensor_id,
                valor_aplicacao=24.0,
                nm_resp_aplicacao="João Carlos Silva"
            )
            print(f"  Atualização {'bem-sucedida' if success else 'falhou'}")

            # Verificar a atualização
            aplicacao_atualizada = db.read_aplicacao(new_aplicacao_id)[0]
            print(
                f"  Valores atualizados: Valor = {aplicacao_atualizada['VALOR_APLICACAO']}, Responsável = {aplicacao_atualizada['NM_RESP_APLICACAO']}")

            # ===== Consultas analíticas =====
            print("\n===== Consultas analíticas =====")

            # Medições por cultura
            print("\n1. Medições por cultura:")
            medicoes_cultura = db.get_medicoes_by_cultura(cultura_id)
            print(f"  Total de medições para a cultura {cultura_id}: {len(medicoes_cultura)}")

            # Aplicações por cultura
            print("\n2. Aplicações por cultura:")
            aplicacoes_cultura = db.get_aplicacoes_by_cultura(cultura_id)
            print(f"  Total de aplicações para a cultura {cultura_id}: {len(aplicacoes_cultura)}")

            # Sugestões por sensor
            print("\n3. Sugestões por sensor:")
            sugestoes_sensor = db.get_sugestoes_by_sensor(sensor_id)
            print(f"  Total de sugestões para o sensor {sensor_id}: {len(sugestoes_sensor)}")

            # ===== Limpeza (opcional) =====
            print("\n===== Limpeza dos dados de teste =====")

            # 4. Delete - Remover em ordem para respeitar as chaves estrangeiras
            print("\n4. Delete: Removendo dados de teste")

            # Remover aplicação
            print("  Removendo aplicação...")
            success = db.delete_aplicacao(new_aplicacao_id, medicao_id, sugestao_id, sensor_id)
            print(f"  Remoção da aplicação {'bem-sucedida' if success else 'falhou'}")

            # Remover sugestão
            print("  Removendo sugestão...")
            success = db.delete_sugestao(sugestao_id, medicao_id, sensor_id)
            print(f"  Remoção da sugestão {'bem-sucedida' if success else 'falhou'}")

            # Remover medição
            print("  Removendo medição...")
            success = db.delete_medicao(medicao_id, sensor_id)
            print(f"  Remoção da medição {'bem-sucedida' if success else 'falhou'}")

            # Remover sensor
            print("  Removendo sensor...")
            success = db.delete_sensor(sensor_id)
            print(f"  Remoção do sensor {'bem-sucedida' if success else 'falhou'}")

            # Remover cultura
            print("  Removendo cultura...")
            success = db.delete_cultura(cultura_id)
            print(f"  Remoção da cultura {'bem-sucedida' if success else 'falhou'}")

        except Exception as e:
            print(f"Erro durante a demonstração: {e}")

        print("\nDemonstração completa concluída.")

    except Exception as e:
        print(f"Erro ao inicializar o sistema: {e}")
        logger.exception("Erro fatal durante a execução do programa")

if __name__ == "__main__":
    main()
