# Genotype–Phenotype Graph Learning with Random Forests

This repository contains the statistical and computational pipeline developed as part of an **undergraduate research project (Iniciação Científica) at the Federal University of São Carlos (UFSCar), supported by CNPq**.

The project investigates the use of **Random Forests, variable importance, feature selection, and stability-based procedures** to identify relationships between genetic markers (SNPs), phenotypic variables, and sociodemographic covariates in high-dimensional genomic data.

The broader objective is to explore methods for learning **genotype–phenotype dependence structures** and representing the selected relationships through graphical models.

## Research Context

You can see the related papers at [`Important papers ➔`](papers.md).

This research is developed within the **Department of Statistics at the Federal University of São Carlos (UFSCar)**.

**Funding:** Conselho Nacional de Desenvolvimento Científico e Tecnológico — **CNPq**

The project addresses a strongly high-dimensional genomic setting, with approximately:

- **720 individuals**
- **~240,000 candidate genetic markers (SNPs)**

In other words, the number of predictors is substantially larger than the sample size:

**p ≫ n**

where:

- **p** = number of candidate predictors (SNPs)
- **n** = number of individuals
## Reference / Related Publication

The methodological development of this project is inspired by concepts presented in:

**Fellinghauer et al. — Stable Graphical Model Estimation with Random Forests for Discrete, Continuous, and Mixed Variables**

- **arXiv:** [1109.0152](https://arxiv.org/abs/1109.0152)

The project investigates adaptations of these ideas to high-dimensional genotype–phenotype data, particularly through Random Forest-based variable selection and stability analysis.

## Data Structure

The analysis integrates three main data sources, harmonized using unique individual identifiers.

### 1. LD-Imputed Genetic Database

Located in the `Banco Genetico Imputado LD` directory, this dataset consists of PLINK `.raw` files containing genetic information for each chromosome.

- **Naming convention:** `chr{num}_imputado_LD.raw`
- **Sample size:** approximately 720 individuals
- **Metadata:** the first columns contain pedigree and phenotype identifiers
- **Primary identifier:** the `IID` column is used to match individuals across datasets
- **Genetic predictors:** numerically encoded SNPs, such as `rs62224618_T`

Because the number of SNPs can reach hundreds of thousands, the resulting dataset presents a strongly high-dimensional structure.

### 2. Marker Maps

Marker-map files contain genomic position information associated with each SNP.

- **Naming convention:** `chr{num}map_imputado_LD.map`
- **Information included:**
  - chromosome;
  - SNP identifier;
  - genetic position;
  - base-pair coordinate.

These files allow selected SNPs to be mapped back to their genomic locations.

### 3. Phenotypes and Covariates

The file `banco_fenotipos_conformal.csv` contains phenotypic outcomes and additional covariates used in the statistical analyses.

- **Matching variable:** `samplefilename`, which must be correctly aligned with the `IID` identifier from the genetic database.
- **Covariates:** the dataset may include categorical and sociodemographic variables related to characteristics such as smoking habits, race/color, marital status, occupation, and alcohol consumption.

Categorical predictors are encoded before model fitting when required.

## Statistical Methodology

The analysis pipeline is designed to handle the statistical and computational challenges associated with high-dimensional genomic data.

### Preprocessing

Preprocessing procedures and quality-control information are documented in the `info_pre_processamento` directory.

The preprocessing stage includes preparation of genomic, phenotypic, and covariate information before statistical modeling.

### Encoding

Categorical variables are transformed using techniques such as **One-Hot Encoding**, avoiding the introduction of arbitrary numerical ordering among nominal categories.

### Random Forest Models

Depending on the type of response variable, the pipeline uses:

- `RandomForestRegressor`
- `RandomForestClassifier`

Random Forests provide a flexible framework for modeling potentially nonlinear relationships and interactions among predictors without requiring a predefined parametric model.

### Variable Importance

Variable relevance is investigated primarily through **Permutation Importance**.

For each predictor, its values are permuted and the resulting change in model performance is measured. Larger deterioration in predictive performance indicates greater dependence of the fitted model on that variable.

Repeated permutations can be used to obtain more stable estimates of variable importance.

### Feature Selection

Because directly working with every SNP can be computationally expensive, the project investigates different strategies for selecting subsets of relevant predictors.

These include criteria based on:

- variable importance;
- top-\(q\) predictors;
- cumulative importance thresholds;
- repeated subsampling;
- selection frequency;
- stability across repeated model fits.

### Stability Analysis

Rather than interpreting the result of a single Random Forest model, the selection procedure can be repeated across multiple subsamples or random seeds.

The frequency with which a relationship is recovered provides a measure of its empirical stability.

These selection frequencies can subsequently be organized into matrices representing the strength or stability of relationships between variables.

### Graph Representation

The estimated relationships can be represented as graphs in which:

- **nodes** correspond to variables;
- **edges** correspond to selected relationships;
- **edge weights** can represent selection frequency, variable importance, or another stability measure.

The project also investigates the interpretation of **directed and undirected graph representations** derived from these selection procedures.

## Repository Structure

The repository contains scripts, notebooks, experiments, and visualization tools associated with the research pipeline.

```text
Genetica/
│
├── src/
│   └── Core analysis and transformation functions
│
├── sintetics/
│   └── Experiments using synthetic datasets
│
├── sintetics_gini/
│   └── Synthetic experiments using Gini-based importance
│
├── info_pre_processamento/
│   └── Information about preprocessing and genomic quality control
│
├── fenotipos.ipynb
├── glass.ipynb
├── app.py
├── pyproject.toml
└── README.md
```

## Interactive Visualization

The repository also includes a **Streamlit application** for exploring matrices and graphical representations generated by the analysis.

The interface allows different selection parameters and graph structures to be investigated interactively.

## Repository Notes & Data Access

The original genomic and phenotypic datasets are **not publicly hosted in this repository** due to their sensitive nature, research-data restrictions, and file-size limitations.

The repository therefore focuses on the statistical methodology, computational pipeline, simulations, and visualization tools developed during the research project.

## Technologies

The project primarily uses:

- Python
- pandas
- NumPy
- scikit-learn
- NetworkX
- Matplotlib
- Streamlit
- Jupyter Notebook
- PLINK-formatted genomic data

## Project Status

**Research in progress.**

The methodology, feature-selection strategies, stability analysis, and graphical representations are actively being developed as part of the undergraduate research project.

## Contact

For questions regarding the methodology, project, or academic collaboration, please contact the research team through:

[benvenutimateus.github.io/contact.html](https://benvenutimateus.github.io/contact.html)
