import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import io
import time
from datetime import datetime, timedelta

# --- NOVA FUNÇÃO: previsão do pagamento para o mês atual ---
def calcular_previsao_mes_atual_market(market_data):
    """
    Recebe o DataFrame `market_data` (retornado por fetch_market_data),
    que deve conter, entre outras colunas, um possível DataFrame em cada linha 
    na coluna 'Historico_Dividendos'. Retorna uma Series com o valor projetado 
    do pagamento (aluguel/dividendo) para o mês atual para cada ticker.
    """
    hoje = datetime.now()
    ano_atual = hoje.year
    mes_atual = hoje.month
    
    previsoes = {}
    
    for ticker, row in market_data.iterrows():
        df_hist = row.get('Historico_Dividendos', None)
        
        if isinstance(df_hist, pd.DataFrame):
            # Garantir que 'Data' está no tipo datetime
            df_hist['Data'] = pd.to_datetime(df_hist['Data'])
            
            # 1) Tentativa de pegar pagamento no mês/ano atuais
            pagos_mes = df_hist[
                (df_hist['Data'].dt.year == ano_atual) &
                (df_hist['Data'].dt.month == mes_atual)
            ]
            if not pagos_mes.empty:
                # Pega o último valor deste mês
                ultimo = pagos_mes.sort_values("Data", ascending=False).iloc[0]
                previsoes[ticker] = float(ultimo['Valor'])
            else:
                # Não há pagamento neste mês; usar último antes do 1º dia do mês
                primeiro_dia_mes = datetime(ano_atual, mes_atual, 1)
                pagos_anteriores = df_hist[df_hist['Data'] < primeiro_dia_mes]
                if not pagos_anteriores.empty:
                    ultimo_ant = pagos_anteriores.sort_values("Data", ascending=False).iloc[0]
                    previsoes[ticker] = float(ultimo_ant['Valor'])
                else:
                    previsoes[ticker] = float("nan")
        else:
            # Sem histórico de dividendos/aluguel
            previsoes[ticker] = float("nan")
    
    return pd.Series(previsoes, name="Prev_Pag_Mes_Atual")


# --- Funções Auxiliares Originais (copiadas do seu código anterior) --- #

@st.cache_data
def load_excel_data(uploaded_file):
    """Carrega os dados das abas do arquivo Excel enviado pelo usuário."""
    try:
        df_historico = pd.read_excel(
            uploaded_file,
            sheet_name='Historico_Compras',
            parse_dates=['Data_Compra']
        )
        df_watchlist = pd.read_excel(uploaded_file, sheet_name='Watchlist')
        
        # Garantir que Codigo_Ativo seja string e remover espaços
        df_historico['Codigo_Ativo'] = df_historico['Codigo_Ativo'].astype(str).str.strip()
        df_watchlist['Codigo_Ativo'] = df_watchlist['Codigo_Ativo'].astype(str).str.strip()
        
        # Validar colunas essenciais
        required_hist_cols = [
            'Data_Compra', 'Codigo_Ativo', 'Tipo_Ativo',
            'Quantidade', 'Preco_Compra_Unitario'
        ]
        required_watch_cols = ['Codigo_Ativo', 'Tipo_Ativo']
        
        if not all(col in df_historico.columns for col in required_hist_cols):
            st.error(f"A aba 'Historico_Compras' deve conter as colunas: {', '.join(required_hist_cols)}")
            return None, None
            
        if not all(col in df_watchlist.columns for col in required_watch_cols):
            st.error(f"A aba 'Watchlist' deve conter as colunas: {', '.join(required_watch_cols)}")
            return None, None
            
        # Adicionar coluna Corretagem_Taxas se não existir
        if 'Corretagem_Taxas' not in df_historico.columns:
            df_historico['Corretagem_Taxas'] = 0
        df_historico['Corretagem_Taxas'] = df_historico['Corretagem_Taxas'].fillna(0)

        return df_historico, df_watchlist
    except Exception as e:
        st.error(f"Erro ao ler o arquivo Excel: {e}. Verifique o formato e as abas ('Historico_Compras', 'Watchlist').")
        return None, None

