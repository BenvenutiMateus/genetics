import os
import time

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
import streamlit as st

from src.utils.estabilidade import (
    carregar_metadata,
    listar_iteracoes_disponiveis,
    calcular_q,
    calcular_limite_esperado_v,
    calcular_matriz_estabilidade,
    matriz_para_lista_arestas
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="GRaFo — Stability Selection",
    page_icon="🕸️",
    layout="wide"
)


# ============================================================
# FUNÇÕES COM CACHE
# ============================================================

@st.cache_data
def carregar_info_experimento(
    pasta
):
    """
    Carrega metadata e lista de iterações.
    """

    metadata = carregar_metadata(
        pasta
    )

    iteracoes = (
        listar_iteracoes_disponiveis(
            pasta
        )
    )

    return (
        metadata,
        iteracoes
    )


@st.cache_data
def calcular_estabilidade_cache(
    pasta,
    q,
    ev,
    pi_thr,
    n_iteracoes
):
    """
    Wrapper com cache para evitar recalcular a matriz
    toda vez que algum componente visual é atualizado.
    """

    return calcular_matriz_estabilidade(
        pasta=pasta,

        q=q,

        ev=ev,

        pi_thr=pi_thr,

        n_iteracoes=n_iteracoes,

        mostrar_progresso=False
    )


# ============================================================
# GRAFO
# ============================================================

def criar_grafo(
    matriz_estabilidade,
    pi_thr
):
    """
    Cria o grafo NÃO DIRECIONADO do GRaFo.

    Uma aresta i-j entra quando:

        estabilidade(i,j) >= pi_thr
    """

    G = nx.Graph()

    nos = list(
        matriz_estabilidade.index
    )

    G.add_nodes_from(
        nos
    )

    valores = (
        matriz_estabilidade
        .reindex(
            index=nos,
            columns=nos
        )
        .to_numpy()
    )

    idx_i, idx_j = np.triu_indices(
        len(nos),
        k=1
    )

    for i, j in zip(
        idx_i,
        idx_j
    ):

        peso = valores[
            i,
            j
        ]

        if (
            pd.notna(peso)
            and peso >= pi_thr
        ):

            G.add_edge(
                nos[i],
                nos[j],
                weight=float(peso)
            )

    return G


# ============================================================
# PLOTAR GRAFO
# ============================================================

def plotar_grafo(
    matriz_estabilidade,
    pi_thr,
    manter_isolados=False
):
    """
    Plota o grafo final de Stability Selection.
    """

    G = criar_grafo(
        matriz_estabilidade,
        pi_thr
    )

    # ========================================================
    # REMOVER ISOLADOS
    # ========================================================

    if not manter_isolados:

        isolados = list(
            nx.isolates(G)
        )

        G.remove_nodes_from(
            isolados
        )

    # ========================================================
    # FIGURA
    # ========================================================

    fig, ax = plt.subplots(
        figsize=(15, 15),
        dpi=150
    )

    # ========================================================
    # GRAFO VAZIO
    # ========================================================

    if G.number_of_nodes() == 0:

        ax.text(
            0.5,
            0.5,
            (
                "Nenhuma conexão encontrada\n"
                f"com πthr ≥ {pi_thr:.3f}"
            ),
            ha="center",
            va="center",
            fontsize=16
        )

        ax.axis(
            "off"
        )

        return (
            fig,
            G
        )

    # ========================================================
    # POSIÇÃO
    # ========================================================

    pos = nx.spring_layout(
        G,
        weight="weight",
        k=2,
        iterations=200,
        seed=1
    )

    # ========================================================
    # PESOS
    # ========================================================

    pesos = np.asarray(
        [
            dados["weight"]
            for _, _, dados
            in G.edges(
                data=True
            )
        ],
        dtype=float
    )

    # ========================================================
    # ESPESSURA
    # ========================================================

    if len(pesos) > 0:

        minimo = pesos.min()
        maximo = pesos.max()

        if maximo > minimo:

            espessuras = (
                1
                + 4
                * (
                    (pesos - minimo)
                    /
                    (maximo - minimo)
                )
            )

        else:

            espessuras = (
                np.full(
                    len(pesos),
                    3.0
                )
            )

    else:

        espessuras = 1

    # ========================================================
    # NÓS
    # ========================================================

    nx.draw_networkx_nodes(
        G,
        pos,
        node_size=1000,
        node_color="skyblue",
        edgecolors="black",
        linewidths=1,
        ax=ax
    )

    # ========================================================
    # ARESTAS
    # ========================================================

    nx.draw_networkx_edges(
        G,
        pos,
        width=espessuras,
        edge_color="gray",
        alpha=0.7,
        ax=ax
    )

    # ========================================================
    # LABELS
    # ========================================================

    nx.draw_networkx_labels(
        G,
        pos,
        font_size=9,
        font_weight="bold",
        ax=ax
    )

    # ========================================================
    # LABELS DAS ARESTAS
    # ========================================================

    labels_arestas = {

        (u, v):
            f"{dados['weight']:.2f}"

        for u, v, dados
        in G.edges(
            data=True
        )
    }

    nx.draw_networkx_edge_labels(
        G,
        pos,
        edge_labels=labels_arestas,
        font_size=7,
        ax=ax
    )

    # ========================================================
    # TÍTULO
    # ========================================================

    ax.set_title(
        (
            "Graphical Random Forests — "
            "Stability Selection\n"
            f"πthr = {pi_thr:.3f}"
        ),
        fontsize=16
    )

    ax.axis(
        "off"
    )

    fig.tight_layout()

    return (
        fig,
        G
    )


