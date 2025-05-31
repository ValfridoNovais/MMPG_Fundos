#!/usr/bin/env python
# coding: utf-8

import sys
sys.path.append('/opt/.manus/.sandbox-runtime')
from data_api import ApiClient
import pandas as pd
import time
import json # Import json for potential debugging

# Initialize API client
client = ApiClient()

# List of tickers from the watchlist (add .SA suffix for B3)
tickers_br = [
    'XPLG11.SA', 'HGLG11.SA', 'ITUB4.SA', 'MXRF11.SA', 'VALE3.SA',
    'KNRI11.SA', 'VISC11.SA', 'MALL11.SA', 'CPTS11.SA', 'TVRI11.SA',
    'HGRE11.SA', 'VGHF11.SA', 'VRTA11.SA', 'XPML11.SA'
]

def fetch_market_data(tickers):
    """Fetches market data for a list of tickers using YahooFinance API."""
    market_data = {}
    print(f"Fetching data for: {tickers}")
    for ticker in tickers:
        ticker_key = ticker.replace('.SA', '') # Key for the dictionary
        try:
            print(f"Fetching {ticker}...")
            api_response = client.call_api('YahooFinance/get_stock_chart',
                                           query={'symbol': ticker,
                                                  'region': 'BR',
                                                  'interval': '1d',
                                                  'range': '5d', # Get last few days
                                                  'includePrePost': False,
                                                  'includeAdjustedClose': False})

            # Check for errors in response
            chart_data = api_response.get('chart', {})
            if chart_data.get('error'):
                error_message = chart_data['error']
                print(f"API Error for {ticker}: {error_message}")
                market_data[ticker_key] = {'Preco_Atual': None, 'Erro': str(error_message)}
                continue

            result = chart_data.get('result', [])
            if not result or not result[0].get('meta'):
                print(f"No data/meta found for {ticker} in response: {json.dumps(api_response)}")
                market_data[ticker_key] = {'Preco_Atual': None, 'Erro': 'No data/meta found'}
                continue

            meta = result[0]['meta']
            indicators = result[0].get('indicators', {}).get('quote', [{}])[0]
            timestamps = result[0].get('timestamp', [])

            # Get the latest regular market price from meta
            current_price = meta.get('regularMarketPrice')
            previous_close = meta.get('chartPreviousClose')
            daily_change_pct = None
            if current_price is not None and previous_close is not None and previous_close != 0:
                 daily_change_pct = ((current_price / previous_close) - 1) * 100

            # Fallback: get the last closing price from indicators if meta price is missing
            if current_price is None and 'close' in indicators and indicators['close']:
                last_valid_close = next((price for price in reversed(indicators['close']) if price is not None), None)
                current_price = last_valid_close
                # Cannot calculate daily change accurately without current market price vs previous close
                daily_change_pct = None # Or calculate based on last two closes if needed

            # Store data
            market_data[ticker_key] = {
                'Preco_Atual': current_price,
                'Var_Dia_Pct': daily_change_pct,
                # Add placeholders for other data points
                'P_VP': None,
                'DY_12M_Pct': None,
                'Ult_Dividendo': None,
                'Data_Ult_Div': None,
                'Liquidez_Diaria': meta.get('regularMarketVolume'), # Using volume as proxy for now
                'Patrimonio_Liq': None,
                'VPA': None,
                'Erro': None # Explicitly set error to None on success
            }
            print(f"Success for {ticker}: Price={current_price}")

        except Exception as e:
            print(f"Error processing data for {ticker}: {e}")
            # Ensure the key exists even if an exception occurs during processing
            if ticker_key not in market_data:
                 market_data[ticker_key] = {'Preco_Atual': None, 'Erro': str(e)}
            else:
                 # If data was partially fetched before error, update the error field
                 market_data[ticker_key]['Erro'] = str(e)

        # Add a small delay to avoid hitting API rate limits, if any
        time.sleep(0.5)

    return market_data

# --- Main execution for testing ---
if __name__ == '__main__':
    print("Testing API data fetch...")
    fetched_data = fetch_market_data(tickers_br)
    print("\n--- Fetched Data ---")
    # Use json dumps for potentially cleaner dictionary printing
    print(json.dumps(fetched_data, indent=4))

    # Convert to DataFrame for better visualization
    df_fetched = pd.DataFrame.from_dict(fetched_data, orient='index')
    print("\n--- DataFrame ---")
    print(df_fetched)

