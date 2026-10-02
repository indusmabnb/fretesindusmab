import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from streamlit_gsheets import GSheetsConnection
import io

st.set_page_config(page_title="Gestão de Fretes", layout="wide", page_icon="🚚")

st.title("🚚 Controlo de Fretes e Comissões (Google Sheets)")

# =========================================================================
# CONEXÃO COM O GOOGLE SHEETS
# =========================================================================
# O Streamlit gerencia a conexão de forma segura usando o st.connection
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Lendo as 4 abas da planilha direto da nuvem do Google
    df_fretes = conn.read(worksheet="dados_fretes", ttl=0)
    df_motoristas = conn.read(worksheet="cadastro_motoristas", ttl=0)
    df_veiculos = conn.read(worksheet="cadastro_veiculos", ttl=0)
    df_locais = conn.read(worksheet="cadastro_locais", ttl=0)
    
    # Tratando colunas vazias ou nulas para não quebrar o Pandas
    df_fretes["Data"] = pd.to_datetime(df_fretes["Data"], errors="coerce")
except Exception as e:
    st.error("⚠️ Erro ao conectar com o Google Sheets. Verifique as credenciais.")
    st.stop()

# =========================================================================
# BARRA LATERAL - CADASTROS DE APOIO (SALVANDO NO GOOGLE)
# =========================================================================
st.sidebar.header("🗂️ Cadastros de Apoio")

with st.sidebar.expander("👤 Cadastrar Motorista"):
    novo_mot = st.text_input("Nome do Motorista", key="reg_mot").strip().upper()
    if st.button("Salvar Motorista", key="btn_mot"):
        if novo_mot and (df_motoristas.empty or novo_mot not in df_motoristas["Nome"].values):
            novo_df = pd.DataFrame([{"Nome": novo_mot}])
            df_atualizado = pd.concat([df_motoristas, novo_df], ignore_index=True)
            conn.update(worksheet="cadastro_motoristas", data=df_atualizado)
            st.success(f"{novo_mot} cadastrado no Google Drive!")
            st.rerun()

with st.sidebar.expander("🚛 Cadastrar Camião (Placa)"):
    nova_placa = st.text_input("Placa do Veículo", key="reg_placa").strip().upper()
    if st.button("Salvar Placa", key="btn_placa"):
        if nova_placa and (df_veiculos.empty or nova_placa not in df_veiculos["Placa"].values):
            novo_df = pd.DataFrame([{"Placa": nova_placa}])
            df_atualizado = pd.concat([df_veiculos, novo_df], ignore_index=True)
            conn.update(worksheet="cadastro_veiculos", data=df_atualizado)
            st.success(f"Placa {nova_placa} cadastrada no Google Drive!")
            st.rerun()

with st.sidebar.expander("📍 Cadastrar Local / Rota"):
    nova_rota = st.text_input("Local (Ex: SP x RJ)", key="reg_rota").strip().upper()
    if st.button("Salvar Local", key="btn_local"):
        if nova_rota and (df_locais.empty or nova_rota not in df_locais["Rota"].values):
            novo_df = pd.DataFrame([{"Rota": nova_rota}])
            df_atualizado = pd.concat([df_locais, novo_df], ignore_index=True)
            conn.update(worksheet="cadastro_locais", data=df_atualizado)
            st.success(f"Rota {nova_rota} cadastrada no Google Drive!")
            st.rerun()

# ABAS PRINCIPAIS
aba_cadastro, aba_relatorio, aba_graficos = st.tabs(["📝 Lançar Frete", "📊 Relatórios", "📈 Gráficos Analíticos"])

