"""
FarmTech Solutions - Modulo de Machine Learning
Sistema de Predicao Inteligente para Irrigacao

Este modulo complementa o sistema CRUD existente, adicionando
capacidades de machine learning para predicao de necessidade
de irrigacao baseada em dados historicos.

Autor: FarmTech Solutions
Data: Junho 2025
"""

import oracledb
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
import logging
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Configuracao de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FarmTechMLPredictor:
    """
    Classe para predicao inteligente de irrigacao usando Machine Learning.
    Utiliza dados historicos dos sensores ESP32 para treinar modelos preditivos.
    """
    
    def __init__(self):
        """Inicializa o preditor ML com configuracoes Oracle da Fase 3."""
        # Configuracoes de conexao Oracle (mesmas do sistema CRUD)
        self.host = "localhost"
        self.port = 1522
        self.service_name = "ORCLPDB"
        self.user = "RCOSTA"
        self.password = "Rcosta@1980"
        
        self.conn = None
        self.cursor = None
        
        # Modelos ML
        self.rf_model = None
        self.lr_model = None
        self.scaler = StandardScaler()
        
        # Metricas de performance
        self.model_metrics = {}

    def connect(self):
        """Estabelece conexao com o banco Oracle existente."""
        try:
            dsn = oracledb.makedsn(self.host, self.port, service_name=self.service_name)
            self.conn = oracledb.connect(user=self.user, password=self.password, dsn=dsn)
            self.cursor = self.conn.cursor()
            logger.info("Conectado ao Oracle para ML")
            return True
        except oracledb.DatabaseError as e:
            logger.error(f"Erro de conexao Oracle ML: {e}")
            return False

    def disconnect(self):
        """Fecha a conexao com o banco."""
        if self.conn:
            if self.cursor:
                self.cursor.close()
            self.conn.close()
            self.conn = None
            self.cursor = None
            logger.info("Conexao Oracle ML encerrada")

    def carregar_dados_historicos(self):
        """Carrega dados historicos dos sensores ESP32 para treinamento."""
        if not self.connect():
            return None
            
        try:
            # Query para buscar dados dos sensores ESP32
            sql = """
            SELECT 
                m.cod_medicao,
                m.data_hora_medicao,
                s.nm_sensor,
                m.valor_medicao
            FROM T_MEDICOES m
            JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
            WHERE s.nm_sensor LIKE '%ESP32%'
            ORDER BY m.cod_medicao, s.nm_sensor
            """
            
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            
            if not rows:
                logger.warning("Nenhum dado ESP32 encontrado para ML")
                return None
            
            # Converter para DataFrame
            df = pd.DataFrame(rows, columns=['cod_medicao', 'timestamp', 'sensor', 'valor'])
            
            # Pivotar dados para ter uma linha por medicao
            df_pivot = df.pivot(index=['cod_medicao', 'timestamp'], 
                               columns='sensor', 
                               values='valor').reset_index()
            
            # Renomear colunas para facilitar uso
            column_mapping = {
                'Sensor Fosforo ESP32': 'fosforo',
                'Sensor Potassio ESP32': 'potassio', 
                'Sensor pH ESP32': 'ph',
                'Sensor Umidade ESP32': 'umidade',
                'Sensor Bomba ESP32': 'bomba_ativa'
            }
            
            df_pivot = df_pivot.rename(columns=column_mapping)
            
            # Remover linhas com dados faltantes
            df_pivot = df_pivot.dropna()
            
            logger.info(f"Dados carregados: {len(df_pivot)} medicoes para ML")
            return df_pivot
            
        except Exception as e:
            logger.error(f"Erro ao carregar dados historicos: {e}")
            return None
        finally:
            self.disconnect()

    def preparar_features(self, df):
        """Prepara features para treinamento do modelo."""
        try:
            # Features de entrada (X)
            features = ['fosforo', 'potassio', 'ph', 'umidade']
            X = df[features].copy()
            
            # Target (y) - bomba ativa ou nao
            y = df['bomba_ativa'].copy()
            
            # Criar features adicionais
            X['ph_ideal'] = ((X['ph'] >= 6.0) & (X['ph'] <= 8.0)).astype(int)
            X['umidade_baixa'] = (X['umidade'] < 30).astype(int)
            X['umidade_alta'] = (X['umidade'] > 70).astype(int)
            X['nutrientes_completos'] = ((X['fosforo'] == 1) & (X['potassio'] == 1)).astype(int)
            X['sem_nutrientes'] = ((X['fosforo'] == 0) & (X['potassio'] == 0)).astype(int)
            
            # Interacoes entre features
            X['ph_umidade'] = X['ph'] * X['umidade']
            X['nutrientes_ph'] = X['nutrientes_completos'] * X['ph_ideal']
            
            logger.info(f"Features preparadas: {X.shape[1]} colunas, {X.shape[0]} amostras")
            return X, y
            
        except Exception as e:
            logger.error(f"Erro ao preparar features: {e}")
            return None, None

    def treinar_modelos(self, X, y):
        """Treina modelos de machine learning."""
        try:
            # Dividir dados em treino e teste
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Normalizar features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Modelo 1: Random Forest
            self.rf_model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42,
                class_weight='balanced'
            )
            self.rf_model.fit(X_train, y_train)
            
            # Modelo 2: Logistic Regression
            self.lr_model = LogisticRegression(
                random_state=42,
                class_weight='balanced',
                max_iter=1000
            )
            self.lr_model.fit(X_train_scaled, y_train)
            
            # Avaliar modelos
            self._avaliar_modelos(X_test, X_test_scaled, y_test)
            
            # Salvar modelos
            self._salvar_modelos()
            
            logger.info("Modelos treinados com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao treinar modelos: {e}")
            return False

    def _avaliar_modelos(self, X_test, X_test_scaled, y_test):
        """Avalia performance dos modelos treinados."""
        try:
            # Predicoes Random Forest
            rf_pred = self.rf_model.predict(X_test)
            rf_accuracy = accuracy_score(y_test, rf_pred)
            
            # Predicoes Logistic Regression  
            lr_pred = self.lr_model.predict(X_test_scaled)
            lr_accuracy = accuracy_score(y_test, lr_pred)
            
            # Armazenar metricas
            self.model_metrics = {
                'random_forest': {
                    'accuracy': rf_accuracy,
                    'classification_report': classification_report(y_test, rf_pred, output_dict=True),
                    'confusion_matrix': confusion_matrix(y_test, rf_pred).tolist()
                },
                'logistic_regression': {
                    'accuracy': lr_accuracy,
                    'classification_report': classification_report(y_test, lr_pred, output_dict=True),
                    'confusion_matrix': confusion_matrix(y_test, lr_pred).tolist()
                }
            }
            
            logger.info(f"Random Forest Accuracy: {rf_accuracy:.3f}")
            logger.info(f"Logistic Regression Accuracy: {lr_accuracy:.3f}")
            
        except Exception as e:
            logger.error(f"Erro ao avaliar modelos: {e}")

    def _salvar_modelos(self):
        """Salva modelos treinados em disco."""
        try:
            joblib.dump(self.rf_model, 'farmtech_rf_model.pkl')
            joblib.dump(self.lr_model, 'farmtech_lr_model.pkl')
            joblib.dump(self.scaler, 'farmtech_scaler.pkl')
            logger.info("Modelos salvos em disco")
        except Exception as e:
            logger.error(f"Erro ao salvar modelos: {e}")

    def carregar_modelos(self):
        """Carrega modelos pre-treinados do disco."""
        try:
            self.rf_model = joblib.load('farmtech_rf_model.pkl')
            self.lr_model = joblib.load('farmtech_lr_model.pkl')
            self.scaler = joblib.load('farmtech_scaler.pkl')
            logger.info("Modelos carregados do disco")
            return True
        except Exception as e:
            logger.warning(f"Erro ao carregar modelos: {e}")
            return False

    def prever_irrigacao(self, fosforo, potassio, ph, umidade, modelo='random_forest'):
        """Faz predicao de necessidade de irrigacao."""
        try:
            # Verificar se modelos estao carregados
            if self.rf_model is None or self.lr_model is None:
                if not self.carregar_modelos():
                    logger.error("Modelos nao disponiveis para predicao")
                    return None
            
            # Preparar dados de entrada
            dados = pd.DataFrame({
                'fosforo': [fosforo],
                'potassio': [potassio],
                'ph': [ph],
                'umidade': [umidade]
            })
            
            # Criar features adicionais (mesma logica do treinamento)
            dados['ph_ideal'] = ((dados['ph'] >= 6.0) & (dados['ph'] <= 8.0)).astype(int)
            dados['umidade_baixa'] = (dados['umidade'] < 30).astype(int)
            dados['umidade_alta'] = (dados['umidade'] > 70).astype(int)
            dados['nutrientes_completos'] = ((dados['fosforo'] == 1) & (dados['potassio'] == 1)).astype(int)
            dados['sem_nutrientes'] = ((dados['fosforo'] == 0) & (dados['potassio'] == 0)).astype(int)
            dados['ph_umidade'] = dados['ph'] * dados['umidade']
            dados['nutrientes_ph'] = dados['nutrientes_completos'] * dados['ph_ideal']
            
            # Fazer predicao
            if modelo == 'random_forest':
                predicao = self.rf_model.predict(dados)[0]
                probabilidade = self.rf_model.predict_proba(dados)[0]
            else:
                dados_scaled = self.scaler.transform(dados)
                predicao = self.lr_model.predict(dados_scaled)[0]
                probabilidade = self.lr_model.predict_proba(dados_scaled)[0]
            
            # Interpretar resultado
            resultado = {
                'irrigacao_necessaria': bool(predicao),
                'probabilidade_nao_irrigar': float(probabilidade[0]),
                'probabilidade_irrigar': float(probabilidade[1]),
                'confianca': float(max(probabilidade)),
                'modelo_usado': modelo,
                'dados_entrada': {
                    'fosforo': fosforo,
                    'potassio': potassio,
                    'ph': ph,
                    'umidade': umidade
                }
            }
            
            return resultado
            
        except Exception as e:
            logger.error(f"Erro na predicao: {e}")
            return None

    def obter_importancia_features(self):
        """Retorna importancia das features do modelo Random Forest."""
        try:
            if self.rf_model is None:
                if not self.carregar_modelos():
                    return None
            
            # Nomes das features (deve corresponder ao treinamento)
            feature_names = [
                'fosforo', 'potassio', 'ph', 'umidade', 'ph_ideal',
                'umidade_baixa', 'umidade_alta', 'nutrientes_completos',
                'sem_nutrientes', 'ph_umidade', 'nutrientes_ph'
            ]
            
            importancias = self.rf_model.feature_importances_
            
            # Criar dicionario ordenado por importancia
            feature_importance = dict(zip(feature_names, importancias))
            feature_importance = dict(sorted(feature_importance.items(), 
                                           key=lambda x: x[1], reverse=True))
            
            return feature_importance
            
        except Exception as e:
            logger.error(f"Erro ao obter importancia das features: {e}")
            return None

    def gerar_relatorio_ml(self):
        """Gera relatorio completo de machine learning."""
        try:
            relatorio = {
                'timestamp': datetime.now().isoformat(),
                'modelos_disponiveis': {
                    'random_forest': self.rf_model is not None,
                    'logistic_regression': self.lr_model is not None
                },
                'metricas': self.model_metrics,
                'importancia_features': self.obter_importancia_features()
            }
            
            return relatorio
            
        except Exception as e:
            logger.error(f"Erro ao gerar relatorio ML: {e}")
            return None

    def treinar_pipeline_completo(self):
        """Executa pipeline completo de treinamento."""
        try:
            print("=== FARMTECH ML - PIPELINE DE TREINAMENTO ===")
            
            # 1. Carregar dados
            print("1. Carregando dados historicos...")
            df = self.carregar_dados_historicos()
            if df is None or len(df) < 10:
                print("ERRO: Dados insuficientes para treinamento (minimo 10 amostras)")
                return False
            
            print(f"   Dados carregados: {len(df)} medicoes")
            
            # 2. Preparar features
            print("2. Preparando features...")
            X, y = self.preparar_features(df)
            if X is None:
                print("ERRO: Falha na preparacao das features")
                return False
            
            print(f"   Features: {X.shape[1]} colunas")
            print(f"   Distribuicao target: {y.value_counts().to_dict()}")
            
            # 3. Treinar modelos
            print("3. Treinando modelos...")
            if not self.treinar_modelos(X, y):
                print("ERRO: Falha no treinamento dos modelos")
                return False
            
            # 4. Exibir resultados
            print("4. Resultados do treinamento:")
            if self.model_metrics:
                for modelo, metricas in self.model_metrics.items():
                    print(f"   {modelo}: Accuracy = {metricas['accuracy']:.3f}")
            
            # 5. Teste de predicao
            print("5. Teste de predicao:")
            teste_predicao = self.prever_irrigacao(0, 1, 7.2, 45.0)
            if teste_predicao:
                print(f"   Exemplo: Irrigacao = {teste_predicao['irrigacao_necessaria']}")
                print(f"   Confianca: {teste_predicao['confianca']:.3f}")
            
            print("=== TREINAMENTO CONCLUIDO COM SUCESSO ===")
            return True
            
        except Exception as e:
            logger.error(f"Erro no pipeline de treinamento: {e}")
            print(f"ERRO: {e}")
            return False


