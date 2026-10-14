import os
import json
import itertools

import numpy as np
import pandas as pd


# ============================================================
# CALCULAR q A PARTIR DE E[V]
# ============================================================

def calcular_q(
    n_nodes,
    ev=1,
    pi_thr=0.75
):
    """
    Fórmula da Stability Selection:

        E[V] <=
        q² /
        ((2*pi_thr - 1) * p(p-1)/2)

    Portanto:

        q =
        floor(
            sqrt(
                (2*pi_thr - 1)
                * E[V]
                * p(p-1)/2
            )
        )
    """

    if not 0.5 < pi_thr < 1:

        raise ValueError(
            "pi_thr deve estar entre 0.5 e 1."
        )

    numero_arestas = (
        n_nodes
        * (n_nodes - 1)
        // 2
    )

    q = int(
        np.floor(
            np.sqrt(
                (2 * pi_thr - 1)
                * ev
                * numero_arestas
            )
        )
    )

    return min(
        q,
        numero_arestas
    )


# ============================================================
# SELECIONAR TOP q
# ============================================================

def carregar_iteracao(
    pasta,
    iteracao,
    carregar_desvios=False
):
    """
    Carrega a matriz de importâncias de uma iteração.

    matriz.loc[target, preditor]

    representa:

        preditor -> target
    """

    arquivo_importancias = os.path.join(
        pasta,
        "importancias",
        f"iteracao_{iteracao:04d}.parquet"
    )

    if not os.path.exists(arquivo_importancias):

        raise FileNotFoundError(
            f"Iteração {iteracao} não encontrada:\n"
            f"{arquivo_importancias}"
        )

    importancias = pd.read_parquet(
        arquivo_importancias
    )

    return importancias

# ============================================================
# MATRIZ DE ESTABILIDADE
# ============================================================

