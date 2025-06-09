import numpy as np
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import locale as lc
import consultaSQL
import sys
from inspect import getmembers, isfunction
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta
import calendar
import os
import pandas as pd
from datetime import date
from fpdf import FPDF
from babel.numbers import format_currency
import requests
import json
import re
import base64

try:
    lc.setlocale(lc.LC_ALL, 'pt_BR.UTF-8')
    def formatar_moeda(valor):
        return lc.currency(valor, grouping=True, symbol=True)
except lc.Error:
    lc.setlocale(lc.LC_ALL, '')
    def formatar_moeda(valor):
        return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def verificar_autenticacao():
    """Verifica se o usuário está autenticado"""
    if not st.session_state.get('authenticated', False):
        st.error("Você precisa fazer login para acessar esta página!")
        st.session_state.page = None
        st.rerun()

def pagina_nao_encontrada():
    """Página exibida quando não encontra a função correspondente"""
    verificar_autenticacao()
    st.error("🚨 Dashboard não configurado para este grupo")
    st.write(f"Grupo: {st.session_state.get('dashboard_page', 'Não especificado').replace('pagina', '')}")
    
    if st.button("↩️ Voltar"):
        st.session_state.page = None  
        st.switch_page("main.py")  

# PÁGINA ATOS
def paginaatos():
    verificar_autenticacao()

    # Configuração da página
    st.set_page_config(page_title="Atos Capital", page_icon="📊", layout="wide")

    # Barra lateral
    if 'user_info' in st.session_state:
        # Adicionar botão Voltar apenas para administradores
        if st.session_state.user_info['permissao'].lower() == 'adm':
            if st.sidebar.button("⬅️ Voltar para Administração"):
                st.session_state.page = 'adm'
                st.rerun()

    # Inicializa a variável de sessão se não existir
    if 'pagina' not in st.session_state:
        st.session_state['pagina'] = 'principal'

    # Mostra a página apropriada com base no estado
    if st.session_state['pagina'] == 'principal':
        def pagina_principal():
            # Início sidebar
            st.markdown(
                """
                <style>
                [data-testid="stSidebar"] {
                    background-color: #800000; 
                }
                </style>
                """,
                unsafe_allow_html=True,
            )
            
            st.markdown("""
            <style>
            /* Estilizar todos os botões da sidebar */
            section[data-testid="stSidebar"] button {
                width: 100% !important;
                height: 40px !important;
                margin-bottom: 10px;
                background-color: #1C1C1C;
                color: white;
                font-weight: bold;
                border-radius: 8px;
                border: none;
                transition: background-color 0.3s ease;
            }

            /* Hover nos botões */
            section[data-testid="stSidebar"] button:hover {
                background-color: darkblue;
            }
            </style>
            """, unsafe_allow_html=True)


            st.sidebar.header("Filtros")
            filiais = consultaSQL.obter_nmfilial()
            filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)

            if st.sidebar.button("📅 Selecionar Meses Anteriores"):
                st.session_state['pagina'] = 'meses_anterior'
                st.rerun()

            # Lista de nomes dos meses
            meses_nomes = [
                "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
            ]

            # Usa o dia anterior como base
            data_base = datetime.now() - timedelta(days=1)
            mes_num = data_base.month
            ano_base = data_base.year

            # Define o mês atual como referência
            mes_referencia = [meses_nomes[mes_num - 1]]
            vendas = consultaSQL.obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada)

            # Se não houver dados no mês atual, tenta o mês anterior
            if not vendas:
                if mes_num == 1:
                    mes_anterior = 12
                    ano_base -= 1
                else:
                    mes_anterior = mes_num - 1
                mes_referencia = [meses_nomes[mes_anterior - 1]]
                vendas = consultaSQL.obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada)
            
            if st.sidebar.button("🖨️ Gerar Relatório"):
                st.session_state['dashboard_page'] = 'paginarelatoriocompleto'
                st.rerun()
            
            if st.sidebar.button("🤖 Agente IA Atos"):
                st.session_state['dashboard_page'] = 'paginaagenteia'
                st.rerun()
                            
            # Fim sidebar

            # Início cabeçalho
            left_co, cent_co, last_co = st.columns(3)
            with cent_co:
                st.image('logoatos.png', width=500)
            st.write(f"# Dashboard de venda da {filial_selecionada}")
            # Fim cabeçalho

            total_vendas = consultaSQL.obter_vendas_ano_anterior(filial_selecionada)
            meta_mes = consultaSQL.obter_meta_mes(filial_selecionada)
            previsao = consultaSQL.obter_previsao_vendas(filial_selecionada)
            acumulo_vendas_ano_anterior = consultaSQL.acumulo_vendas_periodo_ano_anterior(filial_selecionada)
            acumulo_meta_ano_anterior = consultaSQL.obter_acumulo_meta_ano_anterior(filial_selecionada)
            acumulo_de_vendas = consultaSQL.obter_acumulo_de_vendas(filial_selecionada)
            vendas_dia_anterior, data_venda_dia = consultaSQL.obter_ultima_venda_com_valor(filial_selecionada)
            percentual_crescimento_atual = consultaSQL.obter_percentual_de_crescimento_atual(filial_selecionada)
            percentual_crescimento_meta = consultaSQL.obter_percentual_crescimento_meta(filial_selecionada)
            vendas_mensais = consultaSQL.obter_vendas_anual_e_filial(filial_selecionada)

            @st.cache_data
            def grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas):
                def safe_float(value):
                    if value is None:
                        return 0.0
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0

                meta_mes = safe_float(meta_mes)
                previsao = safe_float(previsao)
                acumulo_meta_ano_anterior = safe_float(acumulo_meta_ano_anterior)
                acumulo_de_vendas = safe_float(acumulo_de_vendas)

                categorias = ["Meta do mês", "Previsão", "Acumulado meta", "Acumulado Vendas"]
                valores = [meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas]
                cores = ["darkgray", "darkblue", "darkred", "lightgray"]

                fig = go.Figure()
                
                texto_formatado = [formatar_moeda(v) for v in valores]
                hover_texto = [f"{cat}<br>{formatar_moeda(v)}" for cat, v in zip(categorias, valores)]

                
                fig.add_trace(go.Bar(
                x=categorias,
                y=valores,
                marker_color=cores,
                text=texto_formatado,
                textposition='outside',
                hovertext=hover_texto,
                hoverinfo='text'
                ))

                fig.update_layout(
                    title=f"📊 Metas e previsões da {filial_selecionada}",
                    xaxis_title="",
                    yaxis_title="Valor (R$)",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=550,
                    width=500,
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True,
                        tickformat=",."
                    )
                )
                return fig

            @st.cache_data 
            def grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta):
                try:
                    percentual_crescimento_atual = float(percentual_crescimento_atual)
                except (ValueError, TypeError):
                    percentual_crescimento_atual = 0.0

                try:
                    percentual_crescimento_meta = float(percentual_crescimento_meta)
                except (ValueError, TypeError):
                    percentual_crescimento_meta = 0.0
                    
                fig = go.Figure()

                categorias = ["Cresc. 2025", "Cresc. meta"]
                valores = [percentual_crescimento_atual, percentual_crescimento_meta]
                cores = ["green", "aqua"]

                texto_formatado = [f"{v:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".") for v in valores]
                hover_texto = [f"{cat}: {v:,.2f}%".replace(",", "X").replace(".", ",").replace("X", ".") for cat, v in zip(categorias, valores)]
                
                fig.add_trace(go.Bar(
                    x=categorias,
                    y=valores,
                    marker_color=cores,
                    text=texto_formatado,
                    textposition='outside',
                    hovertext=hover_texto,
                    hoverinfo='text' 
                ))

                y_min = min(valores)
                y_max = max(valores)
                y_range_margin = (y_max - y_min) * 0.3  

                fig.update_layout(
                    title="% Crescimento",
                    xaxis_title="",
                    yaxis_title="Valor %",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=350,
                    width=350,
                    margin=dict(t=100, b=50, l=50, r=50), 
                    yaxis=dict(
                        range=[y_min - y_range_margin, y_max + y_range_margin],
                        zeroline=True,
                        zerolinecolor='gray'
                    )
                )

                return fig

            @st.cache_data
            def grafico_linhas_por_filial(mes_referencia, filial_selecionada):
                vendas = consultaSQL.obter_vendas_por_mes_e_filial(mes_referencia, filial_selecionada)

                if not vendas:
                    st.warning("Nenhuma venda encontrada para os filtros selecionados.")
                    return

                valores = [float(v[0]) if isinstance(v[0], Decimal) else v[0] for v in vendas]
                datas = [v[1] for v in vendas]
                meses = [v[2] for v in vendas]
                anos = [v[3] for v in vendas]

                df_vendas = pd.DataFrame({
                    "Data": pd.to_datetime(datas),
                    "Valor": valores,
                    "Mês": [str(m) for m in meses],
                    "Ano": [str(a) for a in anos]
                })

                df_vendas["Dia"] = df_vendas["Data"].dt.day 
                df_vendas["Valor_formatado"] = df_vendas["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))


                fig = go.Figure()

                df_vendas["MesAno"] = df_vendas["Mês"] + "/" + df_vendas["Ano"]

                for mesano in df_vendas["MesAno"].unique():
                    df_mesano = df_vendas[df_vendas["MesAno"] == mesano]

                    fig.add_trace(go.Scatter(
                        x=df_mesano["Dia"], 
                        y=df_mesano["Valor"],
                        mode='lines+markers',
                        name=mesano,
                        hovertemplate='Dia %{x}<br>Valor: %{customdata}<extra></extra>',
                        customdata=df_mesano["Valor_formatado"]
                    ))

                fig.update_layout(
                    title=f"📈 Vendas comparadas {mes_referencia[0]} - {filial_selecionada}",
                    xaxis_title="Dia do Mês",
                    yaxis_title="Vendas (R$)",
                    template="plotly_white",
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True, 
                        tickformat=",."
                    )
                )

                return fig

            def grafico_de_evolucao_vendas(vendas_mensais):
                df_vendas = pd.DataFrame(list(vendas_mensais.items()), columns=['Mês', 'Vendas'])
                df_vendas['Mês'] = pd.to_datetime(df_vendas['Mês'], format='%m/%Y')
                df_vendas = df_vendas.sort_values("Mês")

                fig = go.Figure()

                df_vendas["Valor_formatado"] = df_vendas["Vendas"].apply(formatar_moeda)

                fig.add_trace(go.Scatter(
                    x=df_vendas["Mês"].dt.strftime('%m/%Y'),
                    y=df_vendas["Vendas"],
                    mode='lines+markers',
                    name="Vendas",
                    hovertemplate='Mês %{x}<br>Valor: %{customdata}<extra></extra>',
                    customdata=df_vendas["Valor_formatado"]
                ))

                fig.update_layout(
                    title=f"📊 Vendas nos últimos 12 meses - {filial_selecionada}",
                    xaxis_title="Meses",
                    yaxis_title="Valor das Vendas (R$)",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis_tickformat="R$ ,.2f",
                    template="plotly_white",
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True,
                        tickformat=",." 
                    )
                )
                return fig

            # Mapa das filiais
            coordenadas_filiais = {
                'FILIAL BELÉM': {'latitude': -1.455, 'longitude': -48.489},
                'FILIAL BELO HORIZONTE': {'latitude': -19.9167, 'longitude': -43.9345},
                'FILIAL BRASÍLIA': {'latitude': -15.7939, 'longitude': -47.8828},
                'FILIAL CAMPINAS': {'latitude': -22.9056, 'longitude': -47.0608},
                'FILIAL CURITIBA': {'latitude': -25.4284, 'longitude': -49.2733},
                'FILIAL DUQUE DE CAXIAS': {'latitude': -22.7868, 'longitude': -43.3054},
                'FILIAL FORTALEZA': {'latitude': -3.7172, 'longitude': -38.5433},
                'FILIAL GOIÂNIA': {'latitude': -16.6869, 'longitude': -49.2648},
                'FILIAL GUARULHOS': {'latitude': -23.4545, 'longitude': -46.5333},
                'FILIAL MACEIÓ': {'latitude': -9.6658, 'longitude': -35.735},
                'FILIAL MANAUS': {'latitude': -3.119, 'longitude': -60.0217},
                'FILIAL RECIFE': {'latitude': -8.0476, 'longitude': -34.877},
                'FILIAL RIO DE JANEIRO': {'latitude': -22.9068, 'longitude': -43.1729},
                'FILIAL SALVADOR': {'latitude': -12.9714, 'longitude': -38.5014},
                'FILIAL SÃO GONÇALO': {'latitude': -22.8268, 'longitude': -43.0634},
                'FILIAL SÃO LUÍS': {'latitude': -2.5307, 'longitude': -44.3068},
                'FILIAL SÃO PAULO': {'latitude': -23.5505, 'longitude': -46.6333},
            }
            
            dados_vendas = pd.DataFrame({
                'filial': ['FILIAL BELÉM', 'FILIAL BELO HORIZONTE', 'FILIAL BRASÍLIA', 'FILIAL CAMPINAS', 
                          'FILIAL CURITIBA', 'FILIAL DUQUE DE CAXIAS', 'FILIAL FORTALEZA', 'FILIAL GOIÂNIA', 
                          'FILIAL GUARULHOS', 'FILIAL MACEIÓ', 'FILIAL MANAUS', 'FILIAL RECIFE', 
                          'FILIAL RIO DE JANEIRO', 'FILIAL SALVADOR', 'FILIAL SÃO GONÇALO', 
                          'FILIAL SÃO LUÍS', 'FILIAL SÃO PAULO']
            })
            
            dados_vendas['latitude'] = dados_vendas['filial'].map(lambda x: coordenadas_filiais[x]['latitude'])
            dados_vendas['longitude'] = dados_vendas['filial'].map(lambda x: coordenadas_filiais[x]['longitude'])

            # Exibição:
            col1, col2, col3 = st.columns(3)

            with col1:
                st.write(f"""#### Vendas 2024: \n 
                        {formatar_moeda(total_vendas)}
                        """)
            with col2:
                st.write(f"""#### Acumulado 2024: \n
                        {formatar_moeda(acumulo_vendas_ano_anterior)}
                        """)
            with col3:
                st.write(f"""#### Vendas do dia: ({data_venda_dia.strftime('%d/%m/%Y') if data_venda_dia else 'Sem data'})\n
                        {formatar_moeda(vendas_dia_anterior)} """)

            exibindo_grafico_de_barras = grafico_de_barras(meta_mes, previsao, acumulo_meta_ano_anterior, acumulo_de_vendas)
            st.plotly_chart(exibindo_grafico_de_barras, use_container_width=True)

            st.divider()

            exibindo_grafico_de_crescimento = grafico_de_crescimento(percentual_crescimento_atual, percentual_crescimento_meta)
            st.sidebar.plotly_chart(exibindo_grafico_de_crescimento)

            exibindo_grafico_de_linhas_vendas_por_mes = grafico_linhas_por_filial(mes_referencia, filial_selecionada)
            st.write(exibindo_grafico_de_linhas_vendas_por_mes)

            exibindo_grafico_acompanhamanto_anual = grafico_de_evolucao_vendas(vendas_mensais)
            st.write(exibindo_grafico_acompanhamanto_anual)

            # Simula valores de vendas para cada filial
            dados_vendas["vendas"] = dados_vendas["filial"].apply(
                lambda f: max(float(consultaSQL.obter_acumulo_de_vendas(f) or 0), 1)
            )

            dados_vendas["vendas_formatado"] = dados_vendas["vendas"].apply(formatar_moeda)

            fig_mapa = px.scatter_mapbox(
                dados_vendas,
                lat="latitude",
                lon="longitude",
                color="vendas",
                size="vendas",
                size_max=30,
                zoom=3,
                height=600,
                color_continuous_scale="RdBu",
                custom_data=["filial", "vendas_formatado"]  
            )

            fig_mapa.update_traces(
                hovertemplate="<b>%{customdata[0]}</b><br>Vendas: %{customdata[1]}<extra></extra>"
            )

            fig_mapa.update_layout(
                mapbox_style="carto-darkmatter",
                margin={"r": 0, "t": 0, "l": 0, "b": 0},
                coloraxis_colorbar=dict(
                    title="Vendas (R$)",
                    tickvals=np.linspace(dados_vendas["vendas"].min(), dados_vendas["vendas"].max(), 5),
                    ticktext=[formatar_moeda(v) for v in np.linspace(dados_vendas["vendas"].min(), dados_vendas["vendas"].max(), 5)]
                )
            )

            st.subheader("📍 Mapa das filiais - Vendas Acumuladas Mês")
            st.plotly_chart(fig_mapa, use_container_width=True)
                    
        pagina_principal()
    else:
        def pagina_meses_anterior():
            st.markdown(
                """
                <style>
                [data-testid="stSidebar"] {
                    background-color: #800000; 
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("""
                <style>
                /* Estilizar todos os botões da sidebar */
                section[data-testid="stSidebar"] button {
                    width: 100% !important;
                    height: 40px !important;
                    margin-bottom: 10px;
                    background-color: #1C1C1C;
                    color: white;
                    font-weight: bold;
                    border-radius: 8px;
                    border: none;
                    transition: background-color 0.3s ease;
                }

                /* Hover nos botões */
                section[data-testid="stSidebar"] button:hover {
                    background-color: darkblue;
                }
                </style>
            """, unsafe_allow_html=True)

            st.sidebar.header("Filtros")
            filiais = consultaSQL.obter_nmfilial()
            filial_selecionada = st.sidebar.selectbox("Selecione a Filial", filiais)

            meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", 
                     "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

            hoje = datetime.today()
            dia_hoje = hoje.day
            mes_atual = hoje.month
            ano_atual = hoje.year

            anos_disponiveis = consultaSQL.obter_anos_disponiveis()
            ano_selecionado = st.sidebar.selectbox("Selecione o ano de referência", anos_disponiveis, index=len(anos_disponiveis) - 1)

            if dia_hoje == 1 and mes_atual == 1:
                anos_disponiveis.remove(ano_atual)

            if ano_selecionado == ano_atual:
                if dia_hoje == 1:
                    if mes_atual == 1:
                        meses_disponiveis = []
                    else:
                        meses_disponiveis = meses[:mes_atual - 2]
                else:
                    meses_disponiveis = meses[:mes_atual - 1]
            else:
                meses_disponiveis = meses

            if meses_disponiveis:
                mes_referencia = st.sidebar.selectbox("Selecione o mês de referência", meses_disponiveis)
                # Botão para voltar ao mês atual
                if st.sidebar.button("Voltar para Mês Atual"):
                    st.session_state['pagina'] = 'principal'
                    st.rerun()
            else:
                st.sidebar.warning("Nenhum mês disponível para seleção com base na data atual.")
                mes_referencia = None
                  
            indice_mes_referencia = meses.index(mes_referencia) + 1

            if dia_hoje == 1 and indice_mes_referencia == mes_atual and ano_selecionado == ano_atual:
                data_ref = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
                data_ref = (data_ref - timedelta(days=1)).replace(day=1)
                mes_final = data_ref.month
                ano_final = data_ref.year 
            elif dia_hoje != 1 and indice_mes_referencia == mes_atual and ano_selecionado == ano_atual:
                data_ref = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
                mes_final = data_ref.month
                ano_final = data_ref.year
            else:
                mes_final = indice_mes_referencia
                ano_final = ano_selecionado

            mes_referencia = [mes_referencia]
            mes_selecionado = mes_referencia[0]
            # Fim sidebar

            # Início cabeçalho
            left_co, cent_co, last_co = st.columns(3)
            with cent_co:
                st.image('logoatos.png', width=500)
            st.write(f"# Dashboard de venda da {filial_selecionada}")
            # Fim cabeçalho

            total_vendas = consultaSQL.obter_vendas_ano_anterior_mes_anterior(filial_selecionada, mes_final, ano_final - 1)
            meta_mes = consultaSQL.obter_meta_mes_anterior(filial_selecionada, mes_final, ano_final)
            vendas_mes_atual = consultaSQL.obter_vendas_mes_anterior(filial_selecionada, mes_final, ano_selecionado)
            percentual_crescimento_meta = consultaSQL.obter_percentual_crescimento_meta_mes_anterior(filial_selecionada)
            vendas_mensais = consultaSQL.obter_vendas_anual_e_filial_mes_anterior(filial_selecionada, mes=mes_final, ano=ano_final)

            def calcular_percentual_crescimento(vendas_mes_atual, total_vendas):
                if total_vendas and total_vendas > 0:
                    percentual = ((vendas_mes_atual / total_vendas) - Decimal("1")) * Decimal("100")
                    return percentual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    return Decimal("0.00")
            percentual_crescimento = calcular_percentual_crescimento(vendas_mes_atual, total_vendas)

            def calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes):
                if meta_mes and meta_mes > 0:
                    percentual = ((vendas_mes_atual / meta_mes) - Decimal("1")) * Decimal("100")
                    return percentual.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    return Decimal("0.00")
            percentual_crescimento_meta = calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes)

            @st.cache_data
            def grafico_de_barras_mes_anterior(meta_mes, vendas_ano, vendas_mes_atual):
                def safe_float(value):
                    if value is None:
                        return 0.0
                    try:
                        return float(value)
                    except (ValueError, TypeError):
                        return 0.0

                meta_mes = safe_float(meta_mes)
                vendas_ano = safe_float(vendas_ano)
                vendas_mes_atual = safe_float(vendas_mes_atual)

                categorias = ["Vendas ano anterior", "Meta do mês", f"Vendas de {mes_selecionado}"]
                valores = [vendas_ano, meta_mes, vendas_mes_atual]
                cores = ["darkgray", "darkblue", "darkred"]
                textos_formatados = [f'R$ {v:,.2f}'.replace(",", "X").replace(".", ",").replace("X", ".") for v in valores]

                fig = go.Figure()

                fig.add_trace(go.Bar(
                    x=categorias,
                    y=valores,
                    marker_color=cores,
                    text=textos_formatados,
                    textposition='outside',
                    hovertemplate=[
                        f'{cat}, {txt}<extra></extra>' for cat, txt in zip(categorias, textos_formatados)
                    ]
                ))

                fig.update_layout(
                    title=f"📊 Mês: {mes_selecionado}",
                    xaxis_title="",
                    yaxis_title="Valor (R$)",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=550,
                    width=500,
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True,
                        tickformat=",."
                    )
                )
                return fig

            @st.cache_data 
            def grafico_de_crescimento_mes(vendas_mes_atual, total_vendas, meta_mes):
                try:
                    percentual_crescimento = float(calcular_percentual_crescimento(vendas_mes_atual, total_vendas))
                except (ValueError, TypeError):
                    percentual_crescimento = 0.0

                try:
                    percentual_crescimento_meta = float(calcular_percentual_crescimento_meta(vendas_mes_atual, meta_mes))
                except (ValueError, TypeError):
                    percentual_crescimento_meta = 0.0
                    
                fig = go.Figure()

                categorias = ["Cresc. Mês", "Cresc. meta"]
                valores = [percentual_crescimento, percentual_crescimento_meta]
                cores = ["green", "aqua"]
                
                texto_formatado = [lc.format_string('%.2f', v, grouping=True) + "%" for v in valores]
                hover_texto = [f"{cat}: {lc.format_string('%.2f', v, grouping=True)}%" for cat, v in zip(categorias, valores)]

                fig.add_trace(go.Bar(
                    x=categorias,
                    y=valores,
                    marker_color=cores,
                    text=texto_formatado,
                    textposition='outside',
                    hovertext=hover_texto,
                    hoverinfo='text'
                ))
                
                y_min = min(valores)
                y_max = max(valores)
                y_range_margin = (y_max - y_min) * 0.3

                fig.update_layout(
                    title="% Crescimento",
                    xaxis_title="",
                    yaxis_title="Valor %",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    height=450, 
                    width=450,
                    margin=dict(t=100, b=50, l=50, r=50),
                    yaxis=dict(
                        range=[y_min - y_range_margin, y_max + y_range_margin],
                        zeroline=True,
                        zerolinecolor='gray'
                    )
                )
                return fig

            @st.cache_data
            def grafico_linhas_por_filial(mes_referencia, filial_selecionada, ano_selecionado):
                vendas = consultaSQL.obter_vendas_por_mes_e_filial_mes_anterior(mes_referencia, filial_selecionada, ano_selecionado)

                if not vendas:
                    st.warning("Nenhuma venda encontrada para os filtros selecionados.")
                    return

                valores = [float(v[0]) if isinstance(v[0], Decimal) else v[0] for v in vendas]
                datas = [v[1] for v in vendas]
                meses = [v[2] for v in vendas]
                anos = [v[3] for v in vendas]

                df_vendas = pd.DataFrame({
                    "Data": pd.to_datetime(datas),
                    "Valor": valores,
                    "Mês": [str(m) for m in meses],
                    "Ano": [str(a) for a in anos]
                })

                df_vendas["Dia"] = df_vendas["Data"].dt.day 
                df_vendas["Valor_formatado"] = df_vendas["Valor"].apply(lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                df_vendas["MesAno"] = df_vendas["Mês"] + "/" + df_vendas["Ano"]

                fig = go.Figure()

                for mesano in df_vendas["MesAno"].unique():
                    df_mesano = df_vendas[df_vendas["MesAno"] == mesano]

                    fig.add_trace(go.Scatter(
                        x=df_mesano["Dia"], 
                        y=df_mesano["Valor"],
                        mode='lines+markers',
                        name=mesano,
                        hovertemplate='Dia %{x}<br>Valor: %{customdata}<extra></extra>',
                        customdata=df_mesano["Valor_formatado"]
                    ))

                fig.update_layout(
                    title=f"📈 Vendas comparadas {mes_referencia[0]} - {filial_selecionada}",
                    xaxis_title="Dia do Mês",
                    yaxis_title="Vendas (R$)",
                    template="plotly_white",
                    showlegend=True,
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True, 
                        tickformat=",."
                    )
                )

                return fig

            def grafico_de_evolucao_vendas_mes_anterior(vendas_mensais, filial, ano):
                df_vendas = pd.DataFrame(list(vendas_mensais.items()), columns=['Mês', 'Vendas'])
                df_vendas['Mês'] = pd.to_datetime(df_vendas['Mês'], format='%m/%Y')
                df_vendas = df_vendas.sort_values("Mês")

                fig = go.Figure()

                df_vendas["Valor_formatado"] = df_vendas["Vendas"].apply(lambda y: f"R$ {y:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))

                fig.add_trace(go.Scatter(
                    x=df_vendas["Mês"].dt.strftime('%m/%Y'),
                    y=df_vendas["Vendas"],
                    mode='lines+markers',
                    name="Vendas",
                    hovertemplate='Mês %{x}<br>Valor: %{customdata}<extra></extra>',
                    customdata=df_vendas["Valor_formatado"]
                ))

                fig.update_layout(
                    title=f"📊 Vendas - Evolução até {mes_final:02d}/{ano} - {filial}",
                    xaxis_title="Meses",
                    yaxis_title="Valor das Vendas (R$)",
                    font=dict(color="lightgray", size=14),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    yaxis_tickformat="R$ ,.2f",
                    template="plotly_white",
                    yaxis=dict(
                        tickprefix="R$ ",
                        separatethousands=True,
                        tickformat=",."
                    )
                )
                return fig

            # Exibição:
            col1, col2, col3 = st.columns(3)

            exibindo_grafico_de_barras = grafico_de_barras_mes_anterior(meta_mes, total_vendas, vendas_mes_atual)
            st.plotly_chart(exibindo_grafico_de_barras, use_container_width=True)

            st.divider()

            exibindo_grafico_de_crescimento = grafico_de_crescimento_mes(vendas_mes_atual, total_vendas, meta_mes)
            st.sidebar.plotly_chart(exibindo_grafico_de_crescimento)

            exibindo_grafico_de_linhas_vendas_por_mes = grafico_linhas_por_filial(mes_referencia, filial_selecionada, ano_selecionado)
            st.write(exibindo_grafico_de_linhas_vendas_por_mes)

            exibindo_grafico_acompanhamanto_mensal = grafico_de_evolucao_vendas_mes_anterior(vendas_mensais, filial_selecionada, ano_selecionado)
            st.write(exibindo_grafico_acompanhamanto_mensal)

        pagina_meses_anterior()

    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.session_state.page = None
        st.rerun()

#Página relatório 
def paginarelatoriocompleto():
    verificar_autenticacao()
    
    st.set_page_config(page_title="Relatório de Vendas", page_icon="📈", layout="wide") 
    st.markdown("""
    <style>
    [data-testid="stSidebar"] {
        background-color: #800000; 
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <style>
        section[data-testid="stSidebar"] button {
            width: 100% !important;
            height: 40px !important;
            margin-bottom: 10px;
            background-color: #1C1C1C;
            color: white;
            font-weight: bold;
            border-radius: 8px;
            border: none;
            transition: background-color 0.3s ease;
        }

        section[data-testid="stSidebar"] button:hover {
            background-color: darkblue;
        }
        </style>
    """, unsafe_allow_html=True)

    def formatar_brasileiro(valor):
        try:
            return format_currency(valor, 'BRL', locale='pt_BR')
        except:
            return "R$ 0,00"

    def safe_percent(value):
        try:
            if value is None:
                return 0.0
            if isinstance(value, str) and '%' in value:
                value = value.replace('%', '')
            value = float(value)
            if value == float("inf") or value == float("-inf") or pd.isna(value):
                return 0.0
            return value
        except (ZeroDivisionError, ValueError, TypeError):
            return 0.0

    def valor_para_float(valor_str):
        try:
            if isinstance(valor_str, str):
                valor_str = valor_str.replace('R$ ', '').strip()
                valor_str = re.sub(r'\.(?=\d{3}(?:[.,]))', '', valor_str)  
                valor_str = valor_str.replace(',', '.')
            return float(valor_str)
        except:
            return 0.0

    def obter_dados_relatorio(data_selecionada):
        df = consultaSQL.obter_relatorio_vendas(data_selecionada)
        
        if df is None:
            st.error("Erro ao obter dados do relatório. Verifique a conexão com o banco de dados.")
            return pd.DataFrame()
        
        df = df.rename(columns={
            'nmFilial': 'FILIAL',
            'vendas_2024': 'VENDAS 2024',
            'meta_mes': 'META MÊS',
            'previsao_vendas': 'PREVISÃO',
            'acumulo_2024': 'ACUM. 2024',
            'acumulo_meta': 'ACUM. META',
            'acumulado_vendas': 'ACUM. VENDAS',
            'ultima_venda_valor': 'VENDAS DO DIA',
            'crescimento_vs_ano_anterior': 'CRESC. 2025',
            'crescimento_vs_meta': 'CRESC. META'
        })
        
        for col in df.columns:
            if col != 'FILIAL':
                if 'CRESC' in col:
                    df[col] = df[col].astype(str).str.replace('%', '').str.replace(',', '.').astype(float)
                else:
                    df[col] = df[col].apply(valor_para_float)
        
        return df

    def exportar_para_excel(df, data_venda):
        data_formatada = data_ultima_venda.strftime('%d-%m')
        nome_arquivo = f"Relatorio_de_Venda_{data_formatada}.xlsx"
        with pd.ExcelWriter(nome_arquivo, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Relatório', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Relatório']
            formato_percentual = workbook.add_format({'num_format': '#,##0.00"%"', 'align': 'center'})
            formato_percentual_neg = workbook.add_format({'num_format': '#,##0.00"%"', 'align': 'center', 'font_color': 'red'})
            formato_moeda = workbook.add_format({'num_format': '#,##0.00', 'align': 'right'})
            formato_titulo = workbook.add_format({'bold': True, 'bg_color': '#D3D3D3', 'align': 'center'})
            worksheet.set_row(0, None, formato_titulo)
            for col_num, col_name in enumerate(df.columns):
                if "CRESC" in col_name:
                    for row_num in range(1, len(df) + 1):
                        valor = df.iloc[row_num - 1, col_num]
                        formato = formato_percentual_neg if valor < 0 else formato_percentual
                        worksheet.write_number(row_num, col_num, valor, formato)
                elif col_name != "FILIAL":
                    for row_num in range(1, len(df) + 1):
                        worksheet.write_number(row_num, col_num, df.iloc[row_num - 1, col_num], formato_moeda)
                else:
                    worksheet.set_column(col_num, col_num, 25)
        return nome_arquivo

    def gerar_pdf(df, data_venda):
        data_atual = datetime.now()
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.set_font("Courier", "B", 12)
        pdf.cell(0, 10, f"Relatório de vendas emitido em - {data_atual.strftime('%d/%m/%Y')}", ln=True, align="C")
        data_exibida = data_venda - pd.Timedelta(days=1)
        pdf.set_font("Courier", "", 10)
        pdf.cell(0, 10, f"Relatório referente às vendas do dia - {data_formatada}", ln=True, align="C")
        pdf.set_font("Courier", "B", 8)
        colunas = list(df.columns)
        larguras = [35, 27, 27, 27, 27, 27, 27, 27, 22, 22]
        for i, col in enumerate(colunas):
            pdf.cell(larguras[i], 7, col[:18], border=1, align='C')
        pdf.ln()
        pdf.set_font("Courier", "", 7)
        for _, row in df.iterrows():
            for i, col in enumerate(colunas):
                valor = row[col]
                if "CRESC" in col:
                    valor_formatado = f"{valor:,.2f}".replace(",", "v").replace(".", ",").replace("v", ".") + "%"
                    if valor < 0:
                        valor_formatado = f"-{valor_formatado.replace('-', '')}"
                elif col == "FILIAL":
                    valor_formatado = str(valor)[:22]
                else:
                    valor_formatado = formatar_brasileiro(valor)
                pdf.cell(larguras[i], 6, valor_formatado[:22], border=1, align='C')
            pdf.ln()
        nome_pdf = f"Relatorio_de_Venda_{data_ultima_venda.strftime('%d-%m-%Y')}.pdf"
        pdf.output(nome_pdf)
        return nome_pdf

    def formatar_dataframe_para_exibicao(df):
        df_formatado = df.copy()
        for col in df.columns:
            if "CRESC" in col:
                df_formatado[col] = df[col].map(lambda x: f"{x:,.2f}%".replace(",", "v").replace(".", ",").replace("v", "."))
            elif col != "FILIAL":
                df_formatado[col] = df[col].map(formatar_brasileiro)
        return df_formatado

    # Sidebar com seleção de data
    with st.sidebar:
        st.header("Menu")
        
        data_default = date.today()
        
        if 'data_selecionada' in st.session_state:
            data_default = st.session_state.data_selecionada
        
        data_selecionada = st.date_input(
            "Selecione a data:",
            value=data_default,
            max_value=date.today(),
            format="DD/MM/YYYY"
        ) 
        
        st.session_state.data_selecionada = data_selecionada
        
        if st.button("Voltar Para Mês Atual"):
            st.session_state['dashboard_page'] = 'paginaatos'
            st.rerun()
        if st.button("🚪 Sair"):    
            st.session_state.authenticated = False
            st.session_state.page = None
            st.rerun()

    # Obtém os dados usando o módulo importar
    df = obter_dados_relatorio(data_selecionada)

    data_atual = datetime.now()

    left_co, cent_co, last_co = st.columns(3) 
    with cent_co:
        st.image('logoatos.png', width=500)

    st.markdown(
        f"<h2 style='text-align: center;'>📈 Relatório de vendas emitido em - {data_atual.strftime('%d/%m/%Y')}</h2>",
        unsafe_allow_html=True
    )

    df = obter_dados_relatorio(data_selecionada)

    data_ultima_venda = consultaSQL.obter_data_ultima_venda(data_selecionada)

    data_formatada = data_ultima_venda.strftime('%d/%m/%Y') if data_ultima_venda is not None else "N/D"

    st.markdown(f"<h3> Relatório referente às vendas do dia - {data_formatada}</h3>", unsafe_allow_html=True)

    if not df.empty:
        df_formatado = formatar_dataframe_para_exibicao(df)
        st.dataframe(df_formatado.set_index(pd.Index(range(1, len(df_formatado) + 1))), use_container_width=True, height=635)

        espaco1, col_botoes, espaco2 = st.columns([1, 2, 1])
        with col_botoes:
            col_excel, col_pdf = st.columns([1, 1])
            with col_excel:
                if st.button("📊 Gerar Excel"):
                    arquivo_excel = exportar_para_excel(df, data_selecionada)
                    st.success("✅ Excel gerado com sucesso.")
                    with open(arquivo_excel, "rb") as f:
                        st.download_button("⬇️ Baixar Excel", f, file_name=arquivo_excel, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
                    os.remove(arquivo_excel)
            with col_pdf:
                if st.button("📄 Gerar PDF"):
                    arquivo_pdf = gerar_pdf(df, data_selecionada)
                    st.success("✅ PDF gerado com sucesso.")
                    with open(arquivo_pdf, "rb") as f:
                        st.download_button("⬇️ Baixar PDF", f, file_name=arquivo_pdf, mime="application/pdf")
                    os.remove(arquivo_pdf)
    else:
        st.warning("Nenhum dado encontrado para a data selecionada.")

    #pagina Agente IA

#Página IA 
def paginaagenteia():
    verificar_autenticacao()
    
    st.set_page_config(
    page_title="Assistente Atos Capital",
    page_icon="🤖",
    layout="wide"
    )

    st.markdown("""
    <style>
        .message-container {
            display: flex;
            margin-bottom: 12px;
        }
        .user-message {
            background-color: #DCF8C6;
            color: #000;
            border-radius: 15px 15px 0 15px;
            padding: 10px 15px;
            margin-left: auto;
            max-width: 70%;
            box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        }
        .assistant-message {
            background-color: #ECE5DD;
            color: #000;
            border-radius: 15px 15px 15px 0;
            padding: 10px 15px;
            margin-right: auto;
            max-width: 70%;
            box-shadow: 0 1px 1px rgba(0,0,0,0.1);
        }
        .sender-name {
            font-size: 0.8em;
            font-weight: bold;
            margin-bottom: 3px;
        }
        .chat-input {
            position: fixed;
            bottom: 20px;
            width: 80%;
        }
        .loading-dots {
            display: inline-block;
        }
        .loading-dots:after {
            content: ' .';
            animation: dots 1.5s steps(5, end) infinite;
        }
        a {
            color: #0066cc;
            text-decoration: underline;
        }
        [data-testid="stSidebar"] {
            background-color: #800000; 
        }
        .cover-glow {
            width: 80%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #a8d8ff,
                0 0 10px #7ac4ff,
                0 0 15px #4db0ff,
                0 0 20px #1e9cff,
                0 0 25px #0088ff,
                0 0 30px #0077dd,
                0 0 35px #0066bb;
            position: relative;
            z-index: -1;
            border-radius: 45px;
            display: block;       
            margin: 0 auto;
        }
        @keyframes dots {
            0%, 20% {
                color: rgba(0,0,0,0);
                text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0);
            }
            40% {
                color: black;
                text-shadow: .25em 0 0 rgba(0,0,0,0), .5em 0 0 rgba(0,0,0,0);
            }
            60% {
                text-shadow: .25em 0 0 black, .5em 0 0 rgba(0,0,0,0);
            }
            80%, 100% {
                text-shadow: .25em 0 0 black, .5em 0 0 black;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    # Função para converter URLs em links clicáveis
    def url_to_link(text):
        url_pattern = re.compile(r'https?://\S+|www\.\S+')
        
        def replace_with_link(match):
            url = match.group(0)
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            return f'<a href="{url}" target="_blank">{url}</a>'
        
        return url_pattern.sub(replace_with_link, text)

    # Função para converter imagem para base64
    def img_to_base64(img_path):
        with open(img_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')

    # Título da aplicação
    left_co, cent_co, last_co = st.columns(3)
    with cent_co:
        st.image('logoatos.png', width=500)
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {
            background-color: #800000; 
        }
        </style>
        """, unsafe_allow_html=True)

    st.header("💬 Conversando com Theo")

    # Inicialização do histórico
    if 'historico' not in st.session_state:
        st.session_state.historico = []
    if 'aguardando_resposta' not in st.session_state:
        st.session_state.aguardando_resposta = False  

    # Sidebar - Imagem com efeito glow
    img_path = "logoia.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )

    # Sidebar - Nome
    st.sidebar.markdown("<div style='margin-top: 20px; text-align: center; color: #F8F8FF; font-size: 30px; font-weight: bold; margin-bottom: 20px;'>🤖 Theo Agente IA</div>", unsafe_allow_html=True)
    
    # Função para enviar ao webhook
    def enviar_para_webhook(mensagem):
        try:
            response = requests.post(
                "https://n8n-n8n.zofbat.easypanel.host/webhook/pergunta-whatsapp",
                headers={"Content-Type": "application/json"},
                data=json.dumps({"pergunta": mensagem}),
                timeout=300
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Erro ao conectar com o webhook: {str(e)}")
            return None

    # Exibir histórico de mensagens
    for mensagem in st.session_state.historico:
        conteudo = url_to_link(mensagem['conteudo']) if isinstance(mensagem['conteudo'], str) else str(mensagem['conteudo'])
        
        if mensagem["autor"] == "Atos Capital IA":
            st.markdown(f"""
            <div class="message-container">
                <div class="assistant-message">
                    <div class="sender-name">Atos Capital IA</div>
                    {conteudo}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="message-container">
                <div class="user-message">
                    <div class="sender-name">Você</div>
                    {conteudo}
                </div>
            </div>
            """, unsafe_allow_html=True)

    # Input do usuário
    if prompt := st.chat_input("Digite sua mensagem...", disabled=st.session_state.aguardando_resposta):
        st.session_state.historico.append({
            "autor": "Usuário",
            "conteudo": prompt
        })
        
        st.session_state.historico.append({
            "autor": "Atos Capital IA",
            "conteudo": "<div class='loading-dots'>Processando sua resposta, aguarde</div>",
            "loading": True
        })
        
        st.session_state.aguardando_resposta = True
        st.rerun()

    # Processamento da resposta
    if st.session_state.aguardando_resposta:
        ultima_mensagem_usuario = next(
            (msg for msg in reversed(st.session_state.historico) if msg["autor"] == "Usuário"),
            None
        )
        
        if ultima_mensagem_usuario:
            resposta_webhook = enviar_para_webhook(ultima_mensagem_usuario["conteudo"])
            
            st.session_state.historico = [msg for msg in st.session_state.historico if not msg.get("loading")]
            
            if resposta_webhook:
                resposta = resposta_webhook.get("resposta") or resposta_webhook.get("output") or resposta_webhook.get("message") or str(resposta_webhook)
                st.session_state.historico.append({
                    "autor": "Atos Capital IA",
                    "conteudo": resposta
                })
            else:
                st.session_state.historico.append({
                    "autor": "Atos Capital IA",
                    "conteudo": "Desculpe, não consegui processar sua solicitação no momento, envie a pergunta novamente."
                })
        
        st.session_state.aguardando_resposta = False
        st.rerun()

    st.markdown("""
    <style>
    /* Estilizar todos os botões da sidebar */
    section[data-testid="stSidebar"] button {
        width: 100% !important;
        height: 40px !important;
        margin-bottom: 10px;
        background-color: #1C1C1C;
        color: white;
        font-weight: bold;
        border-radius: 8px;
        border: none;
        transition: background-color 0.3s ease;
    }

    /* Hover nos botões */
    section[data-testid="stSidebar"] button:hover {
        background-color: darkblue;
    }
    </style>
    """, unsafe_allow_html=True)

    if st.sidebar.button("Voltar Para Mês Atual"):
        st.session_state['dashboard_page'] = 'paginaatos'
        st.rerun()
        
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.session_state.page = None
        st.rerun()

# PÁGINA UNIT

def paginaunit():
    verificar_autenticacao()
    
    # Configuração da página
    st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
    
    # Barra lateral
    if 'user_info' in st.session_state:
        st.sidebar.subheader("Informações do Usuário")
        st.sidebar.write(f"👤 Nome: {st.session_state.user_info['nome']}")
        st.sidebar.write(f"🔑 Permissão: {st.session_state.user_info['permissao']}")
        
        # Adicionar botão Voltar apenas para administradores
        if st.session_state.user_info['permissao'].lower() == 'adm':
            if st.sidebar.button("⬅️ Voltar para Administração"):
                st.session_state.page = 'adm'
                st.rerun()
    
    # Botão sair da conta
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.session_state.page = None
        st.rerun()
    
    # Nome Principal Pagina
    st.title("📊 TESTE")
    
    # Mensagem boas vindas com nome cadastrado na conta
    if 'user_info' in st.session_state:
        st.write(f"Bem-vindo, {st.session_state.user_info['nome']}!")

# PÁGINA RESIDENCIA

def paginaresidencia():
    verificar_autenticacao()
    
    # Configuração da página
    st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")
    
    # Barra lateral
    if 'user_info' in st.session_state:
        st.sidebar.subheader("Informações do Usuário")
        st.sidebar.write(f"👤 Nome: {st.session_state.user_info['nome']}")
        st.sidebar.write(f"🔑 Permissão: {st.session_state.user_info['permissao']}")
        
        # Adicionar botão Voltar apenas para administradores
        if st.session_state.user_info['permissao'].lower() == 'adm':
            if st.sidebar.button("⬅️ Voltar para Administração"):
                st.session_state.page = 'adm'
                st.rerun()
    
    # Botão sair da conta
    if st.sidebar.button("🚪 Sair"):
        st.session_state.authenticated = False
        st.session_state.page = None
        st.rerun()
    
    # Nome Principal Pagina
    st.title("📊 Residencia")
    
    # Mensagem boas vindas com nome cadastrado na conta
    if 'user_info' in st.session_state:
        st.write(f"Bem-vindo, {st.session_state.user_info['nome']}!")

# PÁGINA NOVA ADICIONAR....

# SISTEMA DINÂMICO DE ROTEAMENTO

def encontrar_paginas():
    """Lista todas as funções pagina* disponíveis"""
    return [name for name, func in getmembers(sys.modules[__name__]) 
             if name.startswith('pagina') and isfunction(func)]

def main():
    # Pega o nome da página da session_state
    nome_pagina = st.session_state.get('dashboard_page', 'pagina_nao_encontrada')
    
    # Verifica se a função existe
    if nome_pagina in globals() and callable(globals()[nome_pagina]):
        globals()[nome_pagina]()
    else:
        pagina_nao_encontrada()

if __name__ == "__main__":
    main()
