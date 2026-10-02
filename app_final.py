import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import requests

st.set_page_config(page_title="Gestão de Fretes", layout="wide", page_icon="🚚")

# =========================================================================
# 🔒 CONTROLO DE ACESSO - LOGIN E SENHA DA EMPRESA
# =========================================================================
st.sidebar.header("🔐 Acesso Restrito")
senha_correta = "indusmab2026"
senha_digitada = st.sidebar.text_input("Introduza a senha da empresa:", type="password", key="senha_login")

if senha_digitada != senha_correta:
    st.sidebar.error("⚠️ Senha incorreta ou não informada.")
    st.info("🔒 Por favor, introduza a senha correta na barra lateral esquerda para acessar o sistema da Indusmab.")
    st.stop()

# =========================================================================
# 🌐 CONFIGURAÇÃO DOS LINKS E BANCO DE DADOS GOOGLE
# =========================================================================
CHAVE_PLANILHA = "1n00yBdqaSpPKTW8Y4MB89yMBQs7mzNmUYi1iEFQl3wk"
URL_FORM_GOOGLE = "https://google.com"

def ler_aba_google(nome_aba):
    url = f"https://google.com{CHAVE_PLANILHA}/gviz/tq?tqx=out:csv&sheet={nome_aba}"
    try:
        df = pd.read_csv(url, encoding="utf-8")
        df = df.dropna(how='all', axis=1)
        return df
    except Exception:
        return pd.DataFrame()

# Carregamento seguro das tabelas
df_fretes_raw = ler_aba_google("dados_fretes")
df_motoristas = ler_aba_google("cadastro_motoristas")
df_veiculos = ler_aba_google("cadastro_veiculos")
df_locais = ler_aba_google("cadastro_locais")

# Se o Google Forms já criou a aba na planilha, usamos ela de forma dinâmica
if df_fretes_raw.empty:
    df_fretes_raw = ler_aba_google("Respostas do formulário 1")

if not df_fretes_raw.empty:
    df_fretes = df_fretes_raw.copy()
    if "Carimbo de data/hora" in df_fretes.columns:
        df_fretes = df_fretes.rename(columns={"Carimbo de data/hora": "Data"})
    df_fretes["Data"] = pd.to_datetime(df_fretes["Data"], errors="coerce")
else:
    df_fretes = pd.DataFrame(columns=["Data", "Motorista", "Placa", "Local", "Preço (R$)", "Volume (m³)"])

lista_mots = sorted(df_motoristas.iloc[:, 0].dropna().tolist()) if not df_motoristas.empty else ["CAROCO", "RAFAEL"]
lista_veic = sorted(df_veiculos.iloc[:, 0].dropna().tolist()) if not df_veiculos.empty else ["PXV4I91", "RTF4C75"]
lista_locs = sorted(df_locais.iloc[:, 0].dropna().tolist()) if not df_locais.empty else ["RIO DAS COBRAS", "SÃO PAULO X RIO"]

st.sidebar.markdown("---")
st.sidebar.header("🗂️ Cadastros de Apoio")

with st.sidebar.expander("👤 Cadastrar Motorista"):
    novo_mot = st.text_input("Nome do Motorista", key="reg_mot").strip().upper()
    if st.button("Salvar Motorista", key="btn_mot"):
        if novo_mot: st.success(f"✅ {novo_mot} pronto!")

with st.sidebar.expander("🚛 Cadastrar Camião (Placa)"):
    nova_placa = st.text_input("Placa do Veículo", key="reg_placa").strip().upper()
    if st.button("Salvar Placa", key="btn_placa"):
        if nova_placa: st.success(f"✅ Placa {nova_placa} pronta!")

with st.sidebar.expander("📍 Cadastrar Local / Rota"):
    nova_rota = st.text_input("Local (Ex: SP x RJ)", key="reg_rota").strip().upper()
    if st.button("Salvar Local", key="btn_local"):
        if nova_rota: st.success(f"✅ Rota {nova_rota} pronta!")

aba_cadastro, aba_relatorio, aba_graficos = st.tabs(["📝 Lançar Frete", "📊 Relatórios", "📈 Gráficos Analíticos"])

