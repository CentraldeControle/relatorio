import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

import os

st.set_page_config(
    layout="wide"
)

# Função para pré-processamento
def preprocess_data(data):
    # Corrigir o tipo de dado para datetime
    data['Data Filiação'] = pd.to_datetime(data['Data Filiação'], errors='coerce')
    # Remover linhas com datas inválidas
    data = data.dropna(subset=['Data Filiação'])
    # Converter datas para string no formato 'YYYY-MM-DD'
    data['Data Filiação'] = data['Data Filiação'].dt.strftime('%Y-%m-%d')
    # Adicionar coluna de quantidade com valor 1
    data['quantidade'] = 1
    # Agrupar por data de Filiação e franquia e calcular a contagem
    data = data.groupby(['Data Filiação','Franquia','Promotor de Vendas']).size().reset_index(name='quantidade')
    
    return data

def main():
    st.markdown("<h1 style='text-align: center;'>CDT</h1>", unsafe_allow_html=True)

    # List all Excel files in the current directory
    # List all Excel files in the current directory
    excel_files = [f for f in os.listdir('.') if f.endswith('.xlsx')]

    # Initialize an error message and data frames list
    error_message = ""
    data_frames = []

    if len(excel_files) < 3:
        error_message = 'Menos de três arquivos Excel encontrados na pasta.'
    else:
        # Sort the files by modification time, descending
        sorted_files = sorted(excel_files, key=lambda x: os.path.getmtime(x), reverse=True)
        # Select the three most recent Excel files
        selected_files = sorted_files[:3]

        # Read data from each selected Excel file
        for file_path in selected_files:
            try:
                # Read each Excel file into a DataFrame
                df = pd.read_excel(file_path)
                data_frames.append(df)
            except Exception as e:
                error_message = f"Failed to read {file_path}: {str(e)}"

    # Comment out to prevent execution
    # st.write(selected_files)
    # for df in data_frames:
    #     print(df.head())  # Display the first few rows of each DataFrame
    # print(error_message) if error_message else None

    if selected_files is not None:
        # Ler o arquivo Excel
        df = pd.read_excel("data.xlsx", header=0)
        
        # Pré-processamento dos dados
        processed_data = preprocess_data(df)
        
        
        # Adicionando o código de projeção
        processed_data['Data Filiação'] = pd.to_datetime(processed_data['Data Filiação'])
        processed_data['mes'] = processed_data['Data Filiação'].dt.month

        df_projec = processed_data.copy()
        
        # Convertendo a coluna 'Data Filiação' para o tipo datetime
        df_projec['Data Filiação'] = pd.to_datetime(df_projec['Data Filiação'])
        
        # Extraindo o mês da coluna 'Data Filiação' e criando uma nova coluna 'Mês'
  # Mapeando os números dos meses para os nomes em português
        meses_pt_br = {
            1: 'Janeiro',
            2: 'Fevereiro',
            3: 'Março',
            4: 'Abril',
            5: 'Maio',
            6: 'Junho',
            7: 'Julho',
            8: 'Agosto',
            9: 'Setembro',
            10: 'Outubro',
            11: 'Novembro',
            12: 'Dezembro'
        }
        
        # Calculando o primeiro dia do mês atual
        hoje = datetime.datetime.now().replace(day=1)

        # Calculando o primeiro dia do mês 3 meses atrás
        cinco_meses_atras = hoje - relativedelta(months=2)

        # Filtrar os dados para incluir apenas os últimos 3 meses completos
        df_ultimos_cinco_meses = df_projec[df_projec['Data Filiação'] >= cinco_meses_atras]

        # Adicionando a coluna 'Mês' com os nomes em português
        df_ultimos_cinco_meses['Mês'] = df_ultimos_cinco_meses['Data Filiação'].dt.month.map(meses_pt_br)

        # Agrupando os dados por franquia e mês, somando a quantidade para cada grupo
        dados_agrupados = df_ultimos_cinco_meses.groupby(['Franquia', 'Mês'])['quantidade'].sum().reset_index()

        # Definindo a ordem dos meses
        meses_ordem = [
            'Janeiro',
            'Fevereiro',
            'Março',
            'Abril',
            'Maio',
            'Junho',
            'Julho',
            'Agosto',
            'Setembro',
            'Outubro',
            'Novembro',
            'Dezembro'
        ]

        # Convertendo a coluna 'Mês' para o tipo categoria com a ordem definida
        dados_agrupados['Mês'] = pd.Categorical(dados_agrupados['Mês'], categories=meses_ordem, ordered=True)

        # Ordenando os dados pela ordem definida
        dados_agrupados = dados_agrupados.sort_values(by='Mês')

        # Definindo uma paleta de cores
        cores = ['#007bff', '#ffc107', '#28a745', '#17a2b8', '#ffc885']

        # Função para criar o gráfico
        def plotar_grafico(franquias_selecionadas):
            if not franquias_selecionadas:
                st.write(" ")
            else:
                # Ordenando as franquias selecionadas em ordem alfabética
                franquias_selecionadas.sort()

                cor_iter = iter(cores * (len(franquias_selecionadas) // len(cores) + 1))

                traces = []
                for franquia in franquias_selecionadas:
                    dados_franquia = dados_agrupados[dados_agrupados['Franquia'] == franquia]
                    trace = go.Bar(
                        x=dados_franquia['Mês'],
                        y=dados_franquia['quantidade'],
                        name=franquia,
                        hoverinfo='x+y',
                        text=dados_franquia['quantidade'],
                        textposition='outside',
                        marker=dict(color=next(cor_iter))
                    )
                    traces.append(trace)

                # Criando o layout do gráfico
                layout = go.Layout(
                    title='Vendas de cada franquia nos últimos 3 meses completos',
                    xaxis=dict(title='Mês'),
                    yaxis=dict(title='Quantidade'),
                )

                # Criando a figura
                fig = go.Figure(data=traces, layout=layout)
                fig.update_layout(showlegend=True, yaxis=dict(range=[0, dados_agrupados['quantidade'].max() * 1.15]))

                # Exibindo o gráfico
                st.plotly_chart(fig, use_container_width=True, config={
                    'displayModeBar': False,
                    'displaylogo': False
                })

        # Lista de franquias disponíveis
        franquias_disponiveis = dados_agrupados['Franquia'].unique()

        # Checkbox para selecionar as franquias
        franquias_selecionadas = st.sidebar.multiselect('Selecione as franquias para visualizar as vendas nos últimos 3 meses completos', franquias_disponiveis, default=franquias_disponiveis)

        plotar_grafico(franquias_selecionadas)


if __name__ == "__main__":
    main()
