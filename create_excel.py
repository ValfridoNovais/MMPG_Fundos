import pandas as pd

# Criar dados de exemplo para a aba Historico_Compras
data_historico = {
    'Data_Compra': pd.to_datetime(['2024-01-15', '2024-02-20', '2024-03-10', '2024-04-05', '2025-01-10']), # Usar formato YYYY-MM-DD para pandas
    'Codigo_Ativo': ['XPLG11', 'HGLG11', 'ITUB4', 'XPLG11', 'MXRF11'],
    'Tipo_Ativo': ['FII', 'FII', 'Ação', 'FII', 'FII'],
    'Quantidade': [50, 30, 100, 25, 200],
    'Preco_Compra_Unitario': [95.50, 158.20, 28.50, 99.80, 10.15],
    'Corretagem_Taxas': [4.90, 4.90, 4.90, 2.50, 0],
    # 'Valor_Total_Compra' pode ser calculado depois ou deixado para o Excel/Streamlit
}
df_historico = pd.DataFrame(data_historico)
# Calcular Valor_Total_Compra
df_historico['Valor_Total_Compra'] = (df_historico['Quantidade'] * df_historico['Preco_Compra_Unitario']) + df_historico['Corretagem_Taxas']

# Criar dados de exemplo para a aba Watchlist
data_watchlist = {
    'Codigo_Ativo': ['XPLG11', 'HGLG11', 'ITUB4', 'MXRF11', 'VALE3', 'KNRI11', 'VISC11', 'MALL11', 'CPTS11', 'TVRI11', 'HGRE11', 'VGHF11', 'VRTA11', 'XPML11'],
    'Tipo_Ativo': ['FII', 'FII', 'Ação', 'FII', 'Ação', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII', 'FII'],
    'Setor': ['Logística', 'Logística', 'Bancário', 'Papel', 'Mineração', 'Misto', 'Shoppings', 'Shoppings', 'Papel', 'Agências de Bancos', 'Lajes Corporativas', 'Misto', 'Papéis', 'Shoppings'],
    'Nome_Ativo': ['XP Log FII', 'CSHG Logística FII', 'Itaú Unibanco Holding SA', 'Maxi Renda FII', 'Vale S.A.', 'Kinea Renda Imobiliária FII', 'Vinci Shopping Centers FII', 'Malls Brasil Plural FII', 'Capitânia Securities II FII', 'Tivio Renda Imobiliária FII', 'CSHG Real Estate FII', 'Valora Hedge Fund FII', 'Votorantim Renda Varejo FII', 'XP Malls FII'],
    'Observacoes': ['Acompanhar vacância', 'Dividendo estável', 'Aguardar balanço', 'FII de Papel popular', 'Volatilidade commodities', 'Bom histórico', '', '', '', '', '', '', '', '']
}
df_watchlist = pd.DataFrame(data_watchlist)

# Criar o arquivo Excel
excel_file_path = '/home/ubuntu/portfolio_monitor.xlsx'
with pd.ExcelWriter(excel_file_path, engine='openpyxl', date_format='DD/MM/YYYY', datetime_format='DD/MM/YYYY') as writer:
    df_historico.to_excel(writer, sheet_name='Historico_Compras', index=False)
    df_watchlist.to_excel(writer, sheet_name='Watchlist', index=False)

print(f"Arquivo Excel '{excel_file_path}' criado com sucesso.")