def create_example_excel():
    """Cria um arquivo Excel de exemplo para download."""
    data_historico = {
        'Data_Compra': pd.to_datetime([
            '2024-01-15', '2024-02-20', '2024-03-10',
            '2024-04-05', '2025-01-10'
        ]),
        'Codigo_Ativo': ['XPLG11', 'HGLG11', 'ITUB4', 'XPLG11', 'MXRF11'],
        'Tipo_Ativo': ['FII', 'FII', 'Ação', 'FII', 'FII'],
        'Quantidade': [50, 30, 100, 25, 200],
        'Preco_Compra_Unitario': [95.50, 158.20, 28.50, 99.80, 10.15],
        'Corretagem_Taxas': [4.90, 4.90, 4.90, 2.50, 0]
    }
    df_historico = pd.DataFrame(data_historico)
    df_historico['Valor_Total_Compra'] = (
        df_historico['Quantidade'] * df_historico['Preco_Compra_Unitario']
    ) + df_historico['Corretagem_Taxas']

    data_watchlist = {
        'Codigo_Ativo': [
            'XPLG11', 'HGLG11', 'ITUB4', 'MXRF11', 'VALE3',
            'KNRI11', 'VISC11', 'MALL11', 'CPTS11', 'TVRI11',
            'HGRE11', 'VGHF11', 'VRTA11', 'XPML11'
        ],
        'Tipo_Ativo': [
            'FII', 'FII', 'Ação', 'FII', 'Ação', 'FII', 'FII',
            'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII'
        ],
        'Setor': [
            'Logística', 'Logística', 'Bancário', 'Papel',
            'Mineração', 'Misto', 'Shoppings', 'Shoppings',
            'Papel', 'Agências de Bancos', 'Lajes Corporativas',
            'Misto', 'Papéis', 'Shoppings'
        ],
        'Nome_Ativo': [
            'XP Log FII', 'CSHG Logística FII',
            'Itaú Unibanco Holding SA', 'Maxi Renda FII',
            'Vale S.A.', 'Kinea Renda Imobiliária FII',
            'Vinci Shopping Centers FII', 'Malls Brasil Plural FII',
            'Capitânia Securities II FII', 'Tivio Renda Imobiliária FII',
            'CSHG Real Estate FII', 'Valora Hedge Fund FII',
            'Votorantim Renda Varejo FII', 'XP Malls FII'
        ],
        'Observacoes': [
            'Acompanhar vacância', 'Dividendo estável',
            'Aguardar balanço', 'FII de Papel popular',
            'Volatilidade commodities', 'Bom histórico',
            '', '', '', '', '', '', '', ''
        ]
    }
    df_watchlist = pd.DataFrame(data_watchlist)

    # Criar arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_historico.to_excel(writer, sheet_name='Historico_Compras', index=False)
        df_watchlist.to_excel(writer, sheet_name='Watchlist', index=False)
    
    return output.getvalue()

def gerar_dados_historicos_simulados(ticker, preco_atual, volatilidade=0.02, dias=365):
    """Gera dados históricos simulados para um ticker."""
    hoje = datetime.now()
    datas = [
        (hoje - timedelta(days=i)).strftime('%Y-%m-%d')
        for i in range(dias, 0, -1)
    ]
    
    # Gerar preços com tendência aleatória
    np.random.seed(hash(ticker) % 10000)  # Seed baseado no ticker para consistência
    tendencia = np.random.choice([-0.1, 0.1])  # Tendência de alta ou baixa
    
    # Simulação de movimento browniano geométrico
    retornos_diarios = np.random.normal(tendencia/dias, volatilidade, dias)
    precos = [preco_atual]
    
    for retorno in reversed(retornos_diarios[:-1]):
        precos.append(precos[-1] * (1 - retorno))
    
    precos.reverse()  # Ordem cronológica
    
    # Adicionar dividendos simulados (a cada ~60 dias para FIIs)
    dividendos = [0] * dias
    if 'FII' in ticker.upper():
        for i in range(30, dias, 60):
            dividendos[i] = precos[i] * np.random.uniform(0.005, 0.01)  # 0.5% a 1% do preço
    
    df = pd.DataFrame({
        'Data': pd.to_datetime(datas),
        'Preço': precos,
        'Dividendos': dividendos
    })
    
    return df

def criar_grafico_historico(ticker, dados_historicos, periodo='1a'):
    """Cria um gráfico de linhas interativo para o histórico de preços."""
    hoje = datetime.now()
    if periodo == '1m':
        data_inicio = hoje - timedelta(days=30)
    elif periodo == '3m':
        data_inicio = hoje - timedelta(days=90)
    elif periodo == '6m':
        data_inicio = hoje - timedelta(days=180)
    elif periodo == 'YTD':
        data_inicio = datetime(hoje.year, 1, 1)
    else:  # 1a (padrão)
        data_inicio = hoje - timedelta(days=365)
    
    df_filtrado = dados_historicos[dados_historicos['Data'] >= data_inicio]
    
    fig = px.line(
        df_filtrado, 
        x='Data', 
        y='Preço',
        title=f'Histórico de Preços - {ticker}',
        labels={'Data': '', 'Preço': 'Preço (R$)'},
        template='plotly_white'
    )
    fig.update_traces(line=dict(width=2, color='#1f77b4'))
    
    # Adicionar marcadores para dividendos (se houver coluna 'Dividendos')
    if 'Dividendos' in df_filtrado.columns:
        div_dates = df_filtrado[df_filtrado['Dividendos'] > 0]
        if not div_dates.empty:
            fig.add_scatter(
                x=div_dates['Data'], 
                y=div_dates['Preço'],
                mode='markers',
                marker=dict(size=8, symbol='diamond', color='green'),
                name='Dividendo',
                hovertemplate='Data: %{x}<br>Preço: R$ %{y:.2f}<br>Dividendo: R$ %{text:.2f}',
                text=div_dates['Dividendos']
            )
    
    fig.update_layout(
        height=400,
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode='x unified',
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    )
    
    return fig

