# Estrutura do Arquivo Excel (`portfolio_monitor.xlsx`)

Este documento descreve a estrutura proposta para o arquivo Excel que será utilizado como base de dados para a aplicação Streamlit de monitoramento de portfólio.

O arquivo conterá duas abas principais:

1.  **Historico_Compras**: Para registrar manualmente todas as transações de compra de ativos (FIIs e Ações).
2.  **Watchlist**: Para listar todos os ativos que o usuário deseja monitorar, incluindo aqueles que já possui em carteira e outros de interesse.

## Aba: `Historico_Compras`

Esta aba armazenará o histórico detalhado de cada operação de compra realizada pelo usuário.

**Colunas:**

*   `Data_Compra` (Formato: Data - Ex: DD/MM/AAAA): Registra a data exata em que a compra do ativo foi efetuada.
*   `Codigo_Ativo` (Formato: Texto - Ex: XPLG11, ITUB4): Contém o código de negociação (ticker) do Fundo Imobiliário ou Ação adquirido.
*   `Tipo_Ativo` (Formato: Texto - Ex: FII, Ação): Especifica o tipo do ativo comprado, facilitando filtros e análises posteriores.
*   `Quantidade` (Formato: Número - Ex: 100): Indica o número de cotas (para FIIs) ou ações compradas na transação.
*   `Preco_Compra_Unitario` (Formato: Número/Moeda - Ex: 98.50): Registra o preço pago por cada cota ou ação no momento da compra, sem incluir taxas.
*   `Corretagem_Taxas` (Formato: Número/Moeda - Ex: 4.90 - Opcional): Campo opcional para registrar os custos de corretagem e taxas associados à transação específica. Ajuda a calcular o custo médio de aquisição de forma mais precisa.
*   `Valor_Total_Compra` (Formato: Número/Moeda - Calculado ou Manual - Ex: 9854.90): Representa o valor total desembolsado na operação (`Quantidade` * `Preco_Compra_Unitario` + `Corretagem_Taxas`). Pode ser preenchido manualmente ou calculado via fórmula no Excel.

## Aba: `Watchlist`

Esta aba serve como um catálogo central de todos os ativos que o usuário tem interesse em acompanhar, sejam eles parte do portfólio atual ou apenas alvos de estudo.
A aplicação utilizará os códigos desta lista para buscar dados de mercado atualizados.

**Colunas:**

*   `Codigo_Ativo` (Formato: Texto - Ex: HGLG11, VALE3): O código de negociação (ticker) do ativo a ser monitorado. Esta coluna é a chave principal para a busca de dados.
*   `Tipo_Ativo` (Formato: Texto - Ex: FII, Ação): Indica se o ativo é um Fundo Imobiliário ou uma Ação.
*   `Setor` (Formato: Texto - Ex: Logística, Mineração, Bancário - Opcional): Campo opcional, mas recomendado, para classificar o ativo por seu setor de atuação. Útil para filtros e análise de diversificação. Pode ser preenchido manualmente.
*   `Nome_Ativo` (Formato: Texto - Ex: CSHG Logística FII, Vale S.A. - Opcional): O nome completo do fundo ou da empresa, para referência.
*   `Observacoes` (Formato: Texto - Opcional): Espaço para o usuário adicionar notas pessoais, metas de preço, ou qualquer outra informação relevante sobre o ativo.

**Observação Importante:** Todos os `Codigo_Ativo` presentes na aba `Historico_Compras` devem obrigatoriamente constar também na aba `Watchlist` para que seus dados de mercado sejam buscados e exibidos pela aplicação.

