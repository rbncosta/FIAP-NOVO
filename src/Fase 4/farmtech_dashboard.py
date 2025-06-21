"""
FarmTech Solutions - Dashboard Interativo com Streamlit
Interface Web para Monitoramento e Predicao de Irrigacao

Este modulo cria uma interface web interativa usando Streamlit
para visualizar dados dos sensores ESP32 e fazer predicoes ML.

Autor: FarmTech Solutions
Data: Junho 2025
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import oracledb
from datetime import datetime, timedelta
import logging
from farmtech_ml import FarmTechMLPredictor

# Configuracao da pagina
st.set_page_config(
    page_title="FarmTech Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS customizado
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #2E8B57;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f8f0;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2E8B57;
    }
    .prediction-card {
        background-color: #fff8dc;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffa500;
    }
</style>
""", unsafe_allow_html=True)

class FarmTechDashboard:
    """Classe para gerenciar o dashboard Streamlit."""
    
    def __init__(self):
        """Inicializa o dashboard."""
        self.predictor = FarmTechMLPredictor()
        
        # Cache de conexao
        if 'oracle_connected' not in st.session_state:
            st.session_state.oracle_connected = False

    @st.cache_data(ttl=300)  # Cache por 5 minutos
    def carregar_dados_sensores(_self):
        """Carrega dados dos sensores ESP32 do Oracle."""
        try:
            if not _self.predictor.connect():
                return None
                
            sql = """
            SELECT 
                m.cod_medicao,
                m.data_hora_medicao,
                s.nm_sensor,
                m.valor_medicao
            FROM T_MEDICOES m
            JOIN T_SENSORES s ON m.cod_sensor = s.cod_sensor
            WHERE s.nm_sensor LIKE '%ESP32%'
            ORDER BY m.data_hora_medicao DESC
            FETCH FIRST 1000 ROWS ONLY
            """
            
            _self.predictor.cursor.execute(sql)
            rows = _self.predictor.cursor.fetchall()
            
            if not rows:
                return None
            
            df = pd.DataFrame(rows, columns=['cod_medicao', 'timestamp', 'sensor', 'valor'])
            
            # Pivotar dados
            df_pivot = df.pivot(index=['cod_medicao', 'timestamp'], 
                               columns='sensor', 
                               values='valor').reset_index()
            
            # Renomear colunas
            column_mapping = {
                'Sensor Fosforo ESP32': 'fosforo',
                'Sensor Potassio ESP32': 'potassio', 
                'Sensor pH ESP32': 'ph',
                'Sensor Umidade ESP32': 'umidade',
                'Sensor Bomba ESP32': 'bomba_ativa'
            }
            
            df_pivot = df_pivot.rename(columns=column_mapping)
            df_pivot = df_pivot.dropna()
            
            # Converter timestamp
            df_pivot['timestamp'] = pd.to_datetime(df_pivot['timestamp'])
            
            return df_pivot
            
        except Exception as e:
            st.error(f"Erro ao carregar dados: {e}")
            return None
        finally:
            _self.predictor.disconnect()

    def exibir_metricas_principais(self, df):
        """Exibe metricas principais em cards."""
        if df is None or len(df) == 0:
            st.warning("Nenhum dado disponivel")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_medicoes = len(df)
            st.metric("Total de Medições", total_medicoes)
        
        with col2:
            ph_medio = df['ph'].mean()
            st.metric("pH Médio", f"{ph_medio:.2f}")
        
        with col3:
            umidade_media = df['umidade'].mean()
            st.metric("Umidade Média", f"{umidade_media:.1f}%")
        
        with col4:
            bomba_ativa_pct = (df['bomba_ativa'].sum() / len(df)) * 100
            st.metric("Bomba Ativa", f"{bomba_ativa_pct:.1f}%")

    def criar_grafico_temporal(self, df):
        """Cria grafico temporal dos sensores."""
        if df is None or len(df) == 0:
            return None
        
        # Criar subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('pH do Solo', 'Umidade do Solo (%)', 
                          'Nutrientes Presentes', 'Status da Bomba'),
            vertical_spacing=0.1
        )
        
        # pH
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['ph'], 
                      name='pH', line=dict(color='blue')),
            row=1, col=1
        )
        
        # Umidade
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['umidade'], 
                      name='Umidade', line=dict(color='green')),
            row=1, col=2
        )
        
        # Nutrientes (empilhado)
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['fosforo'], 
                      name='Fósforo', fill='tonexty', 
                      line=dict(color='orange')),
            row=2, col=1
        )
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['potassio'], 
                      name='Potássio', fill='tonexty',
                      line=dict(color='purple')),
            row=2, col=1
        )
        
        # Bomba
        fig.add_trace(
            go.Scatter(x=df['timestamp'], y=df['bomba_ativa'], 
                      name='Bomba', line=dict(color='red')),
            row=2, col=2
        )
        
        fig.update_layout(
            height=600,
            title_text="Monitoramento dos Sensores ESP32 em Tempo Real",
            showlegend=False
        )
        
        return fig

    def criar_grafico_correlacao(self, df):
        """Cria matriz de correlacao."""
        if df is None or len(df) == 0:
            return None
        
        # Selecionar colunas numericas
        cols_numericas = ['fosforo', 'potassio', 'ph', 'umidade', 'bomba_ativa']
        corr_matrix = df[cols_numericas].corr()
        
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            title="Matriz de Correlação entre Sensores",
            color_continuous_scale="RdBu_r"
        )
        
        return fig

    def criar_grafico_distribuicao(self, df):
        """Cria graficos de distribuicao."""
        if df is None or len(df) == 0:
            return None
        
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=('Distribuição do pH', 'Distribuição da Umidade')
        )
        
        # Histograma pH
        fig.add_trace(
            go.Histogram(x=df['ph'], name='pH', nbinsx=20),
            row=1, col=1
        )
        
        # Histograma Umidade
        fig.add_trace(
            go.Histogram(x=df['umidade'], name='Umidade', nbinsx=20),
            row=1, col=2
        )
        
        fig.update_layout(
            height=400,
            title_text="Distribuição dos Valores dos Sensores",
            showlegend=False
        )
        
        return fig

    def secao_predicao_ml(self):
        """Seção para predição ML interativa."""
        st.header("🤖 Predição Inteligente de Irrigação")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.subheader("Parâmetros dos Sensores")
            
            fosforo = st.selectbox("Fósforo Presente", [0, 1], 
                                  format_func=lambda x: "Não" if x == 0 else "Sim")
            
            potassio = st.selectbox("Potássio Presente", [0, 1],
                                   format_func=lambda x: "Não" if x == 0 else "Sim")
            
            ph = st.slider("pH do Solo", 0.0, 14.0, 7.0, 0.1)
            
            umidade = st.slider("Umidade do Solo (%)", 0.0, 100.0, 50.0, 1.0)
            
            modelo = st.selectbox("Modelo ML", 
                                 ["random_forest", "logistic_regression"],
                                 format_func=lambda x: "Random Forest" if x == "random_forest" else "Regressão Logística")
        
        with col2:
            st.subheader("Resultado da Predição")
            
            if st.button("🔮 Fazer Predição", type="primary"):
                with st.spinner("Processando predição..."):
                    resultado = self.predictor.prever_irrigacao(fosforo, potassio, ph, umidade, modelo)
                
                if resultado:
                    # Card de resultado
                    if resultado['irrigacao_necessaria']:
                        st.success("💧 **IRRIGAÇÃO RECOMENDADA**")
                        cor_bomba = "🟢"
                    else:
                        st.info("🚫 **IRRIGAÇÃO NÃO NECESSÁRIA**")
                        cor_bomba = "🔴"
                    
                    # Métricas da predição
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.metric("Probabilidade de Irrigar", 
                                f"{resultado['probabilidade_irrigar']:.1%}")
                    with col_b:
                        st.metric("Confiança da Predição", 
                                f"{resultado['confianca']:.1%}")
                    
                    # Gráfico de probabilidades
                    prob_data = pd.DataFrame({
                        'Ação': ['Não Irrigar', 'Irrigar'],
                        'Probabilidade': [resultado['probabilidade_nao_irrigar'], 
                                        resultado['probabilidade_irrigar']]
                    })
                    
                    fig_prob = px.bar(prob_data, x='Ação', y='Probabilidade',
                                     title="Probabilidades da Predição",
                                     color='Probabilidade',
                                     color_continuous_scale="viridis")
                    st.plotly_chart(fig_prob, use_container_width=True)
                    
                else:
                    st.error("Erro na predição. Verifique se os modelos foram treinados.")

    def secao_analise_features(self):
        """Seção para análise de importância das features."""
        st.header("📊 Análise de Importância das Features")
        
        importancia = self.predictor.obter_importancia_features()
        
        if importancia:
            # Converter para DataFrame
            df_imp = pd.DataFrame(list(importancia.items()), 
                                 columns=['Feature', 'Importancia'])
            
            # Gráfico de barras
            fig_imp = px.bar(df_imp, x='Importancia', y='Feature',
                            orientation='h',
                            title="Importância das Features no Modelo Random Forest",
                            color='Importancia',
                            color_continuous_scale="viridis")
            
            fig_imp.update_layout(height=500)
            st.plotly_chart(fig_imp, use_container_width=True)
            
            # Tabela detalhada
            st.subheader("Detalhes das Features")
            df_imp['Importancia_Pct'] = (df_imp['Importancia'] * 100).round(2)
            st.dataframe(df_imp[['Feature', 'Importancia_Pct']], 
                        column_config={
                            'Feature': 'Feature',
                            'Importancia_Pct': st.column_config.NumberColumn(
                                'Importância (%)',
                                format="%.2f%%"
                            )
                        })
        else:
            st.warning("Modelos ML não encontrados. Execute o treinamento primeiro.")

    def secao_estatisticas(self, df):
        """Seção de estatísticas detalhadas."""
        st.header("📈 Estatísticas Detalhadas")
        
        if df is None or len(df) == 0:
            st.warning("Nenhum dado disponível para estatísticas")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Estatísticas Descritivas")
            stats = df[['ph', 'umidade']].describe()
            st.dataframe(stats)
        
        with col2:
            st.subheader("Contadores")
            
            # Nutrientes
            fosforo_count = df['fosforo'].value_counts()
            potassio_count = df['potassio'].value_counts()
            bomba_count = df['bomba_ativa'].value_counts()
            
            st.write("**Fósforo:**")
            st.write(f"Presente: {fosforo_count.get(1, 0)} | Ausente: {fosforo_count.get(0, 0)}")
            
            st.write("**Potássio:**")
            st.write(f"Presente: {potassio_count.get(1, 0)} | Ausente: {potassio_count.get(0, 0)}")
            
            st.write("**Bomba:**")
            st.write(f"Ativa: {bomba_count.get(1, 0)} | Inativa: {bomba_count.get(0, 0)}")