def menu_ml():
    """Interface de linha de comando para o modulo ML."""
    predictor = FarmTechMLPredictor()
    
    while True:
        print("\n" + "="*60)
        print("FARMTECH ML - MACHINE LEARNING PARA IRRIGACAO")
        print("="*60)
        print("1. Treinar modelos com dados historicos")
        print("2. Fazer predicao de irrigacao")
        print("3. Exibir importancia das features")
        print("4. Gerar relatorio completo ML")
        print("5. Carregar modelos existentes")
        print("0. Voltar ao menu principal")
        print("="*60)
        
        try:
            opcao = input("Escolha uma opcao: ").strip()
            
            if opcao == "1":
                predictor.treinar_pipeline_completo()
            
            elif opcao == "2":
                try:
                    print("\nDIGITE OS VALORES DOS SENSORES:")
                    fosforo = int(input("Fosforo presente (0=Nao, 1=Sim): "))
                    potassio = int(input("Potassio presente (0=Nao, 1=Sim): "))
                    ph = float(input("pH do solo (0-14): "))
                    umidade = float(input("Umidade do solo (0-100%): "))
                    
                    print("\nESCOLHA O MODELO:")
                    print("1. Random Forest")
                    print("2. Logistic Regression")
                    modelo_opcao = input("Modelo (1 ou 2): ").strip()
                    
                    modelo = 'random_forest' if modelo_opcao == '1' else 'logistic_regression'
                    
                    resultado = predictor.prever_irrigacao(fosforo, potassio, ph, umidade, modelo)
                    
                    if resultado:
                        print(f"\n=== RESULTADO DA PREDICAO ===")
                        print(f"Irrigacao necessaria: {'SIM' if resultado['irrigacao_necessaria'] else 'NAO'}")
                        print(f"Probabilidade de irrigar: {resultado['probabilidade_irrigar']:.1%}")
                        print(f"Confianca da predicao: {resultado['confianca']:.1%}")
                        print(f"Modelo usado: {resultado['modelo_usado']}")
                    else:
                        print("Erro na predicao. Verifique se os modelos foram treinados.")
                        
                except ValueError:
                    print("Valores invalidos inseridos")
            
            elif opcao == "3":
                importancia = predictor.obter_importancia_features()
                if importancia:
                    print(f"\n=== IMPORTANCIA DAS FEATURES ===")
                    for feature, valor in importancia.items():
                        print(f"{feature}: {valor:.3f}")
                else:
                    print("Erro ao obter importancia. Verifique se os modelos foram treinados.")
            
            elif opcao == "4":
                relatorio = predictor.gerar_relatorio_ml()
                if relatorio:
                    print(f"\n=== RELATORIO ML ===")
                    print(f"Timestamp: {relatorio['timestamp']}")
                    print(f"Modelos disponiveis: {relatorio['modelos_disponiveis']}")
                    if relatorio['metricas']:
                        print("Metricas dos modelos:")
                        for modelo, metricas in relatorio['metricas'].items():
                            print(f"  {modelo}: {metricas['accuracy']:.3f}")
                else:
                    print("Erro ao gerar relatorio")
            
            elif opcao == "5":
                if predictor.carregar_modelos():
                    print("Modelos carregados com sucesso!")
                else:
                    print("Erro ao carregar modelos. Execute o treinamento primeiro.")
            
            elif opcao == "0":
                break
            
            else:
                print("Opcao invalida!")
                
        except KeyboardInterrupt:
            print("\nSistema ML encerrado pelo usuario")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")


if __name__ == "__main__":
    menu_ml()