@st.cache_data(ttl=900)
def fetch_market_data(tickers):
    """Simula a busca de dados de mercado para uma lista de tickers."""
    market_data = {}
    
    sample_data = {
        'XPLG11': {'Preco_Atual': 99.70, 'Var_Dia_Pct': 0.41, 'P_VP': 0.93,
                   'DY_12M_Pct': 10.24, 'Liquidez_Diaria_Vol': 3226098},
        'HGLG11': {'Preco_Atual': 160.23, 'Var_Dia_Pct': 0.14, 'P_VP': 0.98,
                   'DY_12M_Pct': 8.79, 'Liquidez_Diaria_Vol': 5714559},
        'ITUB4':  {'Preco_Atual': 37.79, 'Var_Dia_Pct': 0.69, 'P_VP': 1.25,
                   'DY_12M_Pct': 5.32, 'Liquidez_Diaria_Vol': 15000000},
        'MXRF11': {'Preco_Atual': 9.52, 'Var_Dia_Pct': 0.53, 'P_VP': 0.85,
                   'DY_12M_Pct': 13.25, 'Liquidez_Diaria_Vol': 8125365},
        'VALE3':  {'Preco_Atual': 53.41, 'Var_Dia_Pct': -2.25, 'P_VP': 1.15,
                   'DY_12M_Pct': 6.75, 'Liquidez_Diaria_Vol': 25000000},
        'KNRI11': {'Preco_Atual': 145.70, 'Var_Dia_Pct': 0.48, 'P_VP': 0.90,
                   'DY_12M_Pct': 8.80, 'Liquidez_Diaria_Vol': 6478154},
        'VISC11': {'Preco_Atual': 103.30, 'Var_Dia_Pct': -0.54, 'P_VP': 0.84,
                   'DY_12M_Pct': 9.84, 'Liquidez_Diaria_Vol': 3852021},
        'MALL11': {'Preco_Atual': 101.40, 'Var_Dia_Pct': -0.59, 'P_VP': 0.84,
                   'DY_12M_Pct': 10.03, 'Liquidez_Diaria_Vol': 3082284},
        'CPTS11': {'Preco_Atual': 7.36, 'Var_Dia_Pct': -0.94, 'P_VP': 0.85,
                   'DY_12M_Pct': 13.25, 'Liquidez_Diaria_Vol': 8125365},
        'TVRI11': {'Preco_Atual': 91.62, 'Var_Dia_Pct': 0.35, 'P_VP': 0.90,
                   'DY_12M_Pct': 13.59, 'Liquidez_Diaria_Vol': 1033718},
        'HGRE11': {'Preco_Atual': 113.60, 'Var_Dia_Pct': 1.21, 'P_VP': 0.74,
                   'DY_12M_Pct': 9.94, 'Liquidez_Diaria_Vol': 1648659},
        'VGHF11': {'Preco_Atual': 7.75, 'Var_Dia_Pct': 0.39, 'P_VP': 0.91,
                   'DY_12M_Pct': 14.27, 'Liquidez_Diaria_Vol': 2954165},
        'VRTA11': {'Preco_Atual': 81.55, 'Var_Dia_Pct': -0.60, 'P_VP': 0.92,
                   'DY_12M_Pct': 12.92, 'Liquidez_Diaria_Vol': 1449132},
        'XPML11': {'Preco_Atual': 104.34, 'Var_Dia_Pct': 0.14, 'P_VP': 0.89,
                   'DY_12M_Pct': 11.07, 'Liquidez_Diaria_Vol': 11465813}
    }
    
    fii_details = {
        'XPLG11': {
            'Descricao': 'XP Log FII investe em ativos logísticos (galpões e centros de distribuição).',
            'Segmento': 'Galpões Logísticos',
            'Taxa_Vacancia': 2.5,
            'Qtd_Imoveis': 18,
            'ABL': 106750,
            'VPA': 107.25,
            'Historico_Dividendos': pd.DataFrame({
                'Data': pd.date_range(end=datetime.now(), periods=12, freq='M'),
                'Valor': [0.82, 0.81, 0.83, 0.80, 0.82, 0.85, 0.83, 0.84, 0.82, 0.81, 0.83, 0.85],
                'DY': [0.82, 0.81, 0.83, 0.80, 0.82, 0.85, 0.83, 0.84, 0.82, 0.81, 0.83, 0.85]
            })
        },
        'HGLG11': {
            'Descricao': 'CSHG Logística FII foca em empreendimentos logísticos e industriais de alto padrão.',
            'Segmento': 'Galpões Logísticos',
            'Taxa_Vacancia': 1.8,
            'Qtd_Imoveis': 28,
            'ABL': 162740,
            'VPA': 163.50,
            'Historico_Dividendos': pd.DataFrame({
                'Data': pd.date_range(end=datetime.now(), periods=12, freq='M'),
                'Valor': [1.10, 1.12, 1.10, 1.15, 1.10, 1.12, 1.10, 1.15, 1.10, 1.12, 1.10, 1.15],
                'DY': [0.69, 0.70, 0.69, 0.72, 0.69, 0.70, 0.69, 0.72, 0.69, 0.70, 0.69, 0.72]
            })
        }
    }
    
    acao_details = {
        'ITUB4': {
            'Descricao': 'Itaú Unibanco Holding S.A. é o maior banco privado do Brasil, oferecendo serviços bancários.',
            'Segmento': 'Bancos',
            'P_L': 8.5,
            'ROE': 18.7,
            'Margem_Liquida': 21.3,
            'Divida_Patrimonio': 0.45,
            'Cresc_Receita': 12.8,
            'Historico_Dividendos': pd.DataFrame({
                'Data': pd.date_range(end=datetime.now(), periods=4, freq='3M'),
                'Valor': [0.50, 0.48, 0.52, 0.55],
                'DY': [1.32, 1.27, 1.38, 1.46]
            })
        },
        'VALE3': {
            'Descricao': 'Vale S.A. é uma das maiores empresas de mineração do mundo, maior produtora de minério de ferro.',
            'Segmento': 'Mineração',
            'P_L': 5.2,
            'ROE': 22.5,
            'Margem_Liquida': 25.8,
            'Divida_Patrimonio': 0.38,
            'Cresc_Receita': -5.3,
            'Historico_Dividendos': pd.DataFrame({
                'Data': pd.date_range(end=datetime.now(), periods=4, freq='3M'),
                'Valor': [0.90, 1.20, 0.85, 1.10],
                'DY': [1.68, 2.25, 1.59, 2.06]
            })
        }
    }
    
    for ticker in tickers:
        if ticker in sample_data:
            market_data[ticker] = sample_data[ticker].copy()
            market_data[ticker]['Erro'] = None
            
            # Adicionar dados detalhados para FIIs
            if ticker in fii_details:
                market_data[ticker].update(fii_details[ticker])
            
            # Adicionar dados detalhados para Ações
            if ticker in acao_details:
                market_data[ticker].update(acao_details[ticker])
                
        else:
            # Para tickers não encontrados no nosso conjunto de dados simulados
            market_data[ticker] = {
                'Preco_Atual': None,
                'Var_Dia_Pct': None,
                'P_VP': None,
                'DY_12M_Pct': None,
                'Liquidez_Diaria_Vol': None,
                'Erro': 'Ticker não encontrado na base de dados simulada'
            }
    
    # Adicionar um pequeno atraso para simular chamada de API
    time.sleep(0.5)
    
    return pd.DataFrame.from_dict(market_data, orient='index')

