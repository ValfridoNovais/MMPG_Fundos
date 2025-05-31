# Dados Extraídos da Imagem e Requisitos

## Colunas Identificadas na Imagem:

*   Fundos (Ticker do Ativo)
*   Setor
*   Preço Atual (R$)
*   Liquidez Diária (R$)
*   P/VP (Preço sobre Valor Patrimonial)
*   DY (12M) Acumulado (Dividend Yield acumulado nos últimos 12 meses)
*   Patrimônio Líquido
*   VPA (Valor Patrimonial por Ação/Cota)
*   Quant. Ativos (Quantidade de ativos subjacentes)
*   Último Dividendo
*   (Coluna adicional de Dividend Yield do último dividendo - a ser confirmada)

## Tickers de Exemplo (FIIs):

*   TVRI11
*   XPLG11
*   HGLG11
*   HGRE11
*   VGHF11
*   KNRI11
*   VRTA11
*   CPTS11
*   MALL11
*   XPML11
*   VISC11

## Requisitos da Aplicação:

*   Plataforma: Python com Streamlit.
*   Funcionalidade Principal: Monitoramento de FIIs e outros ativos (ações).
*   Visualização Principal: Tabela com dados similares aos da imagem.
*   Entrada de Dados (Histórico): Arquivo `.xlsx` com abas para:
    *   Histórico de Compras: Data, Código, Quantidade, Preço Compra.
    *   Lista de Interesse (Watchlist): Códigos dos ativos (inclui os comprados).
*   Visualizações Adicionais: Páginas/seções individuais para cada ativo no portfólio/watchlist.
*   Interface:
    *   Sidebar para navegação entre visualizações (Geral, Individual) e filtros.
    *   Filtros (Ex: por Setor, por Tipo - FII/Ação).
    *   Design: Moderno e discreto.
*   Dados de Mercado: Busca automática de dados atualizados (Preço, DY, P/VP, etc.) via API.
*   Pesquisa: Levantar melhores práticas e métricas para análise de FIIs e ações no Brasil.

