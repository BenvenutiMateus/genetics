import os
import json
import re

import numpy as np
import pandas as pd


# ============================================================
# METADATA
# ============================================================

def carregar_metadata(pasta):
    """
    Carrega o metadata.json do experimento.
    """

    caminho = os.path.join(
        pasta,
        "metadata.json"
    )

    if not os.path.exists(caminho):
        raise FileNotFoundError(
            f"metadata.json não encontrado:\n{caminho}"
        )

    with open(
        caminho,
        "r",
        encoding="utf-8"
    ) as f:

        metadata = json.load(f)

    return metadata


# ============================================================
# NÚMERO DE ARESTAS POSSÍVEIS
# ============================================================

def numero_arestas_possiveis(n_nodes):
    """
    Número de arestas possíveis em um grafo não direcionado
    com n_nodes nós:

        p(p - 1) / 2
    """

    return (
        n_nodes
        * (n_nodes - 1)
        // 2
    )


# ============================================================
# CALCULAR q A PARTIR DE E[V]
# ============================================================

def calcular_q(
    n_nodes,
    ev=1,
    pi_thr=0.75
):
    """
    Calcula q usando a fórmula da Stability Selection
    empregada por Fellinghauer et al.

    Temos:

        E[V] <=
        q² /
        (
            (2*pi_thr - 1)
            * p(p-1)/2
        )

    Portanto:

        q =
        ceil(
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

    if ev < 0:

        raise ValueError(
            "E[V] deve ser maior ou igual a zero."
        )

    n_arestas = numero_arestas_possiveis(
        n_nodes
    )

    q = int(
        np.floor(
            np.sqrt(
                (2 * pi_thr - 1)
                * ev
                * n_arestas
            )
        )
    )

    return min(
        q,
        n_arestas
    )


# ============================================================
# CALCULAR LIMITE DE E[V]
# ============================================================

def calcular_limite_esperado_v(
    q,
    n_nodes,
    pi_thr
):
    """
    Calcula:

        E[V] <=
        q² /
        (
            (2*pi_thr - 1)
            * p(p-1)/2
        )
    """

    if not 0.5 < pi_thr < 1:
        return None

    n_arestas = numero_arestas_possiveis(
        n_nodes
    )

    if n_arestas == 0:
        return None

    return (
        q ** 2
        /
        (
            (2 * pi_thr - 1)
            * n_arestas
        )
    )


# ============================================================
# DESCOBRIR ITERAÇÕES DISPONÍVEIS
# ============================================================

def listar_iteracoes_disponiveis(pasta):
    """
    Procura arquivos:

        importancias/
            iteracao_0000.parquet
            iteracao_0001.parquet
            ...

    e retorna:

        [0, 1, 2, ...]
    """

    pasta_importancias = os.path.join(
        pasta,
        "importancias"
    )

    if not os.path.exists(
        pasta_importancias
    ):

        return []

    padrao = re.compile(
        r"^iteracao_(\d+)\.parquet$"
    )

    iteracoes = []

    for arquivo in os.listdir(
        pasta_importancias
    ):

        resultado = padrao.match(
            arquivo
        )

        if resultado:

            iteracoes.append(
                int(
                    resultado.group(1)
                )
            )

    return sorted(iteracoes)


# ============================================================
# CARREGAR UMA ITERAÇÃO
# ============================================================

def carregar_iteracao(
    pasta,
    iteracao
):
    """
    Carrega a matriz de importâncias de uma iteração.

    Convenção:

        linha  = target
        coluna = preditor

    Portanto:

        matriz.loc[target, preditor]

    significa:

        preditor -> target
    """

    arquivo = os.path.join(
        pasta,
        "importancias",
        f"iteracao_{iteracao:04d}.parquet"
    )

    if not os.path.exists(arquivo):

        raise FileNotFoundError(
            f"Iteração {iteracao} não encontrada:\n"
            f"{arquivo}"
        )

    matriz = pd.read_parquet(
        arquivo
    )

    # --------------------------------------------------------
    # Compatibilidade caso "target" venha como coluna
    # em vez de índice.
    # --------------------------------------------------------

    if "target" in matriz.columns:

        matriz = matriz.set_index(
            "target"
        )

    matriz.index = (
        matriz.index
        .astype(str)
    )

    matriz.columns = (
        matriz.columns
        .astype(str)
    )

    return matriz


# ============================================================
# VALIDAR MATRIZ
# ============================================================

def validar_matriz_importancias(
    matriz,
    nos,
    iteracao=None
):
    """
    Garante que a matriz contenha exatamente os nós esperados.
    """

    faltando_linhas = [
        no
        for no in nos
        if no not in matriz.index
    ]

    faltando_colunas = [
        no
        for no in nos
        if no not in matriz.columns
    ]

    if (
        faltando_linhas
        or faltando_colunas
    ):

        mensagem = (
            "A matriz de importâncias está incompleta."
        )

        if iteracao is not None:

            mensagem += (
                f"\nIteração: {iteracao}"
            )

        if faltando_linhas:

            mensagem += (
                "\nTargets faltando:\n"
                f"{faltando_linhas}"
            )

        if faltando_colunas:

            mensagem += (
                "\nPreditores faltando:\n"
                f"{faltando_colunas}"
            )

        raise ValueError(
            mensagem
        )

    matriz = matriz.reindex(
        index=nos,
        columns=nos
    )

    return matriz


# ============================================================
# RANKING DAS ARESTAS DE UMA ITERAÇÃO
# ============================================================

def calcular_ranking_arestas(
    matriz,
    nos
):
    """
    Calcula o ranking das arestas de UMA subsample.

    ----------------------------------------------------------
    1. Ranking local
    ----------------------------------------------------------

    Para cada target:

        maior importância = melhor rank

    Exemplo:

        B -> A = rank 1
        C -> A = rank 2
        D -> A = rank 3


    ----------------------------------------------------------
    2. Combinar as duas direções
    ----------------------------------------------------------

    Para a aresta não direcionada A-B:

        B -> A
        A -> B

    Fellinghauer utiliza a opção conservadora:

        rank_aresta =
        max(
            rank(B -> A),
            rank(A -> B)
        )

    ----------------------------------------------------------
    3. Ordenação global
    ----------------------------------------------------------

    Depois todas as arestas do grafo são ordenadas pelo
    rank_aresta.

    Em caso de empate no rank conservador, usamos como
    desempate o melhor dos dois ranks.

    Esse desempate serve apenas para garantir exatamente q
    arestas quando o corte ocorre dentro de um empate.
    """

    # ========================================================
    # RANK LOCAL
    # ========================================================
    matriz_limpa = matriz.to_numpy(dtype=float, copy=True)

    np.fill_diagonal(matriz_limpa, np.nan)

    df_limpo = pd.DataFrame(
        matriz_limpa,
        index=nos,
        columns=nos
    )

    ranks_locais = df_limpo.rank(
        axis=1,
        ascending=False,
        method="average",
        na_option="keep"
    ).to_numpy(dtype=float)

    # ========================================================
    # ÍNDICES DA PARTE SUPERIOR DA MATRIZ
    # ========================================================

    n = len(nos)

    idx_i, idx_j = np.triu_indices(
        n,
        k=1
    )

    valores = ranks_locais.to_numpy(
        dtype=float
    )

    # --------------------------------------------------------
    # matriz[target, preditor]
    #
    # valores[i, j]:
    #
    #     j -> i
    # --------------------------------------------------------

    rank_j_para_i = valores[
        idx_i,
        idx_j
    ]

    rank_i_para_j = valores[
        idx_j,
        idx_i
    ]

    # ========================================================
    # REGRA CONSERVADORA
    # ========================================================

    rank_aresta = np.maximum(
        rank_j_para_i,
        rank_i_para_j
    )

    nomes = np.asarray(
        nos,
        dtype=object
    )

    arestas = pd.DataFrame({

        "no_1": nomes[idx_i],

        "no_2": nomes[idx_j],

        # no_2 -> no_1
        "rank_no2_para_no1":
            rank_j_para_i,

        # no_1 -> no_2
        "rank_no1_para_no2":
            rank_i_para_j,

        "rank_aresta":
            rank_aresta
    }).dropna(subset=["rank_aresta"])

    # --------------------------------------------------------
    # Se por algum motivo existir NA em alguma direção,
    # a aresta não pode ser ranqueada corretamente.
    # --------------------------------------------------------

    arestas["rank_global"] = arestas["rank_aresta"].rank(
        ascending=True,
        method="average"
    )

    # Posição máxima do bloco empatado (garante nunca ultrapassar q)
    arestas["rank_max"] = arestas["rank_aresta"].rank(
        ascending=True,
        method="max"
    )

    return arestas.sort_values(
        by=["rank_global", "no_1", "no_2"]
    ).reset_index(drop=True)



# ============================================================
# TOP q
# ============================================================

def selecionar_top_q(
    arestas,
    q
):
    """
    Seleciona as arestas com rank_global <= q.
    Pela definição de rank médio (average), se houver empate atravessando
    a fronteira q (ex: 11ª e 12ª empatadas com rank_global = 11.5 para q = 11),
    ambas terão rank_global > q e serão automaticamente descartadas,
    restando apenas as 10 primeiras (exatamente como na pág. 6 de Fellinghauer).
    """
    if q < 0:
        raise ValueError("q não pode ser negativo.")

    if q > len(arestas):
        raise ValueError(
            f"q={q} é maior que o número de arestas ranqueáveis ({len(arestas)})."
        )

    if q == 0:
        return arestas.iloc[0:0].copy()

    return arestas[arestas["rank_max"] <= q].copy()


# ============================================================
# MATRIZ DE ESTABILIDADE
# ============================================================

def calcular_matriz_estabilidade(
    pasta,
    q=None,
    ev=1,
    pi_thr=0.75,
    n_iteracoes=None,
    mostrar_progresso=True
):
    """
    Calcula Stability Selection usando os Parquets salvos.

    Para cada subsample k:

        1. Carrega:

           iteracao_XXXX.parquet

        2. Faz ranking LOCAL dentro de cada regressão.

        3. Para cada aresta i-j:

               rank(i-j)
               =
               max(
                   rank(j -> i),
                   rank(i -> j)
               )

        4. Ordena todas as arestas do grafo.

        5. Seleciona as q melhores arestas.

        6. Soma 1 à contagem da aresta.

    No final:

        pi_hat(i,j)
        =
        número de subsamples em que a aresta foi selecionada
        /
        número de subsamples utilizados

    O grafo final contém:

        pi_hat(i,j) >= pi_thr
    """

    # ========================================================
    # METADATA
    # ========================================================

    metadata = carregar_metadata(
        pasta
    )

    nos = [
        str(no)
        for no in metadata["alvos"]
    ]

    n_nodes = len(nos)

    n_arestas = numero_arestas_possiveis(
        n_nodes
    )

    # ========================================================
    # ITERAÇÕES DISPONÍVEIS
    # ========================================================

    iteracoes_disponiveis = (
        listar_iteracoes_disponiveis(
            pasta
        )
    )

    if not iteracoes_disponiveis:

        raise ValueError(
            "Nenhuma iteração Parquet foi encontrada."
        )

    # --------------------------------------------------------
    # Número de iterações solicitado
    # --------------------------------------------------------

    if n_iteracoes is not None:

        if n_iteracoes <= 0:

            raise ValueError(
                "n_iteracoes deve ser maior que zero."
            )

        if (
            n_iteracoes
            > len(iteracoes_disponiveis)
        ):

            raise ValueError(
                f"Você pediu {n_iteracoes} iterações, "
                f"mas existem apenas "
                f"{len(iteracoes_disponiveis)} disponíveis."
            )

        iteracoes_usadas = (
            iteracoes_disponiveis[
                :n_iteracoes
            ]
        )

    else:

        iteracoes_usadas = (
            iteracoes_disponiveis
        )

    n_sub = len(
        iteracoes_usadas
    )

    # ========================================================
    # q
    # ========================================================

    q_calculado_por_ev = (
        q is None
    )

    if q is None:

        q = calcular_q(
            n_nodes=n_nodes,
            ev=ev,
            pi_thr=pi_thr
        )

    q = int(q)

    if q < 0:

        raise ValueError(
            "q não pode ser negativo."
        )

    if q > n_arestas:

        raise ValueError(
            f"q={q} é maior que o número possível "
            f"de arestas ({n_arestas})."
        )

    # ========================================================
    # INFORMAÇÕES
    # ========================================================

    ev_limite = (
        calcular_limite_esperado_v(
            q=q,
            n_nodes=n_nodes,
            pi_thr=pi_thr
        )
    )

    if mostrar_progresso:

        print(
            "=" * 60
        )

        print(
            f"Número de nós: {n_nodes}"
        )

        print(
            f"Número possível de arestas: "
            f"{n_arestas}"
        )

        print(
            f"Subsamples utilizados: {n_sub}"
        )

        print(
            f"q: {q}"
        )

        print(
            f"pi_thr: {pi_thr}"
        )

        if q_calculado_por_ev:

            print(
                f"E[V] solicitado: {ev}"
            )

        print(
            f"Limite E[V] para q atual: "
            f"{ev_limite:.6f}"
        )

        print(
            "=" * 60
        )

    # ========================================================
    # MATRIZ DE CONTAGEM
    # ========================================================

    contagem = pd.DataFrame(
        0,
        index=nos,
        columns=nos,
        dtype=np.int32
    )

    # ========================================================
    # ITERAÇÕES
    # ========================================================

    for numero, iteracao in enumerate(
        iteracoes_usadas,
        start=1
    ):

        # ====================================================
        # CARREGAR MATRIZ
        # ====================================================

        matriz = carregar_iteracao(
            pasta=pasta,
            iteracao=iteracao
        )

        matriz = validar_matriz_importancias(
            matriz=matriz,
            nos=nos,
            iteracao=iteracao
        )

        # ====================================================
        # RANKING GLOBAL DAS ARESTAS
        # ====================================================

        arestas = calcular_ranking_arestas(
            matriz=matriz,
            nos=nos
        )

        # ====================================================
        # TOP q
        # ====================================================

        selecionadas = selecionar_top_q(
            arestas=arestas,
            q=q
        )

        # ====================================================
        # CONTAGEM
        # ====================================================

        for aresta in selecionadas.itertuples(
            index=False
        ):

            i = aresta.no_1
            j = aresta.no_2

            contagem.loc[
                i,
                j
            ] += 1

            contagem.loc[
                j,
                i
            ] += 1

        if mostrar_progresso:

            print(
                f"\rIteração "
                f"{numero}/{n_sub}",
                end=""
            )

    if mostrar_progresso:
        print()

    # ========================================================
    # FREQUÊNCIA DE ESTABILIDADE
    # ========================================================

    matriz_estabilidade = (
    contagem.astype(np.float32)
    / n_sub
    ).copy()
    
    for no in matriz_estabilidade.index:
        matriz_estabilidade.loc[no, no] = 0.0

    # ========================================================
    # MATRIZ DE ADJACÊNCIA
    # ========================================================

    matriz_adjacencia = (
    matriz_estabilidade
        >= pi_thr
    ).astype(np.uint8).copy()

    for no in matriz_adjacencia.index:
        matriz_adjacencia.loc[no, no] = 0

    # ========================================================
    # INFORMAÇÕES
    # ========================================================

    informacoes = {

        "numero_nos":
            n_nodes,

        "numero_arestas_possiveis":
            n_arestas,

        "iteracoes_disponiveis":
            len(iteracoes_disponiveis),

        "iteracoes_utilizadas":
            n_sub,

        "primeira_iteracao":
            iteracoes_usadas[0],

        "ultima_iteracao":
            iteracoes_usadas[-1],

        "q":
            q,

        "q_calculado_por_ev":
            q_calculado_por_ev,

        "ev_solicitado":
            ev if q_calculado_por_ev else None,

        "ev_limite":
            ev_limite,

        "pi_thr":
            pi_thr
    }

    return (
        matriz_estabilidade,
        matriz_adjacencia,
        q,
        informacoes
    )


# ============================================================
# MATRIZ -> LISTA DE ARESTAS
# ============================================================

def matriz_para_lista_arestas(
    matriz_estabilidade,
    pi_thr=0.0
):
    """
    Transforma a matriz simétrica de estabilidade em uma
    lista de arestas sem duplicar i-j e j-i.
    """

    nos = list(
        matriz_estabilidade.index
    )

    valores = (
        matriz_estabilidade
        .reindex(
            index=nos,
            columns=nos
        )
        .to_numpy()
    )

    i, j = np.triu_indices(
        len(nos),
        k=1
    )

    estabilidade = valores[
        i,
        j
    ]

    nomes = np.asarray(
        nos,
        dtype=object
    )

    resultado = pd.DataFrame({

        "no_1":
            nomes[i],

        "no_2":
            nomes[j],

        "estabilidade":
            estabilidade
    })

    resultado = resultado[
        resultado["estabilidade"]
        >= pi_thr
    ]

    return (
        resultado
        .sort_values(
            "estabilidade",
            ascending=False
        )
        .reset_index(
            drop=True
        )
    )


# ============================================================
# EXECUÇÃO DIRETA
# ============================================================

if __name__ == "__main__":

    pasta = (
        "models/"
        "Importancias_2026-10-03_17-00-00"
    )

    (
        estabilidade,
        adjacencia,
        q,
        info
    ) = calcular_matriz_estabilidade(

        pasta=pasta,

        # ----------------------------------------------------
        # Se q=None:
        # calcula q automaticamente a partir de E[V].
        # ----------------------------------------------------
        q=None,

        ev=1,

        pi_thr=0.75,

        # None = usa todas as iterações disponíveis.
        n_iteracoes=None
    )

    # ========================================================
    # SALVAR RESULTADOS
    # ========================================================

    estabilidade.to_parquet(
        os.path.join(
            pasta,
            "matriz_estabilidade.parquet"
        ),
        compression="zstd"
    )

    estabilidade.to_csv(
        os.path.join(
            pasta,
            "matriz_estabilidade.csv"
        )
    )

    adjacencia.to_parquet(
        os.path.join(
            pasta,
            "matriz_adjacencia.parquet"
        ),
        compression="zstd"
    )

    adjacencia.to_csv(
        os.path.join(
            pasta,
            "matriz_adjacencia.csv"
        )
    )

    arestas_finais = (
        matriz_para_lista_arestas(
            estabilidade,
            pi_thr=info["pi_thr"]
        )
    )

    arestas_finais.to_csv(
        os.path.join(
            pasta,
            "arestas_estaveis.csv"
        ),
        index=False
    )

    with open(
        os.path.join(
            pasta,
            "stability_metadata.json"
        ),
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            info,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        "\nResultados salvos."
    )

    print(
        f"q utilizado: {q}"
    )

    print(
        f"E[V] limite: "
        f"{info['ev_limite']:.6f}"
    )