# ============================================================
# CABEÇALHO
# ============================================================

st.title(
    "🕸️ Graphical Random Forests"
)

st.markdown(
    r"""
    Explorador da **Stability Selection** baseada em
    Fellinghauer et al.

    Para cada subsample:

    1. são calculados os rankings locais das importâncias;
    2. as duas direções de cada par são combinadas;
    3. as arestas recebem um ranking global;
    4. cada aresta recebe seu pior ranking, sendo $\max\{\text{rank}(i \to j), \text{rank}(j \to i)\}$
    5. são selecionadas as **q melhores arestas**;
    6. a frequência de seleção é calculada entre subsamples.
    """
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header(
    "Fonte de dados"
)

caminho_base = st.sidebar.text_input(
    "Pasta do experimento",
    value="",
    placeholder=(
        "Ex.: models/Importancias_2026-10-03_17-00-00"
    )
)


# ============================================================
# VALIDAR PASTA
# ============================================================

if not caminho_base:

    st.info(
        "Informe a pasta do experimento na barra lateral."
    )

    st.stop()


if not os.path.exists(
    caminho_base
):

    st.error(
        f"Pasta não encontrada:\n{caminho_base}"
    )

    st.stop()


pasta_importancias = os.path.join(
    caminho_base,
    "importancias"
)


if not os.path.exists(
    pasta_importancias
):

    st.error(
        "A pasta 'importancias' não foi encontrada."
    )

    st.stop()


# ============================================================
# CARREGAR EXPERIMENTO
# ============================================================

try:

    metadata, iteracoes_disponiveis = (
        carregar_info_experimento(
            caminho_base
        )
    )

except Exception as erro:

    st.error(
        f"Erro ao carregar experimento:\n{erro}"
    )

    st.stop()


# ============================================================
# NÓS
# ============================================================

nos = [
    str(no)
    for no in metadata["alvos"]
]

numero_nos = len(
    nos
)

numero_arestas = (
    numero_nos
    * (numero_nos - 1)
    // 2
)


if numero_nos < 2:

    st.error(
        "São necessários pelo menos dois nós."
    )

    st.stop()


if len(
    iteracoes_disponiveis
) == 0:

    st.error(
        "Nenhum arquivo iteracao_XXXX.parquet encontrado."
    )

    st.stop()


# ============================================================
# INFORMAÇÕES DO EXPERIMENTO
# ============================================================

st.sidebar.markdown(
    "---"
)

st.sidebar.subheader(
    "Experimento"
)

st.sidebar.write(
    f"**Nós:** {numero_nos}"
)

st.sidebar.write(
    f"**Arestas possíveis:** "
    f"{numero_arestas}"
)

st.sidebar.write(
    f"**Iterações disponíveis:** "
    f"{len(iteracoes_disponiveis)}"
)

if "num_trees" in metadata:

    st.sidebar.write(
        f"**Árvores/RF:** "
        f"{metadata['num_trees']}"
    )

if "n_permut" in metadata:

    st.sidebar.write(
        f"**Permutações:** "
        f"{metadata['n_permut']}"
    )

if "fracao_amostra" in metadata:

    st.sidebar.write(
        f"**Fração da subsample:** "
        f"{metadata['fracao_amostra']}"
    )


# ============================================================
# NÚMERO DE ITERAÇÕES
# ============================================================

st.sidebar.markdown(
    "---"
)

st.sidebar.header(
    "Stability Selection"
)

max_iteracoes = len(
    iteracoes_disponiveis
)

valor_padrao_iteracoes = min(
    100,
    max_iteracoes
)

n_iteracoes = st.sidebar.number_input(
    "Número de subsamples",
    min_value=1,
    max_value=max_iteracoes,
    value=valor_padrao_iteracoes,
    step=1
)


# ============================================================
# π_thr
# ============================================================

pi_thr = st.sidebar.number_input(
    "πthr — limiar de estabilidade",
    min_value=0.501,
    max_value=0.999,
    value=0.750,
    step=0.001,
    format="%.3f"
)


# ============================================================
# MODO DE ESCOLHA DE q
# ============================================================

modo_q = st.sidebar.selectbox(
    "Como definir q?",
    options=[
        "A partir de E[V]",
        "Definir q manualmente"
    ],
    index=0
)


# ============================================================
# q A PARTIR DE E[V]
# ============================================================

if modo_q == "A partir de E[V]":

    ev = st.sidebar.number_input(
        "E[V] desejado",
        min_value=0.0,
        value=1.0,
        step=0.1,
        format="%.2f"
    )

    q = calcular_q(
        n_nodes=numero_nos,
        ev=ev,
        pi_thr=pi_thr
    )

    st.sidebar.success(
        f"q calculado = {q}"
    )

    q_funcao = None


# ============================================================
# q MANUAL
# ============================================================

else:

    q = st.sidebar.number_input(
        "q — número de arestas por subsample",
        min_value=1,
        max_value=numero_arestas,
        value=min(
            10,
            numero_arestas
        ),
        step=1
    )

    q = int(q)

    ev = calcular_limite_esperado_v(
        q=q,
        n_nodes=numero_nos,
        pi_thr=pi_thr
    )

    q_funcao = q

    st.sidebar.caption(
        f"Com esse q, o limite é "
        f"E[V] ≤ {ev:.4f}"
    )


# ============================================================
# NÓS ISOLADOS
# ============================================================

st.sidebar.markdown(
    "---"
)

manter_isolados = (
    st.sidebar.checkbox(
        "Manter nós isolados?",
        value=False
    )
)


# ============================================================
# CALCULAR
# ============================================================

inicio = time.perf_counter()

try:

    (
        matriz_estabilidade,
        matriz_adjacencia,
        q_utilizado,
        info
    ) = calcular_estabilidade_cache(

        pasta=caminho_base,

        q=q_funcao,

        ev=ev,

        pi_thr=pi_thr,

        n_iteracoes=int(
            n_iteracoes
        )
    )

except Exception as erro:

    st.error(
        f"Erro ao calcular Stability Selection:\n\n{erro}"
    )

    st.stop()


tempo = (
    time.perf_counter()
    - inicio
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.subheader(
    "⚙️ Configuração"
)

c1, c2, c3, c4, c5 = (
    st.columns(5)
)


with c1:

    st.metric(
        "Nós",
        numero_nos
    )


with c2:

    st.metric(
        "Subsamples",
        info[
            "iteracoes_utilizadas"
        ]
    )


with c3:

    st.metric(
        "q",
        q_utilizado
    )


with c4:

    st.metric(
        "πthr",
        f"{pi_thr:.3f}"
    )


with c5:

    st.metric(
        "E[V] limite",
        f"{info['ev_limite']:.4f}"
    )


st.caption(
    f"Cálculo concluído em {tempo:.3f} segundos."
)


# ============================================================
# EXPLICAÇÃO DE q
# ============================================================

if modo_q == "A partir de E[V]":

    st.info(
        (
            f"Com E[V] = {ev:.2f} e "
            f"πthr = {pi_thr:.3f}, "
            f"o número de arestas selecionadas "
            f"por subsample é q = {q_utilizado}."
        )
    )


# ============================================================
# GRAFO
# ============================================================

fig, G = plotar_grafo(
    matriz_estabilidade=matriz_estabilidade,
    pi_thr=pi_thr,
    manter_isolados=manter_isolados
)

st.pyplot(
    fig,
    use_container_width=True
)

plt.close(
    fig
)


# ============================================================
# ESTATÍSTICAS DO GRAFO
# ============================================================

st.subheader(
    "📊 Informações do grafo"
)

c1, c2, c3, c4 = (
    st.columns(4)
)


with c1:

    st.metric(
        "Nós exibidos",
        G.number_of_nodes()
    )


with c2:

    st.metric(
        "Arestas estáveis",
        G.number_of_edges()
    )


with c3:

    densidade = (
        nx.density(G)
        if G.number_of_nodes() > 1
        else 0
    )

    st.metric(
        "Densidade",
        f"{densidade:.4f}"
    )


with c4:

    grau_medio = (
        sum(
            dict(
                G.degree()
            ).values()
        )
        / G.number_of_nodes()
        if G.number_of_nodes() > 0
        else 0
    )

    st.metric(
        "Grau médio",
        f"{grau_medio:.2f}"
    )


# ============================================================
# ARESTAS ESTÁVEIS
# ============================================================

arestas_estaveis = (
    matriz_para_lista_arestas(
        matriz_estabilidade,
        pi_thr=pi_thr
    )
)


with st.expander(
    "🔗 Ver arestas estáveis",
    expanded=True
):

    if arestas_estaveis.empty:

        st.info(
            "Nenhuma aresta ultrapassou o limiar."
        )

    else:

        st.dataframe(
            arestas_estaveis.style.format(
                {
                    "estabilidade":
                        "{:.3f}"
                }
            ),
            use_container_width=True
        )


# ============================================================
# MATRIZ DE ESTABILIDADE
# ============================================================

with st.expander(
    "📊 Ver matriz de estabilidade"
):

    st.dataframe(
        matriz_estabilidade
        .style
        .format(
            "{:.3f}"
        ),
        use_container_width=True
    )


# ============================================================
# MATRIZ DE ADJACÊNCIA
# ============================================================

with st.expander(
    "🔢 Ver matriz de adjacência"
):

    st.dataframe(
        matriz_adjacencia,
        use_container_width=True
    )


# ============================================================
# TODAS AS ARESTAS
# ============================================================

with st.expander(
    "Ver frequência de todas as arestas"
):

    todas_arestas = (
        matriz_para_lista_arestas(
            matriz_estabilidade,
            pi_thr=0.0
        )
    )

    st.dataframe(
        todas_arestas.style.format(
            {
                "estabilidade":
                    "{:.3f}"
            }
        ),
        use_container_width=True
    )


# ============================================================
# DOWNLOADS
# ============================================================

st.subheader(
    "💾 Exportar"
)

c1, c2, c3 = (
    st.columns(3)
)


with c1:

    csv_estabilidade = (
        matriz_estabilidade
        .to_csv()
        .encode(
            "utf-8"
        )
    )

    st.download_button(
        label="Baixar matriz de estabilidade",
        data=csv_estabilidade,
        file_name="matriz_estabilidade.csv",
        mime="text/csv"
    )


with c2:

    csv_adjacencia = (
        matriz_adjacencia
        .to_csv()
        .encode(
            "utf-8"
        )
    )

    st.download_button(
        label="Baixar matriz de adjacência",
        data=csv_adjacencia,
        file_name="matriz_adjacencia.csv",
        mime="text/csv"
    )


with c3:

    csv_arestas = (
        arestas_estaveis
        .to_csv(
            index=False
        )
        .encode(
            "utf-8"
        )
    )

    st.download_button(
        label="Baixar arestas estáveis",
        data=csv_arestas,
        file_name="arestas_estaveis.csv",
        mime="text/csv"
    )