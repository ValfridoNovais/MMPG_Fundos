import streamlit as st
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import uuid
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Streamlit app configuration
st.set_page_config(page_title="FII Analysis Dashboard", layout="wide")
st.title("FII Analysis: VRTA11, CPTS11, TVRI11")

# Cache data fetching to improve performance
@st.cache_data
def fetch_price_data(ticker, period="10y", interval="1d"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados de preço para {ticker}: {e}")
        return None

@st.cache_data
def fetch_intraday_data(ticker, interval="15m"):
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period="30d", interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        st.error(f"Erro ao buscar dados intradiários para {ticker}: {e}")
        return None

@st.cache_data
def fetch_dividends(ticker_symbol):
    try:
        url = f"https://statusinvest.com.br/fundos-imobiliarios/{ticker_symbol.lower()}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        dividends = []
        table = soup.find("table", {"id": "earning-section"})
        if table:
            rows = table.find_all("tr")[1:]  # Skip header
            for row in rows:
                cols = row.find_all("td")
                if len(cols) >= 2:
                    date_str = cols[0].text.strip()
                    value_str = cols[1].text.strip().replace("R$", "").replace(",", ".")
                    try:
                        date = pd.to_datetime(date_str, format="%d/%m/%Y")
                        value = float(value_str)
                        dividends.append({"Date": date, "Dividend": value})
                    except:
                        continue
        df = pd.DataFrame(dividends)
        if not df.empty:
            df = df.sort_values("Date")
        return df if not df.empty else None
    except Exception as e:
        st.error(f"Erro ao buscar dados de dividendos para {ticker_symbol}: {e}")
        return None

# Plotting function
def plot_data(df, title, ylabel):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df.index, df["Close" if "Close" in df.columns else "Dividend"], color="blue")
    ax.set_title(title)
    ax.set_xlabel("Date")
    ax.set_ylabel(ylabel)
    ax.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    st.pyplot(fig)

# About information for each FII
def show_about_info():
    st.subheader("Sobre os FIIs")
    st.markdown("""
    **VRTA11 - Votorantim Logística**  
    - **Tipo**: Fundo de Logística  
    - **Descrição**: Investe em galpões logísticos e industriais, com foco em propriedades de alta qualidade em localizações estratégicas no Brasil. Busca gerar renda por meio de aluguéis e valorização patrimonial.  
    - **Gestão**: Votorantim Asset Management  
    - **Público-alvo**: Investidores interessados em renda estável e exposição ao setor logístico.

    **CPTS11 - Capitânia Securities II**  
    - **Tipo**: Fundo de Papel (CRI)  
    - **Descrição**: Investe em Certificados de Recebíveis Imobiliários (CRI), focado em ativos financeiros lastreados por operações imobiliárias. Oferece rendimentos mensais com base em juros de títulos.  
    - **Gestão**: Capitânia Investimentos  
    - **Público-alvo**: Investidores que buscam diversificação em ativos de renda fixa imobiliária.

    **TVRI11 - Tivit Real Estate**  
    - **Tipo**: Fundo Híbrido  
    - **Descrição**: Investe em ativos imobiliários variados, incluindo data centers e propriedades comerciais, com foco em tecnologia e inovação. Combina renda de aluguéis com potencial de ganho de capital.  
    - **Gestão**: Tivit Gestão de Investimentos  
    - **Público-alvo**: Investidores interessados em setores de tecnologia e imóveis comerciais.
    """)

# Sidebar for user input
st.sidebar.header("Opções")
fiis = {
    "VRTA11": "VRTA11.SA",
    "CPTS11": "CPTS11.SA",
    "TVRI11": "TVRI11.SA"
}
selected_fii = st.sidebar.selectbox("Selecione o FII", list(fiis.keys()))
time_frame = st.sidebar.selectbox("Selecione o Período", ["Mensal", "Semanal", "Diário"])
intraday_interval = st.sidebar.selectbox("Selecione o Intervalo Intradiário (Últimos 30 Dias)", ["15m", "30m", "60m"])

# About button
if st.sidebar.button("Sobre"):
    show_about_info()

# Fetch and display price data
st.subheader(f"Análise de Preços para {selected_fii}")
period_map = {"Mensal": "1mo", "Semanal": "1wk", "Diário": "1d"}
df_price = fetch_price_data(fiis[selected_fii], period="10y", interval=period_map[time_frame])
if df_price is not None:
    st.write(f"Dados de Preço {time_frame}")
    plot_data(df_price, f"{selected_fii} Preço {time_frame}", "Preço (BRL)")
    st.dataframe(df_price[["Open", "High", "Low", "Close", "Volume"]].tail())
else:
    st.warning(f"Nenhum dado de preço disponível para {selected_fii}.")

# Fetch and display intraday data
st.subheader(f"Análise Intradiária para {selected_fii} (Últimos 30 Dias)")
df_intraday = fetch_intraday_data(fiis[selected_fii], interval=intraday_interval)
if df_intraday is not None:
    plot_data(df_intraday, f"{selected_fii} Preço {intraday_interval} (Últimos 30 Dias)", "Preço (BRL)")
    st.dataframe(df_intraday[["Open", "High", "Low", "Close", "Volume"]].tail())
else:
    st.warning(f"Nenhum dado intradiário disponível para {selected_fii}.")

# Fetch and display dividend data
st.subheader(f"Análise de Dividendos para {selected_fii}")
df_dividends = fetch_dividends(selected_fii)
if df_dividends is not None:
    st.write("Dividendos Mensais (conforme disponível)")
    plot_data(df_dividends, f"{selected_fii} Dividendos Mensais", "Dividendo por Cota (BRL)")
    st.dataframe(df_dividends.tail())
else:
    st.warning(f"Nenhum dado de dividendos disponível para {selected_fii}.")