def calcular_portfolio(df_historico, df_market_data):
    """Calcula métricas do portfólio com base no histórico e dados de mercado."""
    if df_historico.empty:
        return pd.DataFrame(), 0, 0, 0, 0

    # Calcular custo total por transação
    df_historico['Custo_Total_Transacao'] = (
        df_historico['Quantidade'] * df_historico['Preco_Compra_Unitario']
    ) + df_historico['Corretagem_Taxas']

    # Agrupar por ativo para calcular posição consolidada
    portfolio = df_historico.groupby('Codigo_Ativo').agg(
        Quantidade_Total=('Quantidade', 'sum'),
        Custo_Total_Acumulado=('Custo_Total_Transacao', 'sum')
    ).reset_index()

    # Calcular Preço Médio de Compra
    portfolio['Preco_Medio_Compra'] = (
        portfolio['Custo_Total_Acumulado'] / portfolio['Quantidade_Total']
    )

    # Juntar com dados de mercado
    portfolio = portfolio.merge(
        df_market_data[['Preco_Atual', 'Erro']],
        left_on='Codigo_Ativo', right_index=True, how='left'
    )

    # Calcular Valor Atual da Posição e Lucro/Prejuízo
    portfolio['Valor_Atual_Posicao'] = (
        portfolio['Quantidade_Total'] * portfolio['Preco_Atual']
    )
    portfolio['Valor_Atual_Posicao'] = portfolio['Valor_Atual_Posicao'].fillna(0)
    portfolio['Lucro_Prejuizo_Reais'] = (
        portfolio['Valor_Atual_Posicao'] - portfolio['Custo_Total_Acumulado']
    )
    portfolio['Lucro_Prejuizo_Perc'] = portfolio.apply(
        lambda row: (
            row['Lucro_Prejuizo_Reais'] / row['Custo_Total_Acumulado'] * 100
        ) if row['Custo_Total_Acumulado'] != 0 else 0,
        axis=1
    )

    # Calcular totais do portfólio
    total_investido = portfolio['Custo_Total_Acumulado'].sum()
    total_atual = portfolio['Valor_Atual_Posicao'].sum()
    pl_total_reais = total_atual - total_investido
    pl_total_perc = (
        pl_total_reais / total_investido * 100
    ) if total_investido != 0 else 0

    return portfolio, total_investido, total_atual, pl_total_reais, pl_total_perc

