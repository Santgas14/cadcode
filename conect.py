import streamlit as st
import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials
import urllib.parse

# Conexão com Google Sheets
@st.cache_resource
def conectar_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = dict(st.secrets["gspread_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open('lista').sheet1
    return sheet

# Obter dados da planilha
def obter_dados():
    sheet = conectar_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Atualizar status na planilha
def atualizar_status(index, status):
    sheet = conectar_sheet()
    sheet.update_cell(index + 2, 6, status)

# Gerar link para WhatsApp
def gerar_link_whatsapp(numero, mensagem):
    mensagem_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/55{numero}?text={mensagem_encoded}"

# Função principal da interface Streamlit
def main():
    st.set_page_config(page_title="Envio WhatsApp", layout="wide")
    st.title("📱 Envio Automático WhatsApp")

    # Modelo da mensagem
    modelo_msg = st.text_area("📝 Modelo da Mensagem", placeholder="Digite a mensagem aqui. Use {nome} para personalizar automaticamente.")

    # Carregar dados
    df = obter_dados()

    # Sidebar com filtros
    with st.sidebar:
        st.title("🔍 Filtros")
        estados = ['Todos'] + sorted(df['ESTADO'].unique().tolist())
        estado_selecionado = st.selectbox("Filtrar por Estado", estados)
        status_filtro = st.radio("Filtrar por Status", ['Todos', 'Enviado', 'Não enviado'])

    # Aplicar filtros
    if estado_selecionado != 'Todos':
        df = df[df['ESTADO'] == estado_selecionado]

    if status_filtro == 'Enviado':
        df = df[df['STATUS'] == '✔️']
    elif status_filtro == 'Não enviado':
        df = df[df['STATUS'] != '✔️']

    st.subheader("📒 Contatos para envio")

    # Exibir contatos com containers separados claramente
    for i, row in df.iterrows():
        enviado_inicial = row['STATUS'] == '✔️'

        with st.container(border=True):
            cols = st.columns([2.5, 1, 1])

            # Nome e Estado
            cols[0].markdown(f"### 👤 {row['NOME']} ({row['ESTADO']})")

            # Checkbox status de envio
            enviado = cols[1].checkbox("✅ Enviado?", value=enviado_inicial, key=f"status_{i}")

            # Feedback visual mais claro
            if enviado:
                cols[2].success("✔️ Enviado")
            else:
                cols[2].warning("❌ Pendente")

            # Links WhatsApp abaixo dos nomes (melhor organização)
            numeros_whatsapp = [row['WHATSAPP'], row.get('WHATSAPP2'), row.get('WHATSAPP3')]
            numeros_whatsapp = [num for num in numeros_whatsapp if num]

            if modelo_msg:
                mensagem_personalizada = modelo_msg.format(nome=row['NOME'])
                links = ' | '.join(
                    [f"[📲 {num}]({gerar_link_whatsapp(num, mensagem_personalizada)})" for num in numeros_whatsapp]
                )
                st.markdown(f"**WhatsApp:** {links}", unsafe_allow_html=True)
            else:
                st.info("⚠️ Preencha o modelo da mensagem acima para gerar os links do WhatsApp.")

            # Atualizar o status
            if enviado != enviado_inicial:
                status_atual = "✔️" if enviado else ""
                atualizar_status(i, status_atual)
                st.experimental_rerun()

    # Botão para atualizar os dados
    if st.button("🔄 Atualizar dados"):
        st.cache_resource.clear()
        st.rerun()

if __name__ == "__main__":
    main()
