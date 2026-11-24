# N3 · Modelo Preditivo de Inadimplência

Análise Preditiva · Engenharia de Software · Católica SC · Prof. Luiz C. Camargo
Alunas: Maria A. Giuliari e Mariele Vieira · Apresentação: 27/11/2026

## Arquivos

| Arquivo | O que é |
|---|---|
| `N3_Modelo_Preditivo_Inadimplencia.ipynb` | Notebook completo, já executado (itens 1 a 4 da avaliação) |
| `features.py` | Regras de limpeza e engenharia de atributos (usado no treino **e** no app) |
| `app.py` | Interface Streamlit (deploy) |
| `modelo_inadimplencia.joblib` | Pipeline completo salvo (limpeza + pré-processamento + Regressão Logística) |
| `modelo_meta.json` | Métricas, limiar, lista de cidades e versões das bibliotecas |
| `requirements.txt` | Versões exatas usadas para treinar e salvar o modelo |
| `lakehouse/` | Camadas bronze, prata e ouro em Parquet |
| `credito_sujo.csv` | Base de origem (a mesma da N2) |

## Como rodar a interface

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre em `http://localhost:8501`. Use os botões **"Carregar: Cliente de baixo risco"** e **"Carregar: Cliente de alto risco"** para a demonstração.

> **Atenção às versões:** o `.joblib` deste pacote foi salvo com scikit-learn 1.9.1 (Python 3.13). Se vocês **retreinarem no Colab**, o notebook gera um novo `.joblib` **e um novo `requirements.txt`** com as versões do Colab. Usem sempre os dois juntos, gerados na mesma execução.

---

## Roteiro da apresentação (≈ 10 min)

### 1 · Domínio (1,0)
- Previsão de **inadimplência** em empréstimos pessoais (mesma base das atividades da N2).
- Alvo: `inadimplente` (1 = atraso > 90 dias). **Classificação binária desbalanceada** (≈ 17% positivos).
- **Erro mais caro: falso negativo.** Aprovar quem não paga custa o valor emprestado (≈ R$ 14 mil). Recusar um bom pagador custa só a margem de juros.

### 2 · Pipeline de dados (2,0)
- **Data Lakehouse, arquitetura medalhão**, em Parquet:
  - **Bronze:** CSV bruto, sem alteração, com metadados de ingestão.
  - **Prata:** remove 25 duplicatas, padroniza 13 grafias de `estado_civil`, idade/renda inválidas viram NaN e prazo em anos vira meses.
  - **Ouro:** só as colunas que existem na hora da decisão. Sai `qtd_cobrancas` (vazamento) e sai `id_cliente`.
- **Atributos criados:** `comprometimento` (parcela/renda) e `log_renda`.
- **Separação:** 75/25 estratificado, `random_state=42`. Validação cruzada de 5 folds só no treino.
- **Cuidados contra vazamento:** `qtd_cobrancas` removida; duplicatas removidas antes do split; imputação, escala e encoding **dentro do pipeline** (ajustados só no treino); atributos criados são fórmulas linha a linha.

### 3.1 · Modelos (2,0)
Dummy (`most_frequent`) + Regressão Logística + Random Forest + HistGradientBoosting, todos com `class_weight="balanced"`.

### 3.2 · Métricas (2,0)
| Métrica | Mede | Faixa / bom valor | Por que usar |
|---|---|---|---|
| **ROC-AUC** | Capacidade de ordenar por risco | 0–1; 0,5 = chute; > 0,7 útil | O modelo é um score de risco; não depende do limiar |
| **PR-AUC** (average precision) | Precisão × recall só na classe positiva | 0–1; base = prevalência (0,165) | **Robusta ao desbalanceamento** |
| **Recall** | VP / (VP + FN) | 0–1; Dummy = 0 | Mede direto o erro caro (FN) |

### 3.3 · Resultado no teste
| Modelo | ROC-AUC | PR-AUC | Recall | AUC treino |
|---|---|---|---|---|
| Dummy | 0,500 | 0,165 | 0,000 | 0,500 |
| **Regressão Logística** | **0,697** | **0,416** | **0,524** | 0,761 |
| Random Forest | 0,681 | 0,384 | 0,516 | 0,919 |
| HistGradientBoosting | 0,657 | 0,360 | 0,492 | 0,878 |

**Escolha: Regressão Logística.** Foi a melhor nas 3 métricas, a validação cruzada e o teste temporal (2024) confirmam, tem o menor sobreajuste (gap 0,06 contra 0,22–0,24 dos outros) e é **interpretável** (LGPD art. 20: direito à explicação de decisões automatizadas).

### 4 · Deploy (2,0)
- `joblib.dump` do **pipeline inteiro**, não só do estimador.
- Demonstração: `streamlit run app.py` → carregar os dois exemplos → mostrar a probabilidade.
- Versões no `requirements.txt` e na barra lateral do app.
- **Pickle/joblib só de fonte confiável** (pode executar código ao carregar).

---

## Perguntas que o professor pode fazer

**"Por que não usar acurácia?"** O Dummy, que sempre diz "adimplente", tem ≈ 83% de acurácia e não encontra nenhum inadimplente. Com classes desbalanceadas, a acurácia engana.

**"Por que a Random Forest perdeu, se é mais poderosa?"** Ela sobreajustou: AUC 0,92 no treino e 0,68 no teste. Com 3 mil linhas e uma relação de risco quase linear, o modelo simples generaliza melhor.

**"O que é vazamento de dados no seu projeto?"** O caso clássico é `qtd_cobrancas`: cobranças só existem depois do atraso. Na N2, ela levou a AUC a 1,0. O outro tipo seria ajustar imputação ou escala antes do split; evitamos colocando tudo dentro do `Pipeline`.

**"Por que `features.py` separado?"** O joblib salva só uma referência às funções do `FunctionTransformer`. O app precisa importar as mesmas funções para carregar o modelo.

**"Por que holdout estratificado se na N2 vocês defenderam a divisão temporal?"** O enunciado pede `stratify`. Mesmo assim, fizemos a checagem temporal (treino 2021–23, teste 2024) e a Regressão Logística continua a melhor (ROC-AUC 0,722).

**"Um AUC de 0,70 é bom?"** É moderado. Serve como **apoio** para priorizar a análise manual, não como decisão automática. Baixar o limiar para 0,4 sobe o recall para ≈ 69%, ao custo de sinalizar metade dos clientes.

**"O que significa `class_weight='balanced'`?"** Os erros na classe rara (inadimplente) pesam mais no treino, proporcional ao inverso da frequência. Sem isso, o modelo tenderia a prever sempre a classe majoritária.
