import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

st.set_page_config(page_title="Gestão de Fretes", layout="wide", page_icon="🚚")

DB_FRETE = "dados_fretes.csv"
DB_MOT = "cadastro_motoristas.csv"
DB_VEIC = "cadastro_veiculos.csv"
DB_LOC = "cadastro_locais.csv"

def inicializar_bases():
    if not os.path.exists(DB_FRETE) or os.path.getsize(DB_FRETE) == 0:
        pd.DataFrame(columns=["Data", "Motorista", "Placa", "Local", "Preço (R$)", "Volume (m³)"]).to_csv(DB_FRETE, index=False, encoding="utf-8")
    if not os.path.exists(DB_MOT) or os.path.getsize(DB_MOT) == 0:
        pd.DataFrame(columns=["Nome"]).to_csv(DB_MOT, index=False, encoding="utf-8")
    if not os.path.exists(DB_VEIC) or os.path.getsize(DB_VEIC) == 0:
        pd.DataFrame(columns=["Placa"]).to_csv(DB_VEIC, index=False, encoding="utf-8")
    if not os.path.exists(DB_LOC) or os.path.getsize(DB_LOC) == 0:
        pd.DataFrame(columns=["Rota"]).to_csv(DB_LOC, index=False, encoding="utf-8")

inicializar_bases()

df_fretes = pd.read_csv(DB_FRETE, parse_dates=["Data"], encoding="utf-8")
df_motoristas = pd.read_csv(DB_MOT, encoding="utf-8")
df_veiculos = pd.read_csv(DB_VEIC, encoding="utf-8")
df_locais = pd.read_csv(DB_LOC, encoding="utf-8")

st.title("🚚 Controlo de Fretes e Comissões")

# BARRA LATERAL - CADASTROS DE APOIO
st.sidebar.header("🗂️ Cadastros de Apoio")

with st.sidebar.expander("👤 Cadastrar Motorista"):
    novo_mot = st.text_input("Nome do Motorista", key="reg_mot").strip().upper()
    if st.button("Salvar Motorista", key="btn_mot"):
        if novo_mot and novo_mot not in df_motoristas["Nome"].values:
            pd.DataFrame([{"Nome": novo_mot}]).to_csv(DB_MOT, mode='a', header=False, index=False, encoding="utf-8")
            st.success(f"{novo_mot} cadastrado!")
            st.rerun()

with st.sidebar.expander("🚛 Cadastrar Camião (Placa)"):
    nova_placa = st.text_input("Placa do Veículo", key="reg_placa").strip().upper()
    if st.button("Salvar Placa", key="btn_placa"):
        if nova_placa and nova_placa not in df_veiculos["Placa"].values:
            pd.DataFrame([{"Placa": nova_placa}]).to_csv(DB_VEIC, mode='a', header=False, index=False, encoding="utf-8")
            st.success(f"Placa {nova_placa} cadastrada!")
            st.rerun()

with st.sidebar.expander("📍 Cadastrar Local / Rota"):
    nova_rota = st.text_input("Local (Ex: SP x RJ)", key="reg_rota").strip().upper()
    if st.button("Salvar Local", key="btn_local"):
        if nova_rota and nova_rota not in df_locais["Rota"].values:
            pd.DataFrame([{"Rota": nova_rota}]).to_csv(DB_LOC, mode='a', header=False, index=False, encoding="utf-8")
            st.success(f"Rota {nova_rota} cadastrada!")
            st.rerun()

# ABAS PRINCIPAIS
aba_cadastro, aba_relatorio, aba_graficos = st.tabs(["📝 Lançar Frete", "📊 Relatórios", "📈 Gráficos Analíticos"])

with aba_cadastro:
    st.header("Registar Novo Frete")
    lista_mots = sorted(df_motoristas["Nome"].tolist())
    lista_veic = sorted(df_veiculos["Placa"].tolist())
    lista_locs = sorted(df_locais["Rota"].tolist())
    
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
                        "Data": pd.to_datetime(data_frete),
                        "Motorista": motorista_sel,
                        "Placa": placa_sel,
                        "Local": local_sel,
                        "Preço (R$)": valor_final_multiplicado,
                        "Volume (m³)": quantidade_m3
                    }])
                    novo_registo.to_csv(DB_FRETE, mode='a', header=False, index=False, encoding="utf-8")
                    st.success(f"✅ Gravado! Total: R$ {valor_final_multiplicado:,.2f}")
                    st.rerun()

