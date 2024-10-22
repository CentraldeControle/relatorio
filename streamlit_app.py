import streamlit as st
import pandas as pd
import datetime
import plotly.graph_objs as go

st.set_page_config(layout="wide")

# Função para pré-processamento
def preprocess_data(data):
    # Corrigir o tipo de dado para datetime
    data['Data Filiação'] = pd.to_datetime(data['Data Filiação'], errors='coerce')
    # Remover linhas com datas inválidas
    data = data.dropna(subset=['Data Filiação'])
    # Adicionar coluna de quantidade com valor 1
    data['quantidade'] = 1
    # Agrupar por data de Filiação e franquia e somar as quantidades
    data = data.groupby(['Data Filiação', 'Franquia']).agg({'quantidade': 'sum'}).reset_index()
    
    return data

# Função para gerar gráfico
def plotar_grafico(dados_agrupados, titulo):
    cores = ['#007bff', '#ffc107', '#28a745', '#17a2b8', '#ffc885']
    
    traces = []
    franquias_selecionadas = dados_agrupados['Franquia'].unique()
    
    for i, franquia in enumerate(franquias_selecionadas):
        dados_franquia = dados_agrupados[dados_agrupados['Franquia'] == franquia]
        trace = go.Bar(
            x=dados_franquia['Data Filiação'],
            y=dados_franquia['quantidade'],
            name=franquia,
            hoverinfo='x+y',
            marker=dict(color=cores[i % len(cores)]),
            text=dados_franquia['quantidade'],  # Exibe os valores acima das barras
            textposition='outside'
        )
        traces.append(trace)

    layout = go.Layout(
        title=titulo,
        xaxis=dict(title='Data'),
        yaxis=dict(title='Quantidade'),
    )

    # Criando a figura
    fig = go.Figure(data=traces, layout=layout)
    fig.update_layout(showlegend=True, yaxis=dict(range=[0, dados_agrupados['quantidade'].max() * 1.15]))
    
    st.plotly_chart(fig, use_container_width=True, config={
        'displayModeBar': False,
        'displaylogo': False
    })

# Função para gerar relatório detalhado de comparação entre semanas
def gerar_relatorio_comparacao(dados_semana_1, dados_semana_2):
    # Agrupar por franquia e somar as quantidades para cada semana
    resumo_semana_1 = dados_semana_1.groupby('Franquia')['quantidade'].sum().reset_index().rename(columns={'quantidade': 'Total Semana 1'})
    resumo_semana_2 = dados_semana_2.groupby('Franquia')['quantidade'].sum().reset_index().rename(columns={'quantidade': 'Total Semana 2'})
    
    # Unir os dados das duas semanas
    comparacao = pd.merge(resumo_semana_1, resumo_semana_2, on='Franquia', how='outer').fillna(0)
    
    # Calcular a diferença em termos absolutos e percentuais
    comparacao['Diferença Absoluta'] = comparacao['Total Semana 2'] - comparacao['Total Semana 1']
    comparacao['Variação Percentual'] = ((comparacao['Total Semana 2'] - comparacao['Total Semana 1']) / 
                                         comparacao['Total Semana 1'].replace(0, 1)) * 100
    
    # Classificação por total de vendas em cada semana
    comparacao = comparacao.sort_values(by='Total Semana 2', ascending=False)

    col5, col6 = st.columns(2)
    with col5:
    # Exibir o relatório
        st.markdown("### Relatório de Comparação entre as Semanas por Franquia")
        st.write(comparacao)
    
    # Exibir algumas análises
    total_semana_1 = comparacao['Total Semana 1'].sum()
    total_semana_2 = comparacao['Total Semana 2'].sum()
    st.markdown(f"**Total de vendas na Semana 1:** {int(total_semana_1)}")
    st.markdown(f"**Total de vendas na Semana 2:** {int(total_semana_2)}")
    
    if total_semana_1 > 0:
        variacao_total = ((total_semana_2 - total_semana_1) / total_semana_1) * 100
        st.markdown(f"**Variação percentual total:** {variacao_total:.2f}%")
    else:
        st.markdown(f"**Variação percentual total:** N/A")
    
    # Exibir ranking das franquias
    with col6:
        st.markdown("### Ranking de Franquias")
        st.write(comparacao[['Franquia', 'Total Semana 1', 'Total Semana 2', 'Diferença Absoluta', 'Variação Percentual']])

def main():
    st.markdown("<h1 style='text-align: center;'>CDT - Comparação Semanal</h1>", unsafe_allow_html=True)

    # Carregar um arquivo Excel
    uploaded_file = st.file_uploader("Carregue um arquivo Excel", type=["xlsx"])

    if uploaded_file:
        # Ler o arquivo Excel
        df = pd.read_excel(uploaded_file)
        
        # Pré-processamento dos dados
        processed_data = preprocess_data(df)
        
        # Convertendo a coluna 'Data Filiação' para o tipo datetime
        processed_data['Data Filiação'] = pd.to_datetime(processed_data['Data Filiação'])
        
        # Calcular a data de duas semanas atrás considerando o dia de ontem
        hoje = datetime.datetime.now()
        ontem = hoje - datetime.timedelta(days=1)
        duas_semanas_atras = ontem - datetime.timedelta(weeks=2)
        uma_semana_atras = ontem - datetime.timedelta(weeks=1)
        
        # Filtrar dados das duas últimas semanas a partir de ontem
        dados_semana_1 = processed_data[(processed_data['Data Filiação'] >= duas_semanas_atras) & 
                                        (processed_data['Data Filiação'] < uma_semana_atras)]
        
        dados_semana_2 = processed_data[(processed_data['Data Filiação'] >= uma_semana_atras) & 
                                        (processed_data['Data Filiação'] <= ontem)]
        
        # Exibir gráficos lado a lado
        col3, col4 = st.columns(2)
        with col3:
            plotar_grafico(dados_semana_1, "Vendas na Semana 1 (A partir de Ontem)")
        with col4:
            plotar_grafico(dados_semana_2, "Vendas na Semana 2 (A partir de Ontem)")
        
        # Gerar e exibir o relatório de comparação detalhado
        gerar_relatorio_comparacao(dados_semana_1, dados_semana_2)

if __name__ == "__main__":
    main()
