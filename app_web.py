import streamlit as st
import pandas as pd
import os
import time
import sys
import io
import tempfile
from datetime import datetime

# --- Configurações da Página ---
st.set_page_config(
    page_title="Monitor de Portfólio",
    page_icon="📊",
    layout="wide"
)

# --- Funções Auxiliares ---
@st.cache_data
def load_excel_data(uploaded_file):
    """Carrega os dados das abas do arquivo Excel enviado pelo usuário."""
    try:
        df_historico = pd.read_excel(uploaded_file, sheet_name='Historico_Compras', parse_dates=['Data_Compra'])
        df_watchlist = pd.read_excel(uploaded_file, sheet_name='Watchlist')
        
        # Garantir que Codigo_Ativo seja string e remover espaços
        df_historico['Codigo_Ativo'] = df_historico['Codigo_Ativo'].astype(str).str.strip()
        df_watchlist['Codigo_Ativo'] = df_watchlist['Codigo_Ativo'].astype(str).str.strip()
        
        # Validar colunas essenciais
        required_hist_cols = ['Data_Compra', 'Codigo_Ativo', 'Tipo_Ativo', 'Quantidade', 'Preco_Compra_Unitario']
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
        'Data_Compra': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2025-01-10']),
        'Codigo_Ativo': ['XPLG11', 'HGLG11', 'ITUB4', 'XPLG11', 'MXRF11'],
        'Tipo_Ativo': ['FII', 'FII', 'Ação', 'FII', 'FII'],
        'Quantidade': [50, 30, 100, 25, 200],
        'Preco_Compra_Unitario': [95.50, 158.20, 28.50, 99.80, 10.15],
        'Corretagem_Taxas': [4.90, 4.90, 4.90, 2.50, 0]
    }
    df_historico = pd.DataFrame(data_historico)
    df_historico['Valor_Total_Compra'] = (df_historico['Quantidade'] * df_historico['Preco_Compra_Unitario']) + df_historico['Corretagem_Taxas']

    data_watchlist = {
        'Codigo_Ativo': ['XPLG11', 'HGLG11', 'ITUB4', 'MXRF11', 'VALE3', 'KNRI11', 'VISC11', 'MALL11', 'CPTS11', 'TVRI11', 'HGRE11', 'VGHF11', 'VRTA11', 'XPML11'],
        'Tipo_Ativo': ['FII', 'FII', 'Ação', 'FII', 'Ação', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII'],
        'Setor': ['Logística', 'Logística', 'Bancário', 'Papel', 'Mineração', 'Misto', 'Shoppings', 'Shoppings', 'Papel', 'Agências de Bancos', 'Lajes Corporativas', 'Misto', 'Papéis', 'Shoppings'],
        'Nome_Ativo': ['XP Log FII', 'CSHG Logística FII', 'Itaú Unibanco Holding SA', 'Maxi Renda FII', 'Vale S.A.', 'Kinea Renda Imobiliária FII', 'Vinci Shopping Centers FII', 'Malls Brasil Plural FII', 'Capitânia Securities II FII', 'Tivio Renda Imobiliária FII', 'CSHG Real Estate FII', 'Valora Hedge Fund FII', 'Votorantim Renda Varejo FII', 'XP Malls FII'],
        'Observacoes': ['Acompanhar vacância', 'Dividendo estável', 'Aguardar balanço', 'FII de Papel popular', 'Volatilidade commodities', 'Bom histórico', '', '', '', '', '', '', '', '']
    }
    df_watchlist = pd.DataFrame(data_watchlist)

    # Criar arquivo Excel em memória
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_historico.to_excel(writer, sheet_name='Historico_Compras', index=False)
        df_watchlist.to_excel(writer, sheet_name='Watchlist', index=False)
    
    return output.getvalue()

# Cache para dados da API (TTL de 15 minutos)
@st.cache_data(ttl=900)
def fetch_market_data(tickers):
    """Simula a busca de dados de mercado para uma lista de tickers."""
    # Em um ambiente de produção, esta função faria chamadas reais à API
    # Para esta versão web, usamos dados simulados para evitar problemas de acesso à API
    
    market_data = {}
    
    # Dados simulados para demonstração
    sample_data = {
        'XPLG11': {'Preco_Atual': 99.70, 'Var_Dia_Pct': 0.41, 'P_VP': 0.93, 'DY_12M_Pct': 10.24, 'Liquidez_Diaria_Vol': 3226098},
        'HGLG11': {'Preco_Atual': 160.23, 'Var_Dia_Pct': 0.14, 'P_VP': 0.98, 'DY_12M_Pct': 8.79, 'Liquidez_Diaria_Vol': 5714559},
        'ITUB4': {'Preco_Atual': 37.79, 'Var_Dia_Pct': 0.69, 'P_VP': 1.25, 'DY_12M_Pct': 5.32, 'Liquidez_Diaria_Vol': 15000000},
        'MXRF11': {'Preco_Atual': 9.52, 'Var_Dia_Pct': 0.53, 'P_VP': 0.85, 'DY_12M_Pct': 13.25, 'Liquidez_Diaria_Vol': 8125365},
        'VALE3': {'Preco_Atual': 53.41, 'Var_Dia_Pct': -2.25, 'P_VP': 1.15, 'DY_12M_Pct': 6.75, 'Liquidez_Diaria_Vol': 25000000},
        'KNRI11': {'Preco_Atual': 145.70, 'Var_Dia_Pct': 0.48, 'P_VP': 0.90, 'DY_12M_Pct': 8.80, 'Liquidez_Diaria_Vol': 6478154},
        'VISC11': {'Preco_Atual': 103.30, 'Var_Dia_Pct': -0.54, 'P_VP': 0.84, 'DY_12M_Pct': 9.84, 'Liquidez_Diaria_Vol': 3852021},
        'MALL11': {'Preco_Atual': 101.40, 'Var_Dia_Pct': -0.59, 'P_VP': 0.84, 'DY_12M_Pct': 10.03, 'Liquidez_Diaria_Vol': 3082284},
        'CPTS11': {'Preco_Atual': 7.36, 'Var_Dia_Pct': -0.94, 'P_VP': 0.85, 'DY_12M_Pct': 13.25, 'Liquidez_Diaria_Vol': 8125365},
        'TVRI11': {'Preco_Atual': 91.62, 'Var_Dia_Pct': 0.35, 'P_VP': 0.90, 'DY_12M_Pct': 13.59, 'Liquidez_Diaria_Vol': 1033718},
        'HGRE11': {'Preco_Atual': 113.60, 'Var_Dia_Pct': 1.21, 'P_VP': 0.74, 'DY_12M_Pct': 9.94, 'Liquidez_Diaria_Vol': 1648659},
        'VGHF11': {'Preco_Atual': 7.75, 'Var_Dia_Pct': 0.39, 'P_VP': 0.91, 'DY_12M_Pct': 14.27, 'Liquidez_Diaria_Vol': 2954165},
        'VRTA11': {'Preco_Atual': 81.55, 'Var_Dia_Pct': -0.60, 'P_VP': 0.92, 'DY_12M_Pct': 12.92, 'Liquidez_Diaria_Vol': 1449132},
        'XPML11': {'Preco_Atual': 104.34, 'Var_Dia_Pct': 0.14, 'P_VP': 0.89, 'DY_12M_Pct': 11.07, 'Liquidez_Diaria_Vol': 11465813}
    }
    
    for ticker in tickers:
        if ticker in sample_data:
            market_data[ticker] = sample_data[ticker]
            market_data[ticker]['Erro'] = None
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
    df_historico['Custo_Total_Transacao'] = (df_historico['Quantidade'] * df_historico['Preco_Compra_Unitario']) + df_historico['Corretagem_Taxas']

    # Agrupar por ativo para calcular posição consolidada
    portfolio = df_historico.groupby('Codigo_Ativo').agg(
        Quantidade_Total=('Quantidade', 'sum'),
        Custo_Total_Acumulado=('Custo_Total_Transacao', 'sum')
    ).reset_index()

    # Calcular Preço Médio de Compra
    portfolio['Preco_Medio_Compra'] = portfolio['Custo_Total_Acumulado'] / portfolio['Quantidade_Total']

    # Juntar com dados de mercado
    portfolio = portfolio.merge(df_market_data[['Preco_Atual', 'Erro']], left_on='Codigo_Ativo', right_index=True, how='left')

    # Calcular Valor Atual da Posição e Lucro/Prejuízo
    portfolio['Valor_Atual_Posicao'] = portfolio['Quantidade_Total'] * portfolio['Preco_Atual']
    # Tratar casos onde o preço atual não foi encontrado
    portfolio['Valor_Atual_Posicao'] = portfolio['Valor_Atual_Posicao'].fillna(0)
    portfolio['Lucro_Prejuizo_Reais'] = portfolio['Valor_Atual_Posicao'] - portfolio['Custo_Total_Acumulado']
    # Evitar divisão por zero no cálculo percentual
    portfolio['Lucro_Prejuizo_Perc'] = portfolio.apply(
        lambda row: (row['Lucro_Prejuizo_Reais'] / row['Custo_Total_Acumulado'] * 100) if row['Custo_Total_Acumulado'] != 0 else 0,
        axis=1
    )

    # Calcular totais do portfólio
    total_investido = portfolio['Custo_Total_Acumulado'].sum()
    total_atual = portfolio['Valor_Atual_Posicao'].sum()
    pl_total_reais = total_atual - total_investido
    pl_total_perc = (pl_total_reais / total_investido * 100) if total_investido != 0 else 0

    return portfolio, total_investido, total_atual, pl_total_reais, pl_total_perc

# --- Funções de Formatação ---
def format_currency(value):
    return f"R$ {value:,.2f}" if pd.notna(value) else "N/A"

def format_percentage(value):
    return f"{value:,.2f}%" if pd.notna(value) else "N/A"

def format_integer(value):
     return f"{value:,.0f}" if pd.notna(value) else "N/A"

# --- Interface Principal ---
st.title("Monitor de Portfólio de FIIs e Ações 📊")

# Seção de upload de arquivo
st.header("Carregue seu arquivo Excel")

# Criar duas colunas para upload e download de exemplo
col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("Selecione seu arquivo Excel com as abas 'Historico_Compras' e 'Watchlist'", type=['xlsx'])

with col2:
    st.write("Não tem um arquivo no formato correto? Baixe nosso modelo:")
    example_file = create_example_excel()
    st.download_button(
        label="📥 Baixar Arquivo de Exemplo",
        data=example_file,
        file_name="portfolio_monitor_exemplo.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    st.caption("Preencha com seus dados e faça upload para usar o monitor.")

# Verificar se o arquivo foi carregado
if uploaded_file is not None:
    # Carregar dados do Excel
    df_historico, df_watchlist = load_excel_data(uploaded_file)
    
    if df_historico is not None and df_watchlist is not None:
        # --- Busca de Dados da API ---
        tickers_to_fetch = df_watchlist['Codigo_Ativo'].unique().tolist()
        df_market_data = fetch_market_data(tickers_to_fetch)

        # --- Cálculo do Portfólio ---
        df_portfolio, total_investido, total_atual, pl_total_reais, pl_total_perc = calcular_portfolio(df_historico, df_market_data)

        # --- Sidebar ---
        st.sidebar.title("Navegação e Filtros")

        st.sidebar.header("Navegação")
        pagina_selecionada = st.sidebar.radio("Selecione a Visualização", ['Visão Geral', 'Análise Individual'])

        st.sidebar.header("Filtros (Visão Geral)")
        tipo_ativo_opts = sorted(df_watchlist['Tipo_Ativo'].unique())
        tipos_selecionados = st.sidebar.multiselect('Filtrar por Tipo', tipo_ativo_opts, default=tipo_ativo_opts)

        setor_opts = sorted(df_watchlist['Setor'].dropna().unique())
        setores_selecionados = st.sidebar.multiselect('Filtrar por Setor', setor_opts, default=setor_opts)

        ativos_possessao = df_portfolio['Codigo_Ativo'].unique()
        filtro_posse = st.sidebar.radio('Filtrar por Posse', ['Todos da Watchlist', 'Meus Ativos'], index=0)

        st.sidebar.header("Seleção (Análise Individual)")
        ativos_disponiveis = sorted(df_watchlist['Codigo_Ativo'].unique())
        ativo_selecionado = st.sidebar.selectbox('Selecione o Ativo para Análise', ativos_disponiveis)

        # --- Lógica de Filtragem (Visão Geral) ---
        df_display = df_watchlist.merge(df_market_data, left_on='Codigo_Ativo', right_index=True, how='left')
        df_display = df_display.merge(df_portfolio[['Codigo_Ativo', 'Quantidade_Total', 'Preco_Medio_Compra', 'Custo_Total_Acumulado', 'Valor_Atual_Posicao', 'Lucro_Prejuizo_Reais', 'Lucro_Prejuizo_Perc']], on='Codigo_Ativo', how='left')

        # Aplicar filtros da sidebar
        if filtro_posse == 'Meus Ativos':
            df_display = df_display[df_display['Codigo_Ativo'].isin(ativos_possessao)]

        if tipos_selecionados:
            df_display = df_display[df_display['Tipo_Ativo'].isin(tipos_selecionados)]

        if setores_selecionados:
            # Incluir NaN ou vazios se nenhum setor for selecionado, ou filtrar se houver seleção
            if len(setores_selecionados) < len(setor_opts):
                 df_display = df_display[df_display['Setor'].isin(setores_selecionados)]

        # --- Conteúdo Principal ---
        if pagina_selecionada == 'Visão Geral':
            st.header("Visão Geral do Portfólio")

            st.subheader("Resumo do Portfólio")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Valor Investido", format_currency(total_investido))
            with col2:
                st.metric("Valor Atual", format_currency(total_atual))
            with col3:
                st.metric("Lucro/Prejuízo (R$)", format_currency(pl_total_reais))
            with col4:
                st.metric("Lucro/Prejuízo (%)", format_percentage(pl_total_perc))

            st.divider()

            st.subheader("Ativos Monitorados")

            # Selecionar e renomear colunas para exibição
            df_view = df_display[[
                'Codigo_Ativo', 'Tipo_Ativo', 'Setor', 'Preco_Atual', 'Var_Dia_Pct', 'P_VP', 'DY_12M_Pct',
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
                'Quantidade_Total': 'Quant. Carteira',
                'Preco_Medio_Compra': 'Preço Médio (R$)',
                'Custo_Total_Acumulado': 'Custo Total (R$)',
                'Valor_Atual_Posicao': 'Valor Atual (R$)',
                'Lucro_Prejuizo_Reais': 'L/P (R$)',
                'Lucro_Prejuizo_Perc': 'L/P (%)',
                'Liquidez_Diaria_Vol': 'Volume Dia',
                'Erro': 'Erro API'
            })

            # Formatar colunas numéricas
            column_config = {
                "Preço Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Var. Dia (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "P/VP": st.column_config.NumberColumn(format="%.2f"),
                "DY 12M (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Quant. Carteira": st.column_config.NumberColumn(format="%d"),
                "Preço Médio (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Custo Total (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Valor Atual (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "L/P (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "L/P (%)": st.column_config.NumberColumn(format="%.2f%%"),
                "Volume Dia": st.column_config.NumberColumn(format="%d"),
            }

            # Exibir dataframe com formatação
            st.dataframe(df_view, use_container_width=True, hide_index=True, column_config=column_config)

            # Opcional: Exibir histórico de compras
            with st.expander("Ver Histórico de Compras Completo"):
                st.dataframe(df_historico, use_container_width=True, hide_index=True)

        elif pagina_selecionada == 'Análise Individual':
            st.header(f"Análise Detalhada: {ativo_selecionado}")

            # Buscar dados do ativo selecionado (já mergeados)
            dados_ativo_display = df_display[df_display['Codigo_Ativo'] == ativo_selecionado]

            if dados_ativo_display.empty:
                st.warning(f"Não foram encontrados dados para o ativo {ativo_selecionado}.")
                st.stop()

            dados_ativo = dados_ativo_display.iloc[0]

            # Cabeçalho
            st.subheader(f"{dados_ativo.get('Nome_Ativo', ativo_selecionado)} ({ativo_selecionado})")
            st.caption(f"Setor: {dados_ativo.get('Setor', 'N/A')} | Tipo: {dados_ativo.get('Tipo_Ativo', 'N/A')}")

            st.divider()

            st.subheader("Indicadores Chave")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Preço Atual", format_currency(dados_ativo.get('Preco_Atual')))
            with col2:
                st.metric("Var. Dia (%)", format_percentage(dados_ativo.get('Var_Dia_Pct')))
            with col3:
                st.metric("P/VP", format_percentage(dados_ativo.get('P_VP')))
            with col4:
                st.metric("DY (12M)", format_percentage(dados_ativo.get('DY_12M_Pct')))

            # Exibir erro da API se houver
            if pd.notna(dados_ativo.get('Erro')):
                st.error(f"Erro ao buscar dados da API: {dados_ativo['Erro']}")

            st.divider()

            # Posição em carteira
            if ativo_selecionado in ativos_possessao:
                st.subheader("Minha Posição")
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
                     st.metric("Lucro/Prejuízo (R$)", format_currency(dados_ativo.get('Lucro_Prejuizo_Reais')))
                with col6:
                     st.metric("Lucro/Prejuízo (%)", format_percentage(dados_ativo.get('Lucro_Prejuizo_Perc')))

                # Mostrar histórico específico do ativo
                with st.expander("Ver Histórico de Compras deste Ativo"):
                    st.dataframe(df_historico[df_historico['Codigo_Ativo'] == ativo_selecionado], hide_index=True, use_container_width=True)
            else:
                st.info("Você não possui este ativo em carteira (segundo o histórico de compras).")

            st.divider()

            # Informações adicionais
            st.subheader("Informações Adicionais")
            st.write(f"**Volume Diário:** {format_integer(dados_ativo.get('Liquidez_Diaria_Vol'))}")
            
            st.subheader("Observações")
            st.write(dados_ativo.get('Observacoes', ''))

    else:
        st.error("Não foi possível carregar os dados do arquivo. Verifique se o formato está correto e tente novamente.")
        st.info("Baixe o arquivo de exemplo para ver o formato esperado.")

else:
    # Mostrar informações iniciais quando nenhum arquivo foi carregado
    st.info("👆 Faça upload do seu arquivo Excel para começar a monitorar seu portfólio.")
    
    st.markdown("""
    ### Como usar esta aplicação:
    
    1. **Prepare seu arquivo Excel** com duas abas:
       - `Historico_Compras`: Registre todas as suas transações de compra
       - `Watchlist`: Liste todos os ativos que deseja monitorar
       
    2. **Faça upload do arquivo** usando o botão acima
    
    3. **Explore seu portfólio** usando as visualizações e filtros disponíveis
    
    Não tem um arquivo pronto? Baixe nosso modelo de exemplo, preencha com seus dados e faça upload.
    """)
    
    st.markdown("""
    ### Funcionalidades:
    
    - **Visão Geral**: Tabela com todos os ativos monitorados e resumo do portfólio
    - **Análise Individual**: Detalhes específicos de cada ativo
    - **Filtros**: Filtre por tipo de ativo, setor ou posse
    - **Cálculos Automáticos**: Preço médio, valor atual, lucro/prejuízo
    """)

# Rodapé com informações
st.markdown("---")
st.caption(f"Monitor de Portfólio v1.0 | Dados atualizados em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
st.caption("Desenvolvido com Streamlit | Dados de mercado simulados para demonstração")
