import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import urllib.parse

# Conectando ao Google Sheets
@st.cache_resource
def conectar_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gspread_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open('lista').sheet1
    return sheet

# Ler dados da planilha
def obter_dados():
    sheet = conectar_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Atualizar status na planilha
def atualizar_status(index, status):
    sheet = conectar_sheet()
    sheet.update_cell(index + 2, 6, status)

# Gerar link do WhatsApp automaticamente
def gerar_link_whatsapp(numero, mensagem):
    mensagem_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/55{numero}?text={mensagem_encoded}"

# Interface Streamlit
st.title("📱 Envio Automático WhatsApp")

# Campo para inserir o modelo de mensagem
modelo_msg = st.text_area("📝 Modelo da Mensagem", placeholder="Digite a mensagem aqui. Use {nome} para personalizar automaticamente.")

# Carregar dados da planilha
df = obter_dados()

# Filtros
st.sidebar.title("🔍 Filtros")
estados = ['Todos'] + sorted(df['ESTADO'].unique().tolist())
estado_selecionado = st.sidebar.selectbox("Filtrar por Estado", estados)

status_filtro = st.sidebar.radio("Filtrar por Status", ['Todos', 'Enviado', 'Não enviado'])

# Aplicar filtros
if estado_selecionado != 'Todos':
    df = df[df['ESTADO'] == estado_selecionado]

if status_filtro == 'Enviado':
    df = df[df['STATUS'] == '✔️']
elif status_filtro == 'Não enviado':
    df = df[df['STATUS'] != '✔️']

st.subheader("Contatos para envio")

# Exibir lista organizada
for i, row in df.iterrows():
    with st.container(border=True):
        st.markdown(f"### {row['NOME']} ({row['ESTADO']})")
        cols = st.columns([3, 2, 1])

        # WhatsApp botões rápidos
        numeros_whatsapp = [row['WHATSAPP'], row.get('WHATSAPP2'), row.get('WHATSAPP3')]
        numeros_whatsapp = [num for num in numeros_whatsapp if num]

        if modelo_msg:
            mensagem_personalizada = modelo_msg.format(nome=row['NOME'])
            for num in numeros_whatsapp:
                link_whatsapp = gerar_link_whatsapp(num, mensagem_personalizada)
                cols[0].markdown(f"[📤 {num}]({link_whatsapp})", unsafe_allow_html=True)

        # Checkbox para status de envio
        enviado = cols[1].checkbox("Enviado?", value=bool(row['STATUS']), key=f"status_{i}")
        status_atual = "✔️" if enviado else ""

        if enviado != bool(row['STATUS']):
            atualizar_status(i, status_atual)
            st.rerun()

        # Feedback visual
        if enviado:
            cols[2].success("✔️")
        else:
            cols[2].warning("❌")

# Atualizar dados da planilha
if st.button("🔄 Atualizar dados"):
    st.cache_resource.clear()
    st.rerun()