with aba_cadastro:
    st.header("Registar Novo Frete")
    lista_mots = sorted(df_motoristas["Nome"].dropna().tolist()) if not df_motoristas.empty else []
    lista_veic = sorted(df_veiculos["Placa"].dropna().tolist()) if not df_veiculos.empty else []
    lista_locs = sorted(df_locais["Rota"].dropna().tolist()) if not df_locais.empty else []
    
    if not lista_mots or not lista_veic or not lista_locs:
        st.info("⚠️ Use os menus da barra lateral esquerda para cadastrar ao menos: 1 Motorista, 1 Camião e 1 Local.")
    else:
        with st.form("form_frete", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                data_frete = st.date_input("Data do Frete", datetime.now())
                motorista_sel = st.selectbox("Selecione o Motorista", lista_mots)
                placa_sel = st.selectbox("Selecione a Placa", lista_veic)
            with col2:
                local_sel = st.selectbox("Selecione o Local (Rota)", lista_locs)
                preco_por_m3 = st.number_input("Preço por m³ (R$)", min_value=0.0, step=1.0)
                quantidade_m3 = st.number_input("Quantidade (m³)", min_value=0.0, step=1.0)
                
            botao_salvar = st.form_submit_button("Gravar Frete")
            
            if botao_salvar:
                if preco_por_m3 <= 0 or quantidade_m3 <= 0:
                    st.error("⚠️ Preço e Volume devem ser maiores que zero.")
                else:
                    valor_final_multiplicado = float(preco_por_m3) * float(quantidade_m3)
                    novo_registo = pd.DataFrame([{
                        "Data": data_frete.strftime('%Y-%m-%d'),
                        "Motorista": motorista_sel,
                        "Placa": placa_sel,
                        "Local": local_sel,
                        "Preço (R$)": valor_final_multiplicado,
                        "Volume (m³)": quantidade_m3
                    }])
                    df_atualizado = pd.concat([df_fretes, novo_registo], ignore_index=True)
                    conn.update(worksheet="dados_fretes", data=df_atualizado)
                    st.success(f"✅ Gravado no Google Sheets! Total: R$ {valor_final_multiplicado:,.2f}")
                    st.rerun()

with aba_relatorio:
    st.header("Consulta de Histórico")
    # Filtra linhas totalmente em branco que o Google Sheets possa trazer
    df_fretes_validos = df_fretes.dropna(subset=["Motorista", "Placa"]) if not df_fretes.empty else pd.DataFrame()
    
    if df_fretes_validos.empty:
        st.info("Nenhum frete encontrado na planilha do Google.")
    else:
        st.subheader("Filtros de Pesquisa")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            data_minima = df_fretes_validos["Data"].min().date() if pd.notnull(df_fretes_validos["Data"].min()) else datetime.now().date()
            data_maxima = df_fretes_validos["Data"].max().date() if pd.notnull(df_fretes_validos["Data"].max()) else datetime.now().date()
            periodo = st.date_input("Intervalo de Datas", [data_minima, data_maxima])
        with f_col2:
            motorista_filtrado = st.selectbox("Filtrar por Motorista", ["TODOS"] + sorted(df_fretes_validos["Motorista"].unique().tolist()))
        with f_col3:
            placa_filtrada = st.selectbox("Filtrar por Placa", ["TODOS"] + sorted(df_fretes_validos["Placa"].unique().tolist()))
        with f_col4:
            local_filtrado = st.selectbox("Filtrar por Local", ["TODOS"] + sorted(df_fretes_validos["Local"].unique().tolist()))
            
        df_filtrado = df_fretes_validos.copy()
        if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
            data_inicio, data_fim = periodo
            df_filtrado = df_filtrado[(df_filtrado["Data"].dt.date >= data_inicio) & (df_filtrado["Data"].dt.date <= data_fim)]
            
        if motorista_filtrado != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["Motorista"] == motorista_filtrado]
        if placa_filtrada != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["Placa"] == placa_filtrada]
        if local_filtrado != "TODOS":
            df_filtrado = df_filtrado[df_filtrado["Local"] == local_filtrado]
            
        st.markdown("---")
        st.subheader("💰 Comissão")
        porcentagem_comissao = st.number_input("Definir % da Comissão", min_value=0.0, max_value=100.0, value=8.0, step=0.5)
        
        faturamento_total = df_filtrado['Preço (R$)'].sum() if not df_filtrado.empty else 0.0
        valor_comissao_calculado = faturamento_total * (porcentagem_comissao / 100.0)
        volume_total = df_filtrado['Volume (m³)'].sum() if not df_filtrado.empty else 0.0
        
        def gerar_pdf_relatorio_completo(dados_tabela):
            buffer = io.BytesIO()
            p = canvas.Canvas(buffer, pagesize=letter)
            p.setFont("Helvetica-Bold", 14)
            p.drawString(50, 750, "RELATÓRIO DE FRETE E COMISSÃO DE MOTORISTAS")
            p.setFont("Helvetica", 10)
            p.drawString(50, 730, f"Filtros - Motorista: {motorista_filtrado} | Placa: {placa_filtrada} | Rota: {local_filtrado}")
            p.line(50, 715, 550, 715)
            
            p.setFont("Helvetica-Bold", 9)
            p.drawString(50, 695, "DATA")
            p.drawString(120, 695, "MOTORISTA")
            p.drawString(230, 695, "PLACA")
            p.drawString(290, 695, "ROTA / LOCAL")
            p.drawString(420, 695, "VOL (m³)")
            p.drawString(480, 695, "VALOR (R$)")
            p.line(50, 685, 550, 685)
            
            eixo_y = 665
            p.setFont("Helvetica", 9)
            
            for idx, linha in dados_tabela.iterrows():
                data_formatada = linha["Data"].strftime('%d/%m/%Y')
                p.drawString(50, eixo_y, str(data_formatada))
                p.drawString(120, eixo_y, str(linha["Motorista"])[:18])
                p.drawString(230, eixo_y, str(linha["Placa"]))
                p.drawString(290, eixo_y, str(linha["Local"])[:20])
                p.drawString(420, eixo_y, f"{linha['Volume (m³)']:,.2f}")
                p.drawString(480, eixo_y, f"R$ {linha['Preço (R$)']:,.2f}")
                eixo_y -= 20
                if eixo_y < 100:
                    break
            
            p.line(50, eixo_y + 10, 550, eixo_y + 10)
            p.setFont("Helvetica-Bold", 10)
            p.drawString(50, eixo_y - 10, f"Total Viagens: {len(dados_tabela)}")