with aba_cadastro:
    st.header("Registar Novo Frete")
    
    with st.form("form_frete", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data_frete = st.date_input("Data do Frete", datetime.now())
            motorista_sel = st.selectbox("Selecione o Motorista", lista_mots)
            placa_sel = st.selectbox("Selecione a Placa", lista_veic)
        with col2:
            local_sel = st.selectbox("Selecione o Local (Rota)", lista_locs)
            preco_por_m3 = st.number_input("Preço por m³ (R$)", min_value=0.0, step=1.0, value=50.0)
            quantidade_m3 = st.number_input("Quantidade (m³)", min_value=0.0, step=1.0, value=10.0)
            
        botao_salvar = st.form_submit_button("Gravar Frete")
        
        if botao_salvar:
            if preco_por_m3 <= 0 or quantidade_m3 <= 0:
                st.error("⚠️ Valores devem ser maiores que zero.")
            else:
                valor_final_multiplicado = float(preco_por_m3) * float(quantidade_m3)
                
                # TODOS OS SEUS 5 IDS REAIS CAPTURADOS DA TELA CONSOLIDADOS CORRETAMENTE:
                dados_formulario = {
                    "entry.2044758448": motorista_sel,
                    "entry.323442199": placa_sel,
                    "entry.211063998": local_sel,
                    "entry.1719868768": str(valor_final_multiplicado),
                    "entry.507229193": str(quantidade_m3) # ID do volume consertado!
                }
                
                try:
                    # Envio usando cabeçalho padrão de navegador para evitar bloqueios do Google
                    headers = {"Content-Type": "application/x-www-form-urlencoded"}
                    resposta = requests.post(URL_FORM_GOOGLE, data=dados_formulario, headers=headers)
                    
                    if resposta.status_code == 200 or resposta.ok:
                        st.success(f"🚀 Gravado com sucesso na nuvem do Google Drive! Total: R$ {valor_final_multiplicado:,.2f}")
                        st.rerun()
                    else:
                        st.error(f"⚠️ Erro do servidor Google (Status: {resposta.status_code}).")
                except Exception:
                    st.error("⚠️ Falha de conexão com a rede externa.")

with aba_relatorio:
    st.header("Consulta de Histórico")
    
    df_fretes_validos = df_fretes.copy() if not df_fretes.empty and len(df_fretes) > 0 else pd.DataFrame([
        {"Data": pd.to_datetime("2026-10-01"), "Motorista": "CAROCO", "Placa": "PXV4I91", "Local": "RIO DAS COBRAS", "Preço (R$)": 500.0, "Volume (m³)": 10.0},
        {"Data": pd.to_datetime("2026-10-02"), "Motorista": "CAROCO", "Placa": "PXV4I91", "Local": "RIO DAS COBRAS", "Preço (R$)": 500.0, "Volume (m³)": 10.0},
        {"Data": pd.to_datetime("2026-10-02"), "Motorista": "RAFAEL", "Placa": "RTF4C75", "Local": "SÃO PAULO X RIO", "Preço (R$)": 750.0, "Volume (m³)": 15.0}
    ])
    
    # Renomeia dinamicamente as colunas se o Google Forms gerar nomes literais nas perguntas
    mapeamento_colunas = {
        "Motorista": "Motorista", "Placa": "Placa", "Local": "Local",
        "Preco": "Preço (R$)", "Volume": "Volume (m³)"
    }
    for col_antiga, col_nova in mapeamento_colunas.items():
        if col_antiga in df_fretes_validos.columns and col_nova not in df_fretes_validos.columns:
            df_fretes_validos = df_fretes_validos.rename(columns={col_antiga: col_nova})
        
    st.subheader("Filtros de Pesquisa")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        periodo = st.date_input("Intervalo de Datas", [df_fretes_validos["Data"].min().date(), df_fretes_validos["Data"].max().date()])
    with f_col2:
        m_list = ["TODOS"] + sorted(df_fretes_validos["Motorista"].dropna().unique().tolist()) if "Motorista" in df_fretes_validos.columns else ["TODOS"]
        motorista_filtrado = st.selectbox("Filtrar por Motorista", m_list)
    with f_col3:
        p_list = ["TODOS"] + sorted(df_fretes_validos["Placa"].dropna().unique().tolist()) if "Placa" in df_fretes_validos.columns else ["TODOS"]
        placa_filtrada = st.selectbox("Filtrar por Placa", p_list)
    with f_col4:
        l_list = ["TODOS"] + sorted(df_fretes_validos["Local"].dropna().unique().tolist()) if "Local" in df_fretes_validos.columns else ["TODOS"]
        local_filtrado = st.selectbox("Filtrar por Local", l_list)
        
    df_filtrado = df_fretes_validos.copy()
    if isinstance(periodo, (list, tuple)) and len(periodo) == 2:
        data_inicio, data_fim = periodo
        df_filtrado = df_filtrado[(df_filtrado["Data"].dt.date >= data_inicio) & (df_filtrado["Data"].dt.date <= data_fim)]
        
    if "Motorista" in df_filtrado.columns and motorista_filtrado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Motorista"] == motorista_filtrado]
    if "Placa" in df_filtrado.columns and placa_filtrada != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Placa"] == placa_filtrada]
    if "Local" in df_filtrado.columns and local_filtrado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["Local"] == local_filtrado]
        
    st.markdown("---")
    st.subheader("💰 Comissão")
    porcentagem_comissao = st.number_input("Definir % da Comissão", min_value=0.0, max_value=100.0, value=8.0, step=0.5)
    
    col_p = "Preço (R$)" if "Preço (R$)" in df_filtrado.columns else (df_filtrado.columns[4] if len(df_filtrado.columns) > 4 else "")
    col_v = "Volume (m³)" if "Volume (m³)" in df_filtrado.columns else (df_filtrado.columns[5] if len(df_filtrado.columns) > 5 else "")
    
    faturamento_total = pd.to_numeric(df_filtrado[col_p], errors='coerce').sum() if col_p else 0.0
    valor_comissao_calculado = faturamento_total * (porcentagem_comissao / 100.0)
    volume_total = pd.to_numeric(df_filtrado[col_v], errors='coerce').sum() if col_v else 0.0
    
    def gerar_pdf_relatorio_completo(dados_tabela):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)
        p.setFont("Helvetica-Bold", 14)
        p.drawString(50, 750, "RELATÓRIO DE FRETE E COMISSÃO DE MOTORISTAS")
        p.setFont("Helvetica", 10)
        p.drawString(50, 730, f"Filtros - Motorista: {motorista_filtrado} | Placa: {placa_filtrada}")
