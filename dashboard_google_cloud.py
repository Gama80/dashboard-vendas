
import streamlit as st
import pandas as pd
import plotly.express as px

# === Acesso simples com uma senha ===
st.set_page_config(page_title="Painel de Vendas", layout="wide")

senha = st.sidebar.text_input("🔒 Digite a senha para acessar:", type="password")
if senha != "telas3231":
    st.warning("Acesso negado. Informe a senha correta.")
    st.stop()
st.success("Acesso liberado ✅")

# === Carregar dados do Google Drive (URL corrigida) ===
url = "https://drive.google.com/uc?id=14oLRF6uwVLL-vsDBC2LS83YLdrnMH_w8&export=download"
df = pd.read_csv(url, encoding='latin1', sep=';')
df.columns = df.columns.str.strip()

# === Tratamento dos dados ===
df = df[df['VENDEDOR'].notna()]
df['DATAPREVENDA'] = pd.to_datetime(df['DATAPREVENDA'], errors='coerce', dayfirst=True)
df = df[df['DATAPREVENDA'].notna()]
df['DATA_BR'] = df['DATAPREVENDA'].dt.strftime('%d/%m/%Y')

df['PRECOVENDA'] = pd.to_numeric(df['PRECOVENDA'].astype(str).str.replace('R$','').str.replace('.', '').str.replace(',', '.'), errors='coerce')
df['VALORFRETE'] = pd.to_numeric(df['VALORFRETE'].astype(str).str.replace('R$','').str.replace('.', '').str.replace(',', '.'), errors='coerce')

# === Filtros ===
st.sidebar.header("Filtros")
data_inicial = st.sidebar.date_input("Data Inicial", df['DATAPREVENDA'].min())
data_final = st.sidebar.date_input("Data Final", df['DATAPREVENDA'].max())
ufs = st.sidebar.multiselect("Estados (UF)", df['ENDUF1'].dropna().unique(), default=df['ENDUF1'].dropna().unique())

df_filtrado = df[
    (df['DATAPREVENDA'] >= pd.to_datetime(data_inicial)) &
    (df['DATAPREVENDA'] <= pd.to_datetime(data_final)) &
    (df['ENDUF1'].isin(ufs))
]

# === KPIs ===
st.title("📊 Painel de Vendas (Google Sheets + Streamlit Cloud)")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total de Pedidos", f"{df_filtrado.shape[0]}")
col2.metric("Valor Faturado", f"R$ {df_filtrado['PRECOVENDA'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col3.metric("Frete Total", f"R$ {df_filtrado['VALORFRETE'].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
col4.metric("Clientes Únicos", f"{df_filtrado['RAZAOSOCIAL_NOME'].nunique()}")

# === Gráficos ===
st.subheader("📈 Faturamento por Vendedor")
vendedores = df_filtrado.groupby('VENDEDOR')['PRECOVENDA'].sum().reset_index().sort_values(by='PRECOVENDA', ascending=False)
st.plotly_chart(px.bar(vendedores, x='VENDEDOR', y='PRECOVENDA', labels={'PRECOVENDA': 'R$'}))

st.subheader("📆 Faturamento por Mês")
df_filtrado['AnoMes'] = df_filtrado['DATAPREVENDA'].dt.to_period('M').astype(str)
meses = df_filtrado.groupby('AnoMes')['PRECOVENDA'].sum().reset_index()
st.plotly_chart(px.bar(meses, x='AnoMes', y='PRECOVENDA', labels={'AnoMes': 'Mês/Ano', 'PRECOVENDA': 'R$'}))

st.subheader("📊 Tendência de Faturamento")
tendencia = df_filtrado.groupby('DATAPREVENDA')['PRECOVENDA'].sum().reset_index()
st.plotly_chart(px.line(tendencia, x='DATAPREVENDA', y='PRECOVENDA', markers=True))

# === Exportar CSV ===
st.subheader("📤 Exportar Dados")
csv = df_filtrado.to_csv(index=False).encode('utf-8-sig')
st.download_button("⬇️ Baixar CSV", csv, "dados_filtrados.csv", "text/csv")

# === Tabela ===
st.subheader("📋 Top 10 Clientes")
clientes = df_filtrado.groupby('RAZAOSOCIAL_NOME').agg({
    'PRECOVENDA': 'sum',
    'VALORFRETE': 'sum',
    'RAZAOSOCIAL_NOME': 'count'
}).rename(columns={'RAZAOSOCIAL_NOME': 'QtdPedidos'}).sort_values(by='PRECOVENDA', ascending=False).reset_index()
st.dataframe(clientes.head(10))
