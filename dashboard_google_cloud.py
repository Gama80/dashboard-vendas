
import streamlit as st
import pandas as pd
import plotly.express as px

# Carregar dados diretamente do Google Drive
url = "https://drive.google.com/uc?id=14oLRF6uwVLL-vsDBc2LS03YLdrnMH_w8&export=download"
df = pd.read_csv(url, encoding='latin1', sep=';')
df.columns = df.columns.str.strip()  # remove espaços em branco nos nomes


# Pré-processamento
df = df[df['VENDEDOR'].notna()]
df['DATAPREVENDA'] = pd.to_datetime(df['DATAPREVENDA'], errors='coerce', dayfirst=True)
df = df[df['DATAPREVENDA'].notna()]
df['DATA_BR'] = df['DATAPREVENDA'].dt.strftime('%d/%m/%Y')

# Conversão de valores
df['PRECOVENDA'] = pd.to_numeric(df['PRECOVENDA'], errors='coerce')
df['VALORFRETE'] = df['VALORFRETE'].replace({ 'R\$ ': '', ',': '.' }, regex=True)
df['VALORFRETE'] = pd.to_numeric(df['VALORFRETE'], errors='coerce').fillna(0)

# Filtros
st.sidebar.title("Filtros")
data_inicial = st.sidebar.date_input("Data Inicial", df['DATAPREVENDA'].min())
data_final = st.sidebar.date_input("Data Final", df['DATAPREVENDA'].max())
ufs = st.sidebar.multiselect("Estado (UF)", df['ENDUF1'].dropna().unique(), default=df['ENDUF1'].dropna().unique())
tipo_pessoa = st.sidebar.multiselect("Tipo de Pessoa", df['Tipo de Pessoa'].dropna().unique(), default=df['Tipo de Pessoa'].dropna().unique())

df_filtrado = df[
    (df['DATAPREVENDA'] >= pd.to_datetime(data_inicial)) &
    (df['DATAPREVENDA'] <= pd.to_datetime(data_final)) &
    (df['ENDUF1'].isin(ufs)) &
    (df['Tipo de Pessoa'].isin(tipo_pessoa)) &
    (~df['DSCFORMAPAG_PRINCIPAL'].str.contains("LIVRE DÉBITO", na=False))
]

# KPIs
total_pedidos = df_filtrado.shape[0]
total_faturado = df_filtrado['PRECOVENDA'].sum()
total_frete = df_filtrado['VALORFRETE'].sum()
clientes_unicos = df_filtrado['RAZAOSOCIAL_NOME'].nunique()

st.title("Painel de Vendas (Google Sheets + Streamlit Cloud)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Pedidos", f"{total_pedidos}")
col2.metric("Valor Faturado", f"R$ {total_faturado:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Frete Total", f"R$ {total_frete:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Clientes Únicos", f"{clientes_unicos}")

# Faturamento por Vendedor
st.subheader("Faturamento por Vendedor")
vendedores = df_filtrado.groupby('VENDEDOR')['PRECOVENDA'].sum().reset_index().sort_values(by='PRECOVENDA', ascending=False)
fig1 = px.bar(vendedores, x='VENDEDOR', y='PRECOVENDA', labels={'PRECOVENDA': 'R$'})
st.plotly_chart(fig1)

# Formas de Pagamento
st.subheader("Formas de Pagamento")
formas = df_filtrado['DSCFORMAPAG_PRINCIPAL'].value_counts().reset_index()
formas.columns = ['Forma de Pagamento', 'Qtd']
fig2 = px.pie(formas, names='Forma de Pagamento', values='Qtd', hole=0.4)
st.plotly_chart(fig2)

# Faturamento por UF
st.subheader("Faturamento por Estado")
ufs = df_filtrado.groupby('ENDUF1')['PRECOVENDA'].sum().reset_index().sort_values(by='PRECOVENDA', ascending=False)
fig3 = px.bar(ufs, x='ENDUF1', y='PRECOVENDA', labels={'PRECOVENDA': 'R$'})
st.plotly_chart(fig3)

# Ranking de Clientes
st.subheader("Top 10 Clientes")
clientes = df_filtrado.groupby('RAZAOSOCIAL_NOME').agg({
    'PRECOVENDA': 'sum',
    'VALORFRETE': 'sum',
    'RAZAOSOCIAL_NOME': 'count'
}).rename(columns={'RAZAOSOCIAL_NOME': 'QtdPedidos'}).sort_values(by='PRECOVENDA', ascending=False).reset_index()
st.dataframe(clientes.head(10))
