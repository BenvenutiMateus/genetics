# Papers 📚

Some papers I'm saving for my research on **genotype–phenotype graphs**, **Random Forests**, and **stability selection**.

The idea is to keep everything in one place and add notes as I read. It's not a complete literature review — just papers that look useful.

`[ ]` = still need to read · `[x]` = read

## 1. Graph Creation

Papers about building graphs from data and figuring out which variables are connected.

- [x] **Fellinghauer et al. (2013) — Stable Graphical Model Estimation with Random Forests for Discrete, Continuous, and Mixed Variables**  
  [Paper](https://arxiv.org/abs/1109.0152) · [PDF](https://arxiv.org/pdf/1109.0152)  
  The main paper for my IC. Uses Random Forests + stability selection to build graphs. I want to understand the edge-selection steps and compare them with my implementation.

- [ ] **Meinshausen & Bühlmann (2006) — High-Dimensional Graphs and Variable Selection with the Lasso**  
  [Paper](https://arxiv.org/abs/math/0608017) · [PDF](https://arxiv.org/pdf/math/0608017)  
  Builds graphs using LASSO instead of Random Forests. Could be a good alternative method to test.

- [ ] **Friedman, Hastie & Tibshirani (2008) — Sparse Inverse Covariance Estimation with the Graphical Lasso**  
  [Paper](https://doi.org/10.1093/biostatistics/kxm045)  
  Another way to estimate a graph, this time through a sparse inverse covariance matrix. Useful for comparison on smaller datasets.

- [ ] **Huynh-Thu et al. (2010) — Inferring Regulatory Networks from Expression Data Using Tree-Based Methods**  
  [Paper](https://doi.org/10.1371/journal.pone.0012776)  
  Introduces GENIE3, a tree-based method for gene networks. Interesting because it works with *directed* connections.

- [ ] **Haslbeck & Waldorp (2020) — mgm: Estimating Time-Varying Mixed Graphical Models in High-Dimensional Data**  
  [Paper](https://doi.org/10.18637/jss.v093.i08)  
  Graphs with different types of variables. Might help when working with SNPs, phenotypes, and other covariates together.

## 2. Stability Selection

How to pick variables or edges that show up consistently across different samples.

- [ ] **Meinshausen & Bühlmann (2010) — Stability Selection**  
  [Paper](https://arxiv.org/abs/0809.2932) · [PDF](https://arxiv.org/pdf/0809.2932)  
  The key reference for stability selection. Especially important for understanding `q`, selection frequencies, and false positives.

- [ ] **Shah & Samworth (2013) — Variable Selection with Error Control: Another Look at Stability Selection**  
  [Paper](https://arxiv.org/abs/1105.5578) · [PDF](https://arxiv.org/pdf/1105.5578)  
  Looks at a different way of making subsamples (complementary pairs). Worth checking against my current approach.

- [ ] **Liu, Roeder & Wasserman (2010) — Stability Approach to Regularization Selection (StARS) for High Dimensional Graphical Models**  
  [Paper](https://arxiv.org/abs/1006.3316) · [PDF](https://arxiv.org/pdf/1006.3316)  
  Uses graph stability to choose a tuning parameter. Not the same as classical stability selection, but related.

## 3. Feature Selection & Variable Importance

Mostly about how to choose variables and how much to trust Random Forest importance scores.

- [ ] **Breiman (2001) — Random Forests**  
  [Paper](https://doi.org/10.1023/A:1010933404324)  
  The original Random Forest paper. Good background.

- [ ] **Strobl et al. (2008) — Conditional Variable Importance for Random Forests**  
  [Paper](https://doi.org/10.1186/1471-2105-9-307)  
  Very relevant because SNPs can be correlated. Looks at how correlation affects importance and proposes conditional importance.

- [ ] **Altmann et al. (2010) — Permutation Importance: A Corrected Feature Importance Measure**  
  [Paper](https://doi.org/10.1093/bioinformatics/btq134)  
  Interesting for studying variable importance more carefully. It uses permutations of the *response* to assess significance — different from the usual scikit-learn permutation importance.

- [ ] **Nembrini, König & Wright (2018) — The Revival of the Gini Importance?**  
  [Paper](https://doi.org/10.1093/bioinformatics/bty373)  
  A corrected version of impurity-based importance. Might be useful when permutation importance becomes too expensive.

- [ ] **Nicodemus et al. (2010) — The Behaviour of Random Forest Permutation-Based Variable Importance Measures under Predictor Correlation**  
  [Paper](https://doi.org/10.1186/1471-2105-11-110)  
  Another important paper for correlated SNPs. Compares how different importance measures behave when predictors are related.

## 4. Inference for Graphs

Finding connections is one thing. Deciding how much confidence we should put in those connections is another.

- [ ] **Watson & Wright (2021) — Testing Conditional Independence in Supervised Learning Algorithms**  
  [Paper](https://doi.org/10.1007/s10994-021-06030-6) · [arXiv](https://arxiv.org/abs/1901.09917)  
  Looks at tests for conditional feature relevance. Could help connect variable importance with statistical inference.

- [ ] **Janková & van de Geer (2015) — Honest Confidence Regions and Optimality in High-Dimensional Precision Matrix Estimation**  
  [Paper](https://arxiv.org/abs/1507.02061)  
  Confidence intervals for parameters in graphical models. More theoretical, but good to keep around.

- [ ] **Candès et al. (2018) — Panning for Gold: Model-X Knockoffs for High Dimensional Controlled Variable Selection**  
  [Paper](https://doi.org/10.1111/rssb.12265)  
  A different way to select variables while controlling false discoveries. Could be an alternative to look into later.

## 5. Genetics & SNPs

A few papers that are closer to the actual genetic data I'm working with.

- [ ] **Meng et al. (2009) — Performance of Random Forest When SNPs Are in Linkage Disequilibrium**  
  [Paper](https://doi.org/10.1186/1471-2105-10-78)  
  Very relevant: studies Random Forests when SNPs are correlated because of LD.

- [ ] **Sesia, Sabatti & Candès (2019) — Gene Hunting with Hidden Markov Model Knockoffs**  
  [Paper](https://doi.org/10.1093/biomet/asy033)  
  Uses knockoffs for genetic association studies. Interesting for dealing with dependence between SNPs.

## 6. Graph Evaluation

How to check whether the graphs are actually useful, beyond just looking nice.

- [ ] **Marbach et al. (2012) — Wisdom of Crowds for Robust Gene Network Inference**  
  [Paper](https://doi.org/10.1038/nmeth.2016)  
  Compares ways of predicting biological networks. Good inspiration for evaluating and comparing graph methods.

---

## What I want to look into next

- **Negative importances:** ignore them, keep only positive ones, or use absolute values? What changes in the final graph?
- **Selecting variables:** fixed `q` or cumulative importance threshold `p`?
- **Correlated SNPs:** how much does LD change the ranking?
- **Stability selection:** how to choose `q`, `pi_thr`, and the number of subsamples?
- **Other models:** can LASSO replace Random Forests in part of the pipeline?
- **Directed graphs:** do asymmetric importance scores tell us anything useful? (A directed prediction is not automatically a causal relationship.)
- **Validation:** test the methods on simulated data where the true connections are known.

## Reading order (for now)

1. Fellinghauer et al. (2013) — understand the original method well.
2. Meinshausen & Bühlmann (2010) — get the stability selection theory right.
3. Strobl et al. (2008) and Nicodemus et al. (2010) — look into correlated predictors.
4. Altmann et al. (2010) — study importance scores and their interpretation.
5. Meng et al. (2009) — connect all of this to SNPs and LD.
6. Meinshausen & Bühlmann (2006) — explore LASSO as another option.

## Notes

When I finish a paper, I'll just add a few lines underneath it:

```md
**My notes:**
- Main idea:
- What I found interesting:
- Could I use this in my IC?
```

> **Reminder:** an important predictor or a frequently selected edge is not automatically a statistically significant or causal connection.
