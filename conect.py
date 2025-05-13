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

# Gerar link para WhatsApp
def gerar_link_whatsapp(numero, mensagem):
    mensagem_encoded = urllib.parse.quote(mensagem)
    return f"https://wa.me/55{numero}?text={mensagem_encoded}"

# Função principal Streamlit
def main():
    st.set_page_config(page_title="Envio WhatsApp", layout="wide")
    st.title("📱 Envio Automático WhatsApp")

    # Modelo da mensagem
    modelo_msg = st.text_area(
        "📝 Modelo da Mensagem",
        placeholder="Digite a mensagem aqui. Use {nome} para personalizar automaticamente."
    )

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

    # Inicializa session_state para armazenar mudanças
    if 'mudancas' not in st.session_state:
        st.session_state.mudancas = {}

    # Exibir contatos com containers separados
    for i, row in df.iterrows():
        enviado_inicial = row['STATUS'] == '✔️'
        nenhum_funcionou_inicial = row.get('NENHUM FUNCIONOU', '') == 'Sim'
        numero_utilizado_inicial = row.get('NÚMERO UTILIZADO', 'WHATSAPP')

        with st.container(border=True):
            cols = st.columns([2.5, 1, 1])

            # Nome e Estado
            cols[0].markdown(f"### 👤 {row['NOME']} ({row['ESTADO']})")

            # Checkbox status de envio
            enviado = cols[1].checkbox("✅ Enviado?", value=enviado_inicial, key=f"status_{i}")

            # Feedback visual
            if enviado:
                cols[2].success("✔️ Enviado")
            else:
                cols[2].warning("❌ Pendente")

            numeros_whatsapp = {
                'WHATSAPP': row['WHATSAPP'],
                'WHATSAPP2': row.get('WHATSAPP2', ''),
                'WHATSAPP3': row.get('WHATSAPP3', '')
            }
            numeros_whatsapp = {k: v for k, v in numeros_whatsapp.items() if v}

            # WhatsApp links
            if modelo_msg:
                mensagem_personalizada = modelo_msg.format(nome=row['NOME'])
                links = ' | '.join(
                    [f"[📲 {k}: {v}]({gerar_link_whatsapp(v, mensagem_personalizada)})"
                     for k, v in numeros_whatsapp.items()]
                )
                st.markdown(f"**WhatsApp:** {links}", unsafe_allow_html=True)
            else:
                st.info("⚠️ Preencha o modelo da mensagem acima para gerar os links do WhatsApp.")

            # Opções adicionais
            col_extra1, col_extra2 = st.columns(2)

            # Número utilizado
            numero_utilizado = col_extra1.radio(
                "📞 Qual número foi utilizado?",
                options=list(numeros_whatsapp.keys()),
                index=list(numeros_whatsapp.keys()).index(numero_utilizado_inicial) if numero_utilizado_inicial in numeros_whatsapp else 0,
                key=f"num_usado_{i}"
            )

            # Nenhum número funcionou
            nenhum_funcionou = col_extra2.checkbox(
                "❌ Nenhum número funcionou",
                value=nenhum_funcionou_inicial,
                key=f"nenhum_{i}"
            )

            # Armazenar alterações temporariamente
            if (enviado != enviado_inicial or
                numero_utilizado != numero_utilizado_inicial or
                nenhum_funcionou != nenhum_funcionou_inicial):

                st.session_state.mudancas[i] = {
                    'STATUS': "✔️" if enviado else "",
                    'NÚMERO UTILIZADO': "" if nenhum_funcionou else numero_utilizado,
                    'NENHUM FUNCIONOU': "Sim" if nenhum_funcionou else ""
                }

    # Aplicar alterações na planilha com um único botão
    if st.session_state.mudancas:
        if st.button("💾 Salvar alterações na planilha"):
            sheet = conectar_sheet()
            for idx, mudanca in st.session_state.mudancas.items():
                sheet.update_cell(idx + 2, 6, mudanca['STATUS'])
                sheet.update_cell(idx + 2, 7, mudanca['NÚMERO UTILIZADO'])
                sheet.update_cell(idx + 2, 8, mudanca['NENHUM FUNCIONOU'])
            st.success("Alterações salvas com sucesso! ✅")
            st.session_state.mudancas = {}
            st.cache_resource.clear()
            st.rerun()
    else:
        st.info("Nenhuma alteração pendente.")

    # Atualizar dados sem salvar alterações
    if st.button("🔄 Atualizar dados sem salvar"):
        st.cache_resource.clear()
        st.rerun()

if __name__ == "__main__":
    main()