def calcular_matriz_estabilidade(
    pasta,
    q=None,
    ev=1,
    pi_thr=0.75,
    n_iteracoes=None
):
    """
    Calcula a Stability Selection a partir das importâncias
    previamente salvas.

    Para cada iteração k:

        1. Faz ranking LOCAL para cada target.

        2. Para cada aresta i-j:

           rank_ij =
               max(
                   rank(i predictor de j),
                   rank(j predictor de i)
               )

        3. Faz ranking GLOBAL das arestas.

        4. Seleciona as q melhores arestas.

        5. Soma 1 à frequência da aresta.

    No final:

        estabilidade(i,j)
        =
        número de seleções / número de subsamples
    """

    # ========================================================
    # METADATA
    # ========================================================

    caminho_metadata = os.path.join(
        pasta,
        "metadata.json"
    )

    with open(
        caminho_metadata,
        "r"
    ) as f:

        metadata = json.load(f)

    nos = list(
        metadata["alvos"]
    )

    n_nodes = len(nos)

    numero_arestas = (
        n_nodes
        * (n_nodes - 1)
        // 2
    )

    # ========================================================
    # q
    # ========================================================

    if q is None:

        q = calcular_q(
            n_nodes=n_nodes,
            ev=ev,
            pi_thr=pi_thr
        )

    if q > numero_arestas:

        raise ValueError(
            f"q={q} é maior que o número possível "
            f"de arestas ({numero_arestas})."
        )

    print("=" * 60)

    print(
        f"Número de nós: {n_nodes}"
    )

    print(
        f"Número possível de arestas: "
        f"{numero_arestas}"
    )

    print(
        f"q = {q}"
    )

    print(
        f"pi_thr = {pi_thr}"
    )

    print(
        f"E[V] = {ev}"
    )

    print("=" * 60)

    # ========================================================
    # CARREGAR IMPORTÂNCIAS
    # ========================================================

    pasta_importancias = os.path.join(
        pasta,
        "importancias"
    )

    dados_por_target = {}

    conjuntos_iteracoes = []

    for target in nos:

        arquivo = os.path.join(
            pasta_importancias,
            f"{target}.csv"
        )

        if not os.path.exists(arquivo):

            raise FileNotFoundError(
                f"Arquivo não encontrado:\n{arquivo}"
            )

        dados = pd.read_csv(
            arquivo
        )

        dados_por_target[target] = dados

        conjuntos_iteracoes.append(
            set(
                dados["iteracao"].unique()
            )
        )

    # ========================================================
    # USAR APENAS ITERAÇÕES PRESENTES EM TODOS OS TARGETS
    # ========================================================

    iteracoes_disponiveis = sorted(
        set.intersection(
            *conjuntos_iteracoes
        )
    )

    if n_iteracoes is not None:

        if n_iteracoes > len(iteracoes_disponiveis):

            raise ValueError(
                f"Você pediu {n_iteracoes} iterações, "
                f"mas existem apenas "
                f"{len(iteracoes_disponiveis)} completas."
            )

        iteracoes_disponiveis = (
            iteracoes_disponiveis[
                :n_iteracoes
            ]
        )

    n_sub = len(
        iteracoes_disponiveis
    )

    if n_sub == 0:

        raise ValueError(
            "Não existem iterações completas."
        )

    print(
        f"Usando {n_sub} subsamples."
    )

    # ========================================================
    # MATRIZ DE CONTAGEM
    # ========================================================

    contagem = pd.DataFrame(
        0.0,
        index=nos,
        columns=nos
    )

    # ========================================================
    # ITERAÇÕES
    # ========================================================

    for numero, k in enumerate(
        iteracoes_disponiveis,
        start=1
    ):

        # ====================================================
        # RANKINGS LOCAIS
        # ====================================================

        ranks_locais = {}

        for target in nos:

            dados_target = (
                dados_por_target[target]
            )

            grupo = dados_target[
                dados_target["iteracao"] == k
            ]

            importancias = (
                grupo
                .set_index("variavel")[
                    "importancia"
                ]
            )

            # ----------------------------------------------
            # Queremos somente os outros nós do grafo
            # ----------------------------------------------

            outros_nos = [
                x
                for x in nos
                if x != target
            ]

            importancias = (
                importancias
                .reindex(outros_nos)
            )

            if importancias.isna().any():

                faltando = (
                    importancias[
                        importancias.isna()
                    ]
                    .index
                    .tolist()
                )

                raise ValueError(
                    f"Faltam importâncias para "
                    f"target={target}, "
                    f"iteração={k}: "
                    f"{faltando}"
                )

            # ==============================================
            # RANK LOCAL
            #
            # maior importância => menor rank
            #
            # method='average' gera por exemplo:
            #
            # rank 11.5 e 11.5
            #
            # quando há empate entre posições 11 e 12.
            # ==============================================

            ranking = importancias.rank(
                ascending=False,
                method="average"
            )

            ranks_locais[target] = ranking

        # ====================================================
        # CRIAR AS ARESTAS
        # ====================================================

        lista_arestas = []

        for i, j in itertools.combinations(
            nos,
            2
        ):

            # ----------------------------------------------
            # i como predictor de j
            # ----------------------------------------------

            rank_i_para_j = (
                ranks_locais[j].loc[i]
            )

            # ----------------------------------------------
            # j como predictor de i
            # ----------------------------------------------

            rank_j_para_i = (
                ranks_locais[i].loc[j]
            )

            # ==============================================
            # REGRA CONSERVADORA DO PAPER
            #
            # Rank menor = melhor.
            #
            # Portanto o pior dos dois é o MAIOR.
            # ==============================================

            rank_aresta = max(
                rank_i_para_j,
                rank_j_para_i
            )

            lista_arestas.append({

                "no_1": i,

                "no_2": j,

                "rank_i_para_j":
                    rank_i_para_j,

                "rank_j_para_i":
                    rank_j_para_i,

                "rank_aresta":
                    rank_aresta
            })

        arestas = pd.DataFrame(
            lista_arestas
        )

        # ====================================================
        # TOP q DO GRAFO INTEIRO
        # ====================================================

        selecionadas = selecionar_top_q(
            arestas,
            q
        )

        # ====================================================
        # CONTAGEM
        # ====================================================

        for _, aresta in (
            selecionadas.iterrows()
        ):

            i = aresta["no_1"]
            j = aresta["no_2"]

            contagem.loc[i, j] += 1

            contagem.loc[j, i] += 1

        print(
            f"\rIteração "
            f"{numero}/{n_sub}",
            end=""
        )

    print()

    # ========================================================
    # FREQUÊNCIA DE ESTABILIDADE
    # ========================================================

    matriz_estabilidade = (
        contagem
        / n_sub
    )

    np.fill_diagonal(
        matriz_estabilidade.values,
        0
    )

    # ========================================================
    # GRAFO FINAL
    # ========================================================

    matriz_adjacencia = (
        matriz_estabilidade
        >= pi_thr
    ).astype(int)

    np.fill_diagonal(
        matriz_adjacencia.values,
        0
    )

    return (
        matriz_estabilidade,
        matriz_adjacencia,
        q
    )

if __name__ == "__main__":

    pasta = (
        "models/"
        "Importancias_2026-09-30_18-00-00"
    )

    estabilidade, adjacencia, q = (
        calcular_matriz_estabilidade(

            pasta=pasta,

            # Se deixar None,
            # calcula a partir de E[V].
            q=None,

            ev=1,

            pi_thr=0.75,

            n_iteracoes=100
        )
    )

    estabilidade.to_csv(
        os.path.join(
            pasta,
            "matriz_estabilidade.csv"
        )
    )

    adjacencia.to_csv(
        os.path.join(
            pasta,
            "matriz_adjacencia.csv"
        )
    )

    print(
        f"q utilizado: {q}"
    )