with aba_relatorio:
    st.header("Consulta de Histórico")
    if df_fretes.empty:
        st.info("Nenhum frete encontrado na base de dados.")
    else:
        st.subheader("Filtros de Pesquisa")
        f_col1, f_col2, f_col3, f_col4 = st.columns(4)
        with f_col1:
            periodo = st.date_input("Intervalo de Datas", [df_fretes["Data"].min().date(), df_fretes["Data"].max().date()])
        with f_col2:
            motorista_filtrado = st.selectbox("Filtrar por Motorista", ["TODOS"] + sorted(df_fretes["Motorista"].unique().tolist()))
        with f_col3:
            placa_filtrada = st.selectbox("Filtrar por Placa", ["TODOS"] + sorted(df_fretes["Placa"].unique().tolist()))
        with f_col4:
            local_filtrado = st.selectbox("Filtrar por Local", ["TODOS"] + sorted(df_fretes["Local"].unique().tolist()))
            
        df_filtrado = df_fretes.copy()
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
            
            if not dados_tabela.empty:
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
            p.drawString(50, eixo_y - 25, f"Volume Geral: {volume_total:,.2f} m³")
            p.drawString(50, eixo_y - 40, f"Faturamento Bruto: R$ {faturamento_total:,.2f}")
            p.setFillColorRGB(0.1, 0.5, 0.1)
            p.drawString(50,_y:=eixo_y - 60, f"VALOR TOTAL DA COMISSÃO ({porcentagem_comissao}%): R$ {valor_comissao_calculado:,.2f}")
            
            p.showPage()
            p.save()
            buffer.seek(0)
            return buffer

        st.markdown("### Métricas do Período")
               # Configuração das 4 colunas de métricas na tela
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total de Viagens", len(df_filtrado))
        m2.metric("Faturamento Acumulado", f"R$ {faturamento_total:,.2f}")
        m3.metric("Volume Movimentado", f"{volume_total:,.2f} m³")
        m4.metric(f"Comissão ({porcentagem_comissao}%)", f"R$ {valor_comissao_calculado:,.2f}")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Gerando os dados do PDF
        pdf_data = gerar_pdf_relatorio_completo(df_filtrado)
        
        # O BOTÃO QUE ESTAVA FALTANDO (Inserido corretamente no bloco do Relatório):
        st.download_button(
            label="🖨️ Gerar PDF com Todas as Viagens",
            data=pdf_data,
            file_name=f"relatorio_viagens_{motorista_filtrado}.pdf",
            mime="application/pdf"
        )
        
        st.markdown("---")
        st.dataframe(df_filtrado, use_container_width=True)

# =========================================================================
# 3. ABA DE GRÁFICOS (Alinhada corretamente fora da aba de relatórios)
# =========================================================================
with aba_graficos:
    st.header("Análise de Desempenho")
    if df_fretes.empty:
        st.info("Registe fretes para visualizar as métricas visuais.")
    else:
        analise_tipo = st.radio("Selecione o Foco:", ["Por Motorista", "Por Camião (Placa)"], horizontal=True)
        col_g1, col_g2 = st.columns(2)
        if analise_tipo == "Por Motorista":
            with col_g1: st.plotly_chart(px.bar(df_fretes.groupby("Motorista", as_index=False)["Preço (R$)"].sum(), x="Motorista", y="Preço (R$)", title="Faturamento por Motorista"), use_container_width=True)
            with col_g2: st.plotly_chart(px.pie(df_fretes.groupby("Motorista", as_index=False)["Volume (m³)"].sum(), values="Volume (m³)", names="Motorista", title="Volume por Motorista", hole=0.3), use_container_width=True)
        else:
            with col_g1: st.plotly_chart(px.bar(df_fretes.groupby("Placa", as_index=False)["Preço (R$)"].sum(), x="Placa", y="Preço (R$)", title="Receita por Camião"), use_container_width=True)
            with col_g2: st.plotly_chart(px.bar(df_fretes.groupby("Placa", as_index=False).size().rename(columns={"size": "Viagens"}), x="Placa", y="Viagens", title="Viagens por Camião"), use_container_width=True)
