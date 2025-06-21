"""
Sistema de Gerenciamento de Dados Agricolas - FarmTech Solutions
FASE 4 - Integracao ESP32 + Oracle Database (Estrutura Fase 3)

Este sistema conecta ao banco Oracle existente da Fase 3 e insere
dados dos sensores ESP32 na estrutura original (T_MEDICOES, T_SENSORES).

Autor: FarmTech Solutions
Data: Junho 2025
"""

import oracledb
import csv
import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Configuracao de logging sem emojis
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('farmtech_oracle.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class FarmTechOracleManager:
    """
    Classe para gerenciar dados dos sensores ESP32 no banco Oracle da Fase 3.
    Usa a estrutura original: T_CULTURAS, T_SENSORES, T_MEDICOES.
    """

    def __init__(self):
        """Inicializa o gerenciador com configuracoes do Oracle da Fase 3."""
        # Configuracoes de conexao Oracle (da Fase 3)
        self.host = "localhost"
        self.port = 1522
        self.service_name = "ORCLPDB"
        self.user = "RCOSTA"
        self.password = "Rcosta@1980"
        
        self.conn = None
        self.cursor = None
        
        # IDs dos sensores ESP32 (serao criados automaticamente)
        self.sensores_esp32 = {
            'fosforo': None,
            'potassio': None,
            'ph': None,
            'umidade': None,
            'bomba': None
        }

    def connect(self):
        """Estabelece conexao com o banco Oracle existente."""
        try:
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            self.conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)
            self.cursor = self.conn.cursor()
            logger.info("Conectado ao banco Oracle da Fase 3")
            return True
        except oracledb.DatabaseError as e:
            logger.error(f"Erro de conexao Oracle: {e}")
            return False

    def disconnect(self):
        """Fecha a conexao com o banco."""
        if self.conn:
            if self.cursor:
                self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Conexao Oracle encerrada")

    def verificar_tabelas_existentes(self):
        """Verifica se as tabelas da Fase 3 existem no banco."""
        if not self.connect():
            return False
            
        try:
            tabelas_esperadas = ['T_CULTURAS', 'T_SENSORES', 'T_MEDICOES', 'T_SUGESTOES', 'T_APLICACOES']
            tabelas_encontradas = []
            
            for tabela in tabelas_esperadas:
                self.cursor.execute(f"SELECT COUNT(*) FROM USER_TABLES WHERE TABLE_NAME = '{tabela}'")
                if self.cursor.fetchone()[0] > 0:
                    tabelas_encontradas.append(tabela)
            
            print(f"\nTABELAS ENCONTRADAS NO BANCO ORACLE:")
            for tabela in tabelas_encontradas:
                self.cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                count = self.cursor.fetchone()[0]
                print(f"   {tabela}: {count} registros")
            
            if len(tabelas_encontradas) == len(tabelas_esperadas):
                print("Todas as tabelas da Fase 3 estao disponiveis!")
                return True
            else:
                print("Algumas tabelas da Fase 3 nao foram encontradas")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar tabelas: {e}")
            return False
        finally:
            self.disconnect()

    def criar_sensores_esp32(self):
        """Cria sensores virtuais para o ESP32 na tabela T_SENSORES."""
        if not self.connect():
            return False
            
        try:
            # Verifica se ja existe uma cultura para associar os sensores
            self.cursor.execute("SELECT cod_cultura FROM T_CULTURAS WHERE ROWNUM = 1")
            cultura_row = self.cursor.fetchone()
            if not cultura_row:
                # Cria uma cultura padrao para ESP32
                self.cursor.execute("SELECT NVL(MAX(cod_cultura), 0) + 1 FROM T_CULTURAS")
                novo_cod_cultura = self.cursor.fetchone()[0]
                
                sql_cultura = """
                INSERT INTO T_CULTURAS (cod_cultura, desc_cultura, tamanho_cultura)
                VALUES (:1, :2, :3)
                """
                self.cursor.execute(sql_cultura, [novo_cod_cultura, "Cultura ESP32 - FarmTech", 1.0])
                cod_cultura = novo_cod_cultura
                print(f"Cultura ESP32 criada com codigo: {cod_cultura}")
            else:
                cod_cultura = cultura_row[0]
                print(f"Usando cultura existente: {cod_cultura}")
            
            # Definicao dos sensores ESP32 (valores minimos > 0 devido a constraint)
            sensores_config = [
                ('fosforo', 'Sensor Fosforo ESP32', 'FO', 'Deteccao de fosforo', 'FarmTech', 'ESP32-FO', 0.01, 1, 'UN'),
                ('potassio', 'Sensor Potassio ESP32', 'PO', 'Deteccao de potassio', 'FarmTech', 'ESP32-PO', 0.01, 1, 'UN'),
                ('ph', 'Sensor pH ESP32', 'PH', 'Medicao de pH do solo', 'FarmTech', 'ESP32-PH', 0.01, 14, 'PH'),
                ('umidade', 'Sensor Umidade ESP32', 'UM', 'Medicao de umidade do solo', 'FarmTech', 'ESP32-UM', 0.01, 100, '%'),
                ('bomba', 'Sensor Bomba ESP32', 'BO', 'Status da bomba de irrigacao', 'FarmTech', 'ESP32-BO', 0.01, 1, 'UN')
            ]
            
            for sensor_key, nome, tipo, objetivo, fab, modelo, val_min, val_max, unidade in sensores_config:
                # Verifica se o sensor ja existe
                self.cursor.execute("SELECT cod_sensor FROM T_SENSORES WHERE nm_sensor = :1", [nome])
                sensor_existente = self.cursor.fetchone()
                
                if sensor_existente:
                    self.sensores_esp32[sensor_key] = sensor_existente[0]
                    print(f"Sensor {nome} ja existe com codigo: {sensor_existente[0]}")
                else:
                    # Obtem proximo codigo de sensor
                    self.cursor.execute("SELECT NVL(MAX(cod_sensor), 0) + 1 FROM T_SENSORES")
                    novo_cod_sensor = self.cursor.fetchone()[0]
                    
                    # Insere novo sensor
                    sql_sensor = """
                    INSERT INTO T_SENSORES (
                        cod_sensor, nm_sensor, tipo_sensor, objetivo_sensor, fab_sensor,
                        modelo_sensor, data_instalacao, latitude_instalacao, longitude_instalacao,
                        valor_minimo, valor_maximo, unidade, cod_cultura
                    ) VALUES (
                        :1, :2, :3, :4, :5, :6, SYSDATE, :7, :8, :9, :10, :11, :12
                    )
                    """
                    
                    # Coordenadas unicas para cada sensor
                    lat = -23.550520 + (novo_cod_sensor * 0.001)
                    lng = -46.633308 + (novo_cod_sensor * 0.001)
                    
                    params = [novo_cod_sensor, nome, tipo, objetivo, fab, modelo, 
                             lat, lng, val_min, val_max, unidade, cod_cultura]
                    
                    self.cursor.execute(sql_sensor, params)
                    self.sensores_esp32[sensor_key] = novo_cod_sensor
                    print(f"Sensor {nome} criado com codigo: {novo_cod_sensor}")
            
            self.conn.commit()
            print("Sensores ESP32 configurados com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao criar sensores ESP32: {e}")
            self.conn.rollback()
            return False
        finally:
            self.disconnect()

    def carregar_ids_sensores(self):
        """Carrega os IDs dos sensores ESP32 ja criados."""
        if not self.connect():
            return False
            
        try:
            sensores_nomes = {
                'fosforo': 'Sensor Fosforo ESP32',
                'potassio': 'Sensor Potassio ESP32',
                'ph': 'Sensor pH ESP32',
                'umidade': 'Sensor Umidade ESP32',
                'bomba': 'Sensor Bomba ESP32'
            }
            
            for sensor_key, nome in sensores_nomes.items():
                self.cursor.execute("SELECT cod_sensor FROM T_SENSORES WHERE nm_sensor = :1", [nome])
                sensor_row = self.cursor.fetchone()
                if sensor_row:
                    self.sensores_esp32[sensor_key] = sensor_row[0]
                else:
                    print(f"AVISO: Sensor {nome} nao encontrado!")
                    return False
            
            print("IDs dos sensores ESP32 carregados com sucesso!")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao carregar IDs dos sensores: {e}")
            return False
        finally:
            self.disconnect()

    def inserir_medicao_esp32(self, fosforo, potassio, ph, umidade, bomba):
        """Insere uma medicao completa do ESP32 na tabela T_MEDICOES."""
        if not self.connect():
            return False
            
        try:
            # Carrega IDs dos sensores se necessario
            if not all(self.sensores_esp32.values()):
                if not self.carregar_ids_sensores():
                    print("Erro: Sensores ESP32 nao encontrados. Execute a criacao primeiro.")
                    return False
            
            # Obtem proximo codigo de medicao
            self.cursor.execute("SELECT NVL(MAX(cod_medicao), 0) + 1 FROM T_MEDICOES")
            cod_medicao = self.cursor.fetchone()[0]
            
            # Dados para inserir (sensor_key, valor, unidade)
            medicoes_dados = [
                ('fosforo', fosforo, 'UN'),
                ('potassio', potassio, 'UN'),
                ('ph', ph, 'PH'),
                ('umidade', umidade, '%'),
                ('bomba', bomba, 'UN')
            ]
            
            # Insere uma medicao para cada sensor
            sql_medicao = """
            INSERT INTO T_MEDICOES (cod_medicao, data_hora_medicao, valor_medicao, un_medicao, cod_sensor)
            VALUES (:1, SYSTIMESTAMP, :2, :3, :4)
            """
            
            medicoes_inseridas = 0
            for sensor_key, valor, unidade in medicoes_dados:
                cod_sensor = self.sensores_esp32[sensor_key]
                params = [cod_medicao, valor, unidade, cod_sensor]
                
                self.cursor.execute(sql_medicao, params)
                medicoes_inseridas += 1
            
            self.conn.commit()
            logger.info(f"Medicao ESP32 inserida - ID: {cod_medicao}, {medicoes_inseridas} sensores")
            return cod_medicao
            
        except Exception as e:
            logger.error(f"Erro ao inserir medicao ESP32: {e}")
            self.conn.rollback()
            return None
        finally:
            self.disconnect()

    def importar_csv_esp32(self, arquivo_csv):
        """Importa dados CSV do ESP32 para o banco Oracle."""
        if not os.path.exists(arquivo_csv):
            print(f"Arquivo nao encontrado: {arquivo_csv}")
            return False
            
        try:
            with open(arquivo_csv, 'r') as file:
                csv_reader = csv.reader(file)
                
                # Pula cabecalho se existir
                first_line = next(csv_reader)
                if not first_line[0].isdigit():
                    # E cabecalho, continua
                    pass
                else:
                    # Nao e cabecalho, processa a primeira linha
                    self._processar_linha_csv(first_line)
                
                # Processa o resto do arquivo
                count = 0
                for row in csv_reader:
                    if self._processar_linha_csv(row):
                        count += 1
                
                print(f"{count} medicoes ESP32 importadas para o Oracle")
                return True
                
        except Exception as e:
            logger.error(f"Erro ao importar CSV: {e}")
            return False

    def _processar_linha_csv(self, row):
        """Processa uma linha do CSV e insere no banco."""
        try:
            # Formato: timestamp,fosforo,potassio,ph,umidade,bomba_status
            if len(row) >= 6:
                fosforo = int(row[1])
                potassio = int(row[2])
                ph = float(row[3])
                umidade = float(row[4])
                bomba = int(row[5])
                
                return self.inserir_medicao_esp32(fosforo, potassio, ph, umidade, bomba)
            return False
        except (ValueError, IndexError) as e:
            logger.warning(f"Linha CSV invalida: {row} - {e}")
            return False

    def listar_medicoes_recentes(self, limite=10):
        """Lista as medicoes mais recentes do ESP32."""
        if not self.connect():
            return []
            
        try:
            # Busca medicoes dos sensores ESP32
            sql = """
            SELECT m.cod_medicao, m.data_hora_medicao, s.nm_sensor, m.valor_medicao, m.un_medicao
            FROM T_MEDICOES m
            JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
            WHERE s.nm_sensor LIKE '%ESP32%'
            ORDER BY m.data_hora_medicao DESC, m.cod_medicao DESC
            FETCH FIRST :1 ROWS ONLY
            """
            
            self.cursor.execute(sql, [limite * 5])  # 5 sensores por medicao
            rows = self.cursor.fetchall()
            
            # Agrupa por codigo de medicao
            medicoes = {}
            for row in rows:
                cod_medicao = row[0]
                if cod_medicao not in medicoes:
                    medicoes[cod_medicao] = {
                        'id': cod_medicao,
                        'timestamp': row[1],
                        'sensores': {}
                    }
                
                sensor_nome = row[2]
                valor = row[3]
                
                if 'Fosforo' in sensor_nome:
                    medicoes[cod_medicao]['fosforo'] = 'PRESENTE' if valor else 'AUSENTE'
                elif 'Potassio' in sensor_nome:
                    medicoes[cod_medicao]['potassio'] = 'PRESENTE' if valor else 'AUSENTE'
                elif 'pH' in sensor_nome:
                    medicoes[cod_medicao]['ph'] = valor
                elif 'Umidade' in sensor_nome:
                    medicoes[cod_medicao]['umidade'] = valor
                elif 'Bomba' in sensor_nome:
                    medicoes[cod_medicao]['bomba'] = 'LIGADA' if valor else 'DESLIGADA'
            
            return list(medicoes.values())[:limite]
            
        except Exception as e:
            logger.error(f"Erro ao listar medicoes: {e}")
            return []
        finally:
            self.disconnect()

    def obter_estatisticas(self):
        """Calcula estatisticas das medicoes ESP32."""
        if not self.connect():
            return None
            
        try:
            # Estatisticas por tipo de sensor
            stats = {}
            
            sensores_tipos = [
                ('Fosforo', 'fosforo'),
                ('Potassio', 'potassio'),
                ('pH', 'ph'),
                ('Umidade', 'umidade'),
                ('Bomba', 'bomba')
            ]
            
            for sensor_nome, sensor_key in sensores_tipos:
                sql = f"""
                SELECT COUNT(*), AVG(valor_medicao), MIN(valor_medicao), MAX(valor_medicao)
                FROM T_MEDICOES m
                JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
                WHERE s.nm_sensor LIKE '%{sensor_nome}%ESP32%'
                """
                
                self.cursor.execute(sql)
                result = self.cursor.fetchone()
                
                if result and result[0] > 0:
                    stats[sensor_key] = {
                        'total': result[0],
                        'media': round(result[1], 2) if result[1] else 0,
                        'minimo': result[2] if result[2] else 0,
                        'maximo': result[3] if result[3] else 0
                    }
            
            return stats
                
        except Exception as e:
            logger.error(f"Erro ao calcular estatisticas: {e}")
            return None
        finally:
            self.disconnect()

    def exportar_para_csv(self, arquivo_saida):
        """Exporta medicoes ESP32 para um arquivo CSV."""
        if not self.connect():
            return False
            
        try:
            sql = """
            SELECT m.cod_medicao, TO_CHAR(m.data_hora_medicao, 'YYYY-MM-DD HH24:MI:SS'),
                   s.nm_sensor, m.valor_medicao
            FROM T_MEDICOES m
            JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
            WHERE s.nm_sensor LIKE '%ESP32%'
            ORDER BY m.cod_medicao, s.nm_sensor
            """
            
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            
            with open(arquivo_saida, 'w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['cod_medicao', 'timestamp', 'sensor', 'valor'])
                writer.writerows(rows)
            
            print(f"{len(rows)} registros exportados para {arquivo_saida}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao exportar CSV: {e}")
            return False
        finally:
            self.disconnect()


def menu_principal():
    """Interface principal do sistema."""
    manager = FarmTechOracleManager()
    
    print("=== SISTEMA FARMTECH - INTEGRACAO ESP32 + ORACLE (FASE 3) ===")
    print("Conectando ao banco Oracle da Fase 3...")
    
    # Verifica conexao e tabelas
    if not manager.verificar_tabelas_existentes():
        print("Erro: Nao foi possivel conectar ao banco Oracle da Fase 3")
        print("Verifique se o Oracle esta rodando e as credenciais estao corretas")
        return
    
    # Cria sensores ESP32 se necessario
    manager.criar_sensores_esp32()
    
    while True:
        print("\n" + "="*60)
        print("MENU PRINCIPAL - OPERACOES CRUD (ESTRUTURA FASE 3)")
        print("="*60)
        print("1. Visualizar medicoes recentes ESP32")
        print("2. Importar dados CSV do ESP32")
        print("3. Inserir nova medicao ESP32 manualmente")
        print("4. Exibir estatisticas dos sensores ESP32")
        print("5. Exportar dados ESP32 para CSV")
        print("6. Verificar sensores ESP32 criados")
        print("7. Verificar tabelas da Fase 3")
        print("8. CRIAR SENSORES ESP32 (EXECUTAR PRIMEIRO)")
        print("0. Sair")
        print("="*60)
        
        try:
            opcao = input("Escolha uma opcao: ").strip()
            
            if opcao == "1":
                medicoes = manager.listar_medicoes_recentes(10)
                if medicoes:
                    print(f"\nULTIMAS {len(medicoes)} MEDICOES ESP32:")
                    print("-" * 80)
                    for m in medicoes:
                        fosforo = m.get('fosforo', 'N/A')
                        potassio = m.get('potassio', 'N/A')
                        ph = m.get('ph', 'N/A')
                        umidade = m.get('umidade', 'N/A')
                        bomba = m.get('bomba', 'N/A')
                        
                        print(f"ID: {m['id']} | {m['timestamp']} | pH: {ph} | "
                              f"Umidade: {umidade}% | Fosforo: {fosforo} | "
                              f"Potassio: {potassio} | Bomba: {bomba}")
                else:
                    print("Nenhuma medicao ESP32 encontrada")
            
            elif opcao == "2":
                arquivo = input("Digite o caminho do arquivo CSV: ").strip()
                manager.importar_csv_esp32(arquivo)
            
            elif opcao == "3":
                try:
                    print("\nINSERIR NOVA MEDICAO ESP32:")
                    fosforo = int(input("Fosforo presente (0=Nao, 1=Sim): "))
                    potassio = int(input("Potassio presente (0=Nao, 1=Sim): "))
                    ph = float(input("pH do solo (0-14): "))
                    umidade = float(input("Umidade do solo (0-100%): "))
                    bomba = int(input("Bomba ativa (0=Nao, 1=Sim): "))
                    
                    if manager.inserir_medicao_esp32(fosforo, potassio, ph, umidade, bomba):
                        print("Medicao ESP32 inserida com sucesso!")
                    else:
                        print("Erro ao inserir medicao ESP32")
                except ValueError:
                    print("Valores invalidos inseridos")
            
            elif opcao == "4":
                stats = manager.obter_estatisticas()
                if stats:
                    print(f"\nESTATISTICAS DOS SENSORES ESP32:")
                    print("-" * 40)
                    for sensor, dados in stats.items():
                        print(f"{sensor.upper()}: {dados['total']} medicoes | "
                              f"Media: {dados['media']} | "
                              f"Min: {dados['minimo']} | Max: {dados['maximo']}")
                else:
                    print("Nenhuma estatistica encontrada")
            
            elif opcao == "5":
                arquivo = input("Nome do arquivo de saida (ex: medicoes_esp32.csv): ").strip()
                if not arquivo:
                    arquivo = "medicoes_esp32.csv"
                manager.exportar_para_csv(arquivo)
            
            elif opcao == "6":
                manager.carregar_ids_sensores()
                print("Sensores ESP32:")
                for sensor, cod in manager.sensores_esp32.items():
                    print(f"  {sensor}: {cod}")
            
            elif opcao == "7":
                manager.verificar_tabelas_existentes()
            
            elif opcao == "8":
                            print("Criando sensores ESP32...")
                            if manager.criar_sensores_esp32():
                                print("Sensores ESP32 criados com sucesso!")
                                manager.carregar_ids_sensores()
                            else:
                                print("Erro ao criar sensores ESP32")

            elif opcao == "0":
                print("Encerrando sistema FarmTech...")
                break
            
            else:
                print("Opcao invalida!")
                
        except KeyboardInterrupt:
            print("\nSistema encerrado pelo usuario")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    menu_principal()

