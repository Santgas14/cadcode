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

# Atualizar planilha
def salvar_mudancas(mudancas):
    sheet = conectar_sheet()
    for idx, mudanca in mudancas.items():
        sheet.update_cell(idx + 2, 6, mudanca['STATUS'])
        sheet.update_cell(idx + 2, 7, mudanca['NÚMERO UTILIZADO'])
        sheet.update_cell(idx + 2, 8, mudanca['NENHUM FUNCIONOU'])

# Função principal Streamlit
def main():
    st.set_page_config(page_title="Envio WhatsApp", layout="wide")
    st.title("📱 Envio Automático WhatsApp")

    modelo_msg = st.text_area(
        "📝 Modelo da Mensagem",
        placeholder="Digite a mensagem aqui. Use {nome} para personalizar automaticamente."
    )

    # Botões no topo
    col_top1, col_top2 = st.columns([1, 1])
    with col_top1:
        salvar_botao = st.button("💾 Salvar alterações")
    with col_top2:
        atualizar_botao = st.button("🔄 Atualizar dados")

    df = obter_dados()

    # Inicializa session_state para mudanças
    if 'mudancas' not in st.session_state:
        st.session_state.mudancas = {}

    if salvar_botao:
        if st.session_state.mudancas:
            salvar_mudancas(st.session_state.mudancas)
            st.success("Alterações salvas com sucesso! ✅")
            st.session_state.mudancas = {}
            st.cache_resource.clear()
            st.rerun()
        else:
            st.info("Nenhuma alteração para salvar.")

    if atualizar_botao:
        st.cache_resource.clear()
        st.rerun()

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

    # Exibir contatos organizados
    for i, row in df.iterrows():
        enviado_inicial = row['STATUS'] == '✔️'
        nenhum_funcionou_inicial = row.get('NENHUM FUNCIONOU', '') == 'Sim'
        numero_utilizado_inicial = row.get('NÚMERO UTILIZADO', 'WHATSAPP')

        with st.container(border=True):
            st.markdown(f"### 👤 {row['NOME']} ({row['ESTADO']})")

            # WhatsApp links
            numeros_whatsapp = {
                'WHATSAPP': row['WHATSAPP'],
                'WHATSAPP2': row.get('WHATSAPP2', ''),
                'WHATSAPP3': row.get('WHATSAPP3', '')
            }
            numeros_whatsapp = {k: v for k, v in numeros_whatsapp.items() if v}

            if modelo_msg:
                mensagem_personalizada = modelo_msg.format(nome=row['NOME'])
                links = ' | '.join(
                    [f"[📲 {k}: {v}]({gerar_link_whatsapp(v, mensagem_personalizada)})"
                     for k, v in numeros_whatsapp.items()]
                )
                st.markdown(f"**WhatsApp:** {links}", unsafe_allow_html=True)
            else:
                st.info("⚠️ Preencha o modelo da mensagem acima para gerar os links do WhatsApp.")

            # Checkbox e radio organizados claramente
            cols = st.columns([1, 1, 2])

            enviado = cols[0].checkbox(
                "✅ Enviado?",
                value=enviado_inicial,
                key=f"status_{i}"
            )

            nenhum_funcionou = cols[1].checkbox(
                "❌ Nenhum funcionou",
                value=nenhum_funcionou_inicial,
                key=f"nenhum_{i}"
            )

            numero_utilizado = cols[2].radio(
                "📞 Qual número foi utilizado?",
                options=list(numeros_whatsapp.keys()),
                index=list(numeros_whatsapp.keys()).index(numero_utilizado_inicial) if numero_utilizado_inicial in numeros_whatsapp else 0,
                horizontal=True,
                key=f"num_usado_{i}"
            )

            # Feedback visual claro
            if enviado:
                st.success("✔️ Enviado")
            elif nenhum_funcionou:
                st.error("❌ Nenhum número funcionou")
            else:
                st.warning("⚠️ Pendente")

            # Registrar alterações
            if (enviado != enviado_inicial or
                numero_utilizado != numero_utilizado_inicial or
                nenhum_funcionou != nenhum_funcionou_inicial):

                st.session_state.mudancas[i] = {
                    'STATUS': "✔️" if enviado else "",
                    'NÚMERO UTILIZADO': "" if nenhum_funcionou else numero_utilizado,
                    'NENHUM FUNCIONOU': "Sim" if nenhum_funcionou else ""
                }

    if not st.session_state.mudancas:
        st.info("Nenhuma alteração pendente.")

if __name__ == "__main__":
    main()