def main():
    """Função principal do dashboard."""
    # Header
    st.markdown('<h1 class="main-header">🌱 FarmTech Dashboard</h1>', 
                unsafe_allow_html=True)
    st.markdown("**Sistema Inteligente de Irrigação - Monitoramento e Predição ML**")
    
    # Inicializar dashboard
    dashboard = FarmTechDashboard()
    
    # Sidebar
    st.sidebar.title("🎛️ Controles")
    
    # Seleção de página
    pagina = st.sidebar.selectbox(
        "Escolha a página:",
        ["📊 Monitoramento", "🤖 Predição ML", "📈 Análise Features", "📋 Estatísticas"]
    )
    
    # Botão de atualização
    if st.sidebar.button("🔄 Atualizar Dados"):
        st.cache_data.clear()
        st.rerun()
    
    # Carregar dados
    with st.spinner("Carregando dados dos sensores..."):
        df = dashboard.carregar_dados_sensores()
    
    # Verificar se há dados
    if df is None or len(df) == 0:
        st.error("❌ Nenhum dado encontrado no banco Oracle")
        st.info("💡 Certifique-se de que:")
        st.write("- O Oracle está rodando")
        st.write("- Os sensores ESP32 foram criados")
        st.write("- Dados foram importados do CSV")
        return
    
    # Exibir métricas principais
    dashboard.exibir_metricas_principais(df)
    
    st.divider()
    
    # Páginas
    if pagina == "📊 Monitoramento":
        st.header("📊 Monitoramento em Tempo Real")
        
        # Gráfico temporal
        fig_temporal = dashboard.criar_grafico_temporal(df)
        if fig_temporal:
            st.plotly_chart(fig_temporal, use_container_width=True)
        
        # Gráficos adicionais
        col1, col2 = st.columns(2)
        
        with col1:
            fig_corr = dashboard.criar_grafico_correlacao(df)
            if fig_corr:
                st.plotly_chart(fig_corr, use_container_width=True)
        
        with col2:
            fig_dist = dashboard.criar_grafico_distribuicao(df)
            if fig_dist:
                st.plotly_chart(fig_dist, use_container_width=True)
    
    elif pagina == "🤖 Predição ML":
        dashboard.secao_predicao_ml()
    
    elif pagina == "📈 Análise Features":
        dashboard.secao_analise_features()
    
    elif pagina == "📋 Estatísticas":
        dashboard.secao_estatisticas(df)
    
    # Footer
    st.divider()
    st.markdown("**FarmTech Solutions** - Sistema Inteligente de Irrigação | Fase 4")

if __name__ == "__main__":
    main()