# --- Funções de Formatação ---
def format_currency(value):
    return f"R$ {value:,.2f}" if pd.notna(value) else "N/A"

def format_percentage(value):
    return f"{value:,.2f}%" if pd.notna(value) else "N/A"

def format_integer(value):
    return f"{value:,.0f}" if pd.notna(value) else "N/A"

def format_number(value):
    return f"{value:,.2f}" if pd.notna(value) else "N/A"

def criar_cards_info(dados_ativo):
    """Cria cards com informações detalhadas sobre o ativo."""
    tab1, tab2, tab3 = st.tabs(["📋 Informações Gerais", "📊 Métricas Financeiras", "💰 Dividendos"])
    
    with tab1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Sobre")
            st.write(dados_ativo.get('Descricao', 'Informação não disponível'))
        with col2:
            st.subheader("Detalhes")
            st.metric("Setor", dados_ativo.get('Setor', 'N/A'))
            st.metric("Segmento", dados_ativo.get('Segmento', 'N/A'))
            
    with tab2:
        col1, col2, col3 = st.columns(3)
        
        if dados_ativo.get('Tipo_Ativo') == 'FII':
            with col1:
                st.metric("P/VP", format_number(dados_ativo.get('P_VP')))
                st.metric("Taxa de Vacância", format_percentage(dados_ativo.get('Taxa_Vacancia')))
            with col2:
                st.metric("Patrimônio Líquido", format_currency(dados_ativo.get('Patrimonio_Liq')))
                st.metric("Qtd. Imóveis", format_integer(dados_ativo.get('Qtd_Imoveis')))
            with col3:
                st.metric(
                    "Área Bruta Locável",
                    format_integer(dados_ativo.get('ABL')) + " m²"
                    if pd.notna(dados_ativo.get('ABL')) else "N/A"
                )
                st.metric("Valor Patrimonial/Cota", format_currency(dados_ativo.get('VPA')))
        else:  # Ações
            with col1:
                st.metric("P/L", format_number(dados_ativo.get('P_L')))
                st.metric("ROE", format_percentage(dados_ativo.get('ROE')))
            with col2:
                st.metric("Margem Líquida", format_percentage(dados_ativo.get('Margem_Liquida')))
                st.metric("Dívida/Patrimônio", format_number(dados_ativo.get('Divida_Patrimonio')))
            with col3:
                st.metric("Crescimento Receita", format_percentage(dados_ativo.get('Cresc_Receita')))
                st.metric("Liquidez Média Diária", format_currency(dados_ativo.get('Liquidez_Diaria_Vol')))
    
    with tab3:
        if 'Historico_Dividendos' in dados_ativo:
            st.dataframe(
                dados_ativo['Historico_Dividendos'],
                column_config={
                    "Data": st.column_config.DateColumn("Data Pagamento"),
                    "Valor": st.column_config.NumberColumn("Valor (R$)", format="R$ %.2f"),
                    "DY": st.column_config.NumberColumn("Yield (%)", format="%.2f%%")
                },
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Histórico de dividendos não disponível")

def criar_tabela_moderna(df_view):
    """Cria uma tabela moderna com formatação avançada."""
    column_config = {
        "Código": st.column_config.TextColumn(
            "Código",
            help="Código de negociação do ativo"
        ),
        "Tipo": st.column_config.TextColumn(
            "Tipo",
            help="Tipo do ativo (FII ou Ação)"
        ),
        "Setor": st.column_config.TextColumn(
            "Setor",
            help="Setor econômico do ativo"
        ),
        "Preço Atual (R$)": st.column_config.NumberColumn(
            "Preço Atual",
            help="Preço atual de negociação",
            format="R$ %.2f"
        ),
        "Var. Dia (%)": st.column_config.ProgressColumn(
            "Var. Dia",
            help="Variação percentual no dia",
            format="%.2f%%",
            min_value=-5,
            max_value=5
        ),
        "P/VP": st.column_config.NumberColumn(
            "P/VP",
            help="Preço sobre Valor Patrimonial",
            format="%.2f"
        ),
        "DY 12M (%)": st.column_config.NumberColumn(
            "DY 12M",
            help="Dividend Yield dos últimos 12 meses",
            format="%.2f%%"
        ),
        "Previsto Mês Atual (R$)": st.column_config.NumberColumn(
            "Previsto Mês Atual",
            help="Aluguel/Dividendo previsto para o mês atual",
            format="R$ %.2f"
        ),
        "Quant. Carteira": st.column_config.NumberColumn(
            "Quantidade",
            help="Quantidade de cotas/ações em carteira",
            format="%d"
        ),
        "Preço Médio (R$)": st.column_config.NumberColumn(
            "Preço Médio",
            help="Preço médio de compra",
            format="R$ %.2f"
        ),
        "Custo Total (R$)": st.column_config.NumberColumn(
            "Custo Total",
            help="Valor total investido",
            format="R$ %.2f"
        ),
        "Valor Atual (R$)": st.column_config.NumberColumn(
            "Valor Atual",
            help="Valor atual da posição",
            format="R$ %.2f"
        ),
        "L/P (R$)": st.column_config.NumberColumn(
            "Lucro/Prejuízo",
            help="Lucro ou prejuízo em reais",
            format="R$ %.2f"
        ),
        "L/P (%)": st.column_config.ProgressColumn(
            "Retorno",
            help="Retorno percentual da posição",
            format="%.2f%%",
            min_value=-50,
            max_value=50
        ),
        "Volume Dia": st.column_config.NumberColumn(
            "Volume Diário",
            help="Volume financeiro negociado no dia",
            format="%d"
        )
    }
    
    return st.dataframe(
        df_view,
        use_container_width=True,
        hide_index=True,
        column_config=column_config
    )

# --- Interface Principal --- #

# Sidebar
st.sidebar.title("Monitor de Portfólio 📊")

with st.sidebar.expander("📥 Baixar Modelo Excel", expanded=False):
    st.download_button(
        label="Baixar Arquivo de Exemplo",
        data=create_example_excel(),
        file_name="portfolio_monitor_exemplo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Baixe este modelo, preencha com seus dados e faça upload"
    )

st.sidebar.header("📌 Navegação")
pagina_selecionada = st.sidebar.radio(
    "Selecione a Visualização",
    ["📊 Visão Geral", "🔍 Análise Individual"]
)

st.title("Monitor de Portfólio de FIIs e Ações 📊")
st.header("Carregue seu arquivo Excel")
uploaded_file = st.file_uploader(
    "Selecione seu arquivo Excel com as abas 'Historico_Compras' e 'Watchlist'",
    type=['xlsx']
)

if uploaded_file is not None:
    # 1) Carregar dados do Excel
    df_historico, df_watchlist = load_excel_data(uploaded_file)
    
    if df_historico is not None and df_watchlist is not None:
        # --- 2) Busca de Dados da API ---
        tickers_to_fetch = df_watchlist['Codigo_Ativo'].unique().tolist()
        df_market_data = fetch_market_data(tickers_to_fetch)
        
        # --- 3) Cálculo da previsão de pagamento (aluguel/dividendo) ---
        df_previsao = calcular_previsao_mes_atual_market(df_market_data)
        df_market_data = pd.concat([df_market_data, df_previsao], axis=1)
        
        # --- 4) Cálculo do Portfólio ---
        df_portfolio, total_investido, total_atual, pl_total_reais, pl_total_perc = (
            calcular_portfolio(df_historico, df_market_data)
        )

        # --- 5) Filtros na Sidebar ---
        st.sidebar.header("🔎 Filtros")
        with st.sidebar.expander("Filtrar por Tipo", expanded=True):
            tipo_ativo_opts = sorted(df_watchlist['Tipo_Ativo'].unique())
            tipos_selecionados = st.multiselect(
                'Selecione os tipos',
                tipo_ativo_opts,
                default=tipo_ativo_opts
            )
        with st.sidebar.expander("Filtrar por Setor", expanded=True):
            setor_opts = sorted(df_watchlist['Setor'].dropna().unique())
            setores_selecionados = st.multiselect(
                'Selecione os setores',
                setor_opts,
                default=setor_opts
            )
        with st.sidebar.expander("Filtrar por Posse", expanded=True):
            ativos_possessao = df_portfolio['Codigo_Ativo'].unique()
            filtro_posse = st.radio(
                'Mostrar',
                ['Todos da Watchlist', 'Meus Ativos'],
                index=0
            )

        if "🔍 Análise Individual" in pagina_selecionada:
            st.sidebar.header("🎯 Seleção de Ativo")
            ativos_disponiveis = sorted(df_watchlist['Codigo_Ativo'].unique())
            ativo_selecionado = st.sidebar.selectbox(
                'Selecione o Ativo para Análise',
                ativos_disponiveis
            )

        # --- 6) Construir o df_display (Visão Geral) ---
        df_display = df_watchlist.merge(
            df_market_data,
            left_on='Codigo_Ativo',
            right_index=True,
            how='left'
        )
        df_display = df_display.merge(
            df_portfolio[
                [
                    'Codigo_Ativo', 'Quantidade_Total', 'Preco_Medio_Compra',
                    'Custo_Total_Acumulado', 'Valor_Atual_Posicao',
                    'Lucro_Prejuizo_Reais', 'Lucro_Prejuizo_Perc'
                ]
            ],
            on='Codigo_Ativo',
            how='left'
        )

        # Aplicar filtros de posse/tipo/setor
        if filtro_posse == 'Meus Ativos':
            df_display = df_display[df_display['Codigo_Ativo'].isin(ativos_possessao)]
        if tipos_selecionados:
            df_display = df_display[df_display['Tipo_Ativo'].isin(tipos_selecionados)]
        if setores_selecionados:
            if len(setores_selecionados) < len(setor_opts):
                df_display = df_display[df_display['Setor'].isin(setores_selecionados)]

        # --- 7) Conteúdo Principal ---
        if "📊 Visão Geral" in pagina_selecionada:
            st.header("Visão Geral do Portfólio")

            # Cards de resumo
            st.subheader("Resumo do Portfólio")
            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Valor Investido", format_currency(total_investido), delta=None)
                with col2:
                    st.metric("Valor Atual", format_currency(total_atual), delta=None)
                with col3:
                    st.metric(
                        "Lucro/Prejuízo (R$)",
                        format_currency(pl_total_reais),
                        delta=format_currency(pl_total_reais) if pl_total_reais else None,
                        delta_color="normal" if pl_total_reais >= 0 else "inverse"
                    )
                with col4:
                    st.metric(
                        "Lucro/Prejuízo (%)",
                        format_percentage(pl_total_perc),
                        delta=format_percentage(pl_total_perc) if pl_total_perc else None,
                        delta_color="normal" if pl_total_perc >= 0 else "inverse"
                    )

            st.divider()

            st.subheader("Ativos Monitorados")

            # 7.1) Renomear Prev_Pag_Mes_Atual para coluna legível
            df_display = df_display.rename(columns={"Prev_Pag_Mes_Atual": "Previsto Mês Atual (R$)"})

            df_view = df_display[[
                'Codigo_Ativo', 'Tipo_Ativo', 'Setor', 'Preco_Atual',
                'Var_Dia_Pct', 'P_VP', 'DY_12M_Pct', 'Previsto Mês Atual (R$)',
                'Quantidade_Total', 'Preco_Medio_Compra', 'Custo_Total_Acumulado',
                'Valor_Atual_Posicao', 'Lucro_Prejuizo_Reais', 'Lucro_Prejuizo_Perc',
                'Liquidez_Diaria_Vol', 'Erro'
            ]].rename(columns={
                'Codigo_Ativo': 'Código',
                'Tipo_Ativo': 'Tipo',
                'Setor': 'Setor',
                'Preco_Atual': 'Preço Atual (R$)',
                'Var_Dia_Pct': 'Var. Dia (%)',
                'P_VP': 'P/VP',
                'DY_12M_Pct': 'DY 12M (%)',
                'Previsto Mês Atual (R$)': 'Previsto Mês Atual (R$)',
                'Quantidade_Total': 'Quant. Carteira',
                'Preco_Medio_Compra': 'Preço Médio (R$)',
                'Custo_Total_Acumulado': 'Custo Total (R$)',
                'Valor_Atual_Posicao': 'Valor Atual (R$)',
                'Lucro_Prejuizo_Reais': 'L/P (R$)',
                'Lucro_Prejuizo_Perc': 'L/P (%)',
                'Liquidez_Diaria_Vol': 'Volume Dia',
                'Erro': 'Erro API'
            })

            criar_tabela_moderna(df_view)

            with st.expander("Ver Histórico de Compras Completo"):
                st.dataframe(df_historico, use_container_width=True, hide_index=True)

        elif "🔍 Análise Individual" in pagina_selecionada:
            st.header(f"Análise Detalhada: {ativo_selecionado}")

            # Buscar dados do ativo selecionado
            dados_ativo_display = df_display[df_display['Codigo_Ativo'] == ativo_selecionado]
            if dados_ativo_display.empty:
                st.warning(f"Não foram encontrados dados para o ativo {ativo_selecionado}.")
                st.stop()

            dados_ativo = dados_ativo_display.iloc[0]

            st.subheader(f"{dados_ativo.get('Nome_Ativo', ativo_selecionado)} ({ativo_selecionado})")
            st.caption(f"Setor: {dados_ativo.get('Setor', 'N/A')} | Tipo: {dados_ativo.get('Tipo_Ativo', 'N/A')}")

            with st.container():
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Preço Atual", format_currency(dados_ativo.get('Preco_Atual')), delta=None)
                with col2:
                    st.metric(
                        "Var. Dia (%)",
                        format_percentage(dados_ativo.get('Var_Dia_Pct')),
                        delta=format_percentage(dados_ativo.get('Var_Dia_Pct')) if pd.notna(dados_ativo.get('Var_Dia_Pct')) else None,
                        delta_color="normal" if dados_ativo.get('Var_Dia_Pct', 0) >= 0 else "inverse"
                    )
                with col3:
                    st.metric("P/VP", format_number(dados_ativo.get('P_VP')), delta=None)
                with col4:
                    st.metric("DY (12M)", format_percentage(dados_ativo.get('DY_12M_Pct')), delta=None)

            if pd.notna(dados_ativo.get('Erro')):
                st.error(f"Erro ao buscar dados da API: {dados_ativo['Erro']}")

            st.divider()

            # Exibir previsão de pagamento do mês atual
            st.subheader("Previsão de Pagamento (Mês Atual)")
            previsto_atual = dados_ativo.get('Previsto Mês Atual (R$)')
            if pd.notna(previsto_atual):
                st.metric("Previsto Mês Atual", format_currency(previsto_atual))
            else:
                st.info("Não há previsão disponível (sem histórico de dividendos/aluguel).")

            st.divider()

            # Gráfico de histórico de preços
            dados_historicos = gerar_dados_historicos_simulados(
                ativo_selecionado,
                dados_ativo.get('Preco_Atual', 100.0)
            )
            periodos = ['1m', '3m', '6m', '1a', 'YTD']
            periodo_selecionado = st.select_slider(
                "Selecione o período",
                options=periodos,
                value='6m'
            )
            fig = criar_grafico_historico(ativo_selecionado, dados_historicos, periodo_selecionado)
            st.plotly_chart(fig, use_container_width=True)

            st.divider()

            st.subheader("Informações Detalhadas")
            criar_cards_info(dados_ativo)

            st.divider()

            # Posição em carteira
            if ativo_selecionado in ativos_possessao:
                st.subheader("Minha Posição")
                with st.container():
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Quantidade", format_integer(dados_ativo.get('Quantidade_Total')))
                    with col2:
                        st.metric("Preço Médio Compra", format_currency(dados_ativo.get('Preco_Medio_Compra')))
                    with col3:
                        st.metric("Custo Total", format_currency(dados_ativo.get('Custo_Total_Acumulado')))
                    with col4:
                        st.metric("Valor Atual Posição", format_currency(dados_ativo.get('Valor_Atual_Posicao')))

                    col5, col6 = st.columns(2)
                    with col5:
                         st.metric(
                             "Lucro/Prejuízo (R$)", 
                             format_currency(dados_ativo.get('Lucro_Prejuizo_Reais')),
                             delta=format_currency(dados_ativo.get('Lucro_Prejuizo_Reais')) if pd.notna(dados_ativo.get('Lucro_Prejuizo_Reais')) else None,
                             delta_color="normal" if dados_ativo.get('Lucro_Prejuizo_Reais', 0) >= 0 else "inverse"
                         )
                    with col6:
                         st.metric(
                             "Lucro/Prejuízo (%)", 
                             format_percentage(dados_ativo.get('Lucro_Prejuizo_Perc')),
                             delta=format_percentage(dados_ativo.get('Lucro_Prejuizo_Perc')) if pd.notna(dados_ativo.get('Lucro_Prejuizo_Perc')) else None,
                             delta_color="normal" if dados_ativo.get('Lucro_Prejuizo_Perc', 0) >= 0 else "inverse"
                         )

                with st.expander("Ver Histórico de Compras deste Ativo"):
                    st.dataframe(
                        df_historico[df_historico['Codigo_Ativo'] == ativo_selecionado],
                        hide_index=True,
                        use_container_width=True
                    )
            else:
                st.info("Você não possui este ativo em carteira (segundo o histórico de compras).")
    else:
        st.error("Não foi possível carregar os dados do arquivo. Verifique se o formato está correto e tente novamente.")
        st.info("Baixe o arquivo de exemplo para ver o formato esperado.")
else:
    st.info("👆 Faça upload do seu arquivo Excel para começar a monitorar seu portfólio.")
    st.markdown("""
    ### Como usar esta aplicação:
    1. **Prepare seu arquivo Excel** com duas abas:
       - `Historico_Compras`: Registre todas as suas transações de compra
       - `Watchlist`: Liste todos os ativos que deseja monitorar
    2. **Faça upload do arquivo** usando o botão acima
    3. **Explore seu portfólio** usando as visualizações e filtros disponíveis
    """)
    st.markdown("""
    ### Funcionalidades:
    - **Visão Geral**: Tabela com todos os ativos monitorados e resumo do portfólio
    - **Análise Individual**: Detalhes específicos de cada ativo, incluindo gráfico de preços
    - **Filtros**: Filtre por tipo de ativo, setor ou posse
    - **Cálculos Automáticos**: Preço médio, valor atual, lucro/prejuízo
    """)

st.markdown("---")
st.caption(f"Monitor de Portfólio v2.0 | Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.caption("Desenvolvido com Streamlit | Dados de mercado simulados para demonstração")
