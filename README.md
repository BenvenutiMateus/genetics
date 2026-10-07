# Genotype–Phenotype Graph Learning with Random Forests

This repository contains the statistical and computational pipeline developed as part of an **undergraduate research project (Iniciação Científica) at UFSCar, supported by CNPq**.

The project investigates the use of **Random Forests, variable importance, feature selection, and stability selection** to identify relationships between **genetic markers (SNPs), phenotypic variables, and sociodemographic covariates**.

The main objective is to estimate stable **genotype–phenotype dependence structures** and represent them through graphical models.

## Research Context

The dataset contains approximately:

- **720 individuals**
- **~240,000 SNPs**

Therefore, the problem is strongly high-dimensional:

\[
p \gg n
\]

The methodology is inspired by:

**Fellinghauer et al. — Stable Graphical Model Estimation with Random Forests for Discrete, Continuous, and Mixed Variables**

[arXiv:1109.0152](https://arxiv.org/abs/1109.0152)

Additional references are available in [`papers.md`](papers.md).

## Methodology

The general pipeline is:

```text
Data
  ↓
Preprocessing
  ↓
Repeated subsampling
  ↓
Random Forest for each target
  ↓
Variable importance ranking
  ↓
Edge ranking
  ↓
Global top-q edge selection
  ↓
Selection frequencies
  ↓
Stable graph
```

For each target variable, Random Forest models are fitted using the remaining variables as predictors.

Variable relevance is primarily evaluated using **Permutation Importance**.

Following the approach of Fellinghauer et al., predictor rankings are combined to rank possible graph edges.

The parameter \(q\) represents the **maximum number of edges selected globally in each subsample**, rather than the number of predictors selected for each target.

The procedure is repeated across multiple subsamples, and the stability of an edge is estimated by its selection frequency:

\[
\hat{\pi}_{ij}
=
\frac{\text{number of subsamples where edge }(i,j)\text{ is selected}}
{\text{total number of subsamples}}
\]

Edges with stability above a threshold \(\pi_{\text{thr}}\) are retained in the final graph.

## Graph Interpretation

- **Nodes:** variables
- **Edges:** stable selected relationships
- **Edge weights:** selection frequency or importance

Directed relationships may also be explored, but their direction represents the **predictive procedure** and should not automatically be interpreted as causal.

## Data

The analysis combines:

- LD-imputed genetic data in PLINK `.raw` format;
- SNP marker maps;
- phenotypic and sociodemographic variables.

The original genomic and phenotypic datasets are **not publicly distributed** due to privacy and research-data restrictions.

## Repository Structure

```text
Genetica/
├── src/
├── sintetics/
├── sintetics_gini/
├── info_pre_processamento/
├── app.py
├── fenotipos.ipynb
├── papers.md
└── README.md
```

## Technologies

- Python
- pandas
- NumPy
- scikit-learn
- NetworkX
- Matplotlib
- Streamlit
- Jupyter Notebook
- PLINK

## Project Status

**Research in progress.**

Current work focuses on Random Forest-based graph estimation, permutation importance, stability selection, edge-ranking strategies, and high-dimensional genomic applications.

## Funding

This undergraduate research project is supported by the **Conselho Nacional de Desenvolvimento Científico e Tecnológico (CNPq)**.

**CNPq Grant/Process No.:** 126658/2026-9

Federal University of São Carlos — **UFSCar**

## Contact

[benvenutimateus.github.io/contact.html](https://benvenutimateus.github.io/contact.html)
