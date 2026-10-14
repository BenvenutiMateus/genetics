import os
import json
import time
import datetime

import numpy as np
import pandas as pd

from sklearn.ensemble import (
    RandomForestRegressor,
    RandomForestClassifier
)
from sklearn.inspection import permutation_importance

from tqdm import tqdm


# ============================================================
# GERAR E SALVAR IMPORTÂNCIAS
# ============================================================

def extrair_importancias_brutas(
    df,
    alvos,
    num_trees=500,
    iteracoes=100,
    fracao_amostra=0.5,
    pasta=None,
    n_permut=5,
    max_categorias=5
):
    """
    Gera permutation importances para cada target em diferentes
    subsamples e salva uma matriz por iteração.

    ==========================================================
    ESTRUTURA DA MATRIZ
    ==========================================================

    Para cada iteração b:

                        PREDITOR
                    A       B       C
              A    NaN    imp     imp
    TARGET    B    imp     NaN     imp
              C    imp     imp     NaN

    Portanto:

        matriz.loc[target, preditor]

    representa:

        preditor -> target

    Exemplo:

        matriz.loc["glicose", "idade"]

    representa a importância de:

        idade -> glicose


    ==========================================================
    ARQUIVOS
    ==========================================================

    models/Importancias_.../

        metadata.json

        importancias/
            iteracao_0000.parquet
            iteracao_0001.parquet
            ...
            iteracao_0099.parquet

        desvios/
            iteracao_0000.parquet
            iteracao_0001.parquet
            ...
            iteracao_0099.parquet


    ==========================================================
    IMPORTANTE
    ==========================================================

    Esta função NÃO aplica:

        - ranking
        - q
        - pi_thr
        - E[V]
        - stability selection

    Apenas salva as importâncias brutas.

    Assim é possível posteriormente testar diferentes valores
    de q, pi_thr etc. sem rodar novamente as Random Forests.

    Se uma iteração já existir completamente, ela é pulada.

    Exemplo:

        primeira execução:
            iteracoes=100

        depois:
            iteracoes=200

    serão calculadas apenas:

        100, 101, ..., 199
    """

    inicio = time.perf_counter()

    # ========================================================
    # VALIDAÇÕES
    # ========================================================

    alvos = list(alvos)

    if len(alvos) == 0:
        raise ValueError("A lista 'alvos' está vazia.")


    if fracao_amostra <= 0:
        raise ValueError(
            "'fracao_amostra' deve ser maior que zero."
        )

    # ========================================================
    # DADOS
    # ========================================================

    # Pegamos primeiro somente as variáveis utilizadas.
    # Assim NA em colunas externas não remove indivíduos.
    df_modelo = (
        df[alvos]
        .copy()
        .dropna()
    )

    if fracao_amostra > 1:

        if int(fracao_amostra) > len(df_modelo):

            raise ValueError(
                "fracao_amostra é maior que o número "
                "de observações disponíveis."
            )

    # ========================================================
    # IDENTIFICAR TARGETS CATEGÓRICOS
    # ========================================================

    colunas_categoricas = [
        coluna
        for coluna in alvos
        if df_modelo[coluna].nunique() <= max_categorias
    ]

    # ========================================================
    # PASTAS
    # ========================================================

    if pasta is None:

        pasta = os.path.join(
            "models",
            (
                "Importancias_"
                f"{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}"
            )
        )

    pasta_importancias = os.path.join(
        pasta,
        "importancias"
    )


    os.makedirs(
        pasta_importancias,
        exist_ok=True
    )

    caminho_metadata = os.path.join(
        pasta,
        "metadata.json"
    )

    # ========================================================
    # METADATA
    # ========================================================

    configuracao_atual = {

        "formato": "matriz_por_iteracao",

        "convencao_matriz": (
            "linha=target; coluna=preditor; "
            "celula=importancia(preditor->target)"
        ),

        "num_trees": num_trees,

        "fracao_amostra": fracao_amostra,

        "n_permut": n_permut,

        "alvos": alvos,

        "n_linhas_df": len(df_modelo),

        "max_categorias": max_categorias,

        "colunas_categoricas": colunas_categoricas
    }

    # --------------------------------------------------------
    # Se a pasta já existe, verificar compatibilidade
    # --------------------------------------------------------

    if os.path.exists(caminho_metadata):

        with open(
            caminho_metadata,
            "r",
            encoding="utf-8"
        ) as f:

            metadata = json.load(f)

        campos_verificar = [
            "formato",
            "num_trees",
            "fracao_amostra",
            "n_permut",
            "alvos",
            "n_linhas_df",
            "max_categorias"
        ]

        for campo in campos_verificar:

            if metadata.get(campo) != configuracao_atual[campo]:

                raise ValueError(
                    f"A configuração '{campo}' mudou.\n\n"
                    f"Anterior:\n"
                    f"{metadata.get(campo)}\n\n"
                    f"Atual:\n"
                    f"{configuracao_atual[campo]}\n\n"
                    "Crie uma nova pasta para essa configuração."
                )

    else:

        metadata = configuracao_atual.copy()

        metadata["inicio"] = (
            datetime.datetime.now().isoformat()
        )

    metadata["iteracoes_solicitadas"] = max(
        iteracoes,
        metadata.get(
            "iteracoes_solicitadas",
            0
        )
    )

    metadata["ultima_atualizacao"] = (
        datetime.datetime.now().isoformat()
    )

    with open(
        caminho_metadata,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # ITERAÇÕES
    # ========================================================

    for i in tqdm(
        range(iteracoes),
        desc="Iterações"
    ):

        # ====================================================
        # CAMINHOS DA ITERAÇÃO
        # ====================================================

        arquivo_importancias = os.path.join(
            pasta_importancias,
            f"iteracao_{i:04d}.parquet"
        )



        if (
            os.path.exists(arquivo_importancias)

        ):
            continue

        # ====================================================
        # SUBSAMPLE
        # ====================================================


        if fracao_amostra > 1:

            df_sub = df_modelo.sample(
                n=int(fracao_amostra),
                random_state=i,
                replace=False
            )

        else:

            df_sub = df_modelo.sample(
                frac=fracao_amostra,
                random_state=i,
                replace=False
            )


        matriz_importancias = pd.DataFrame(
            np.nan,
            index=alvos,
            columns=alvos,
            dtype=np.float32
        )

        matriz_importancias.index.name = "target"

        # ====================================================
        # TARGETS DA ITERAÇÃO
        # ====================================================

        for target in tqdm(
            alvos,
            desc=f"Iteração {i}",
            leave=False
        ):

            X = df_sub.drop(
                columns=[target]
            )

            y = df_sub[target]

            # =================================================
            # RANDOM FOREST
            # =================================================

            if target in colunas_categoricas:

                modelo = RandomForestClassifier(
                    n_estimators=num_trees,

                    # Aproxima o comportamento tradicional
                    # do randomForest para classificação
                    max_features="sqrt",

                    bootstrap=True,

                    n_jobs=-1,

                    random_state=i
                )

                scoring = "accuracy"

            else:

                modelo = RandomForestRegressor(
                    n_estimators=num_trees,

                    # Aproximadamente p/3
                    max_features=1 / 3,

                    bootstrap=True,

                    n_jobs=-1,

                    random_state=i
                )

                scoring = "neg_mean_squared_error"

            # =================================================
            # AJUSTE
            # =================================================

            modelo.fit(
                X,
                y
            )

            # =================================================
            # PERMUTATION IMPORTANCE
            # =================================================

            resultado = permutation_importance(
                modelo,
                X,
                y,

                n_repeats=n_permut,

                scoring=scoring,

                random_state=i,

                n_jobs=-1
            )

            # =================================================
            # GUARDAR NA MATRIZ
            # =================================================

            matriz_importancias.loc[
                target,
                X.columns
            ] = (
                resultado
                .importances_mean
                .astype(np.float32)
            )

        # ====================================================
        # SALVAR ITERAÇÃO
        # ====================================================

        # Usamos arquivos temporários para evitar deixar um
        # Parquet incompleto caso o processo seja interrompido
        # durante a escrita.

        temp_importancias = (
            arquivo_importancias
            + ".tmp.parquet"
        )

        matriz_importancias.to_parquet(
            temp_importancias,
            engine="pyarrow",
            compression="zstd",
            index=True
        )

        # Renomeação atômica
        os.replace(
            temp_importancias,
            arquivo_importancias
        )

    # ========================================================
    # FINALIZAR METADATA
    # ========================================================

    arquivos_concluidos = [
        nome
        for nome in os.listdir(pasta_importancias)
        if (
            nome.startswith("iteracao_")
            and nome.endswith(".parquet")
        )
    ]

    metadata["iteracoes_concluidas"] = len(
        arquivos_concluidos
    )

    metadata["ultima_atualizacao"] = (
        datetime.datetime.now().isoformat()
    )

    with open(
        caminho_metadata,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            metadata,
            f,
            indent=2,
            ensure_ascii=False
        )

    # ========================================================
    # TEMPO TOTAL
    # ========================================================

    tempo = (
        time.perf_counter()
        - inicio
    )

    print("\n" + "=" * 60)

    print(
        f"Importâncias salvas em:\n{pasta}"
    )

    print(
        f"Iterações concluídas: "
        f"{metadata['iteracoes_concluidas']}"
    )

    print(
        f"Tempo total: {tempo:.2f}s"
    )

    print("=" * 60)

    return pasta


# ============================================================
# CARREGAR UMA ITERAÇÃO
# ============================================================



# ============================================================
# EXECUÇÃO
# ============================================================

if __name__ == "__main__":

    df = pd.read_csv(
        "sintetics/dados_sinteticos.csv"
    )

    df = df.drop(
        columns=[
            "id",
            "samplefilename"
        ],
        errors="ignore"
    )

    pasta = extrair_importancias_brutas(
        df=df,

        pasta='sintetics/',

        alvos=df.columns,

        num_trees=500,

        iteracoes=100,

        fracao_amostra=0.5,

        n_permut=5
    )

