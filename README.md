<div align="center">

# 💳 Risco de Crédito · Modelo Preditivo de Inadimplência

**Do CSV bruto até uma aplicação web: um pipeline completo de Machine Learning, com Data Lakehouse, prevenção de vazamento de dados e deploy em Streamlit.**

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.9-F7931E?logo=scikitlearn&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-3.0-150458?logo=pandas&logoColor=white)
![Parquet](https://img.shields.io/badge/Apache%20Parquet-Lakehouse-50ABF1?logo=apacheparquet&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B?logo=streamlit&logoColor=white)

</div>

---

## 📌 Visão geral

Uma instituição financeira de Santa Catarina concede empréstimos pessoais, e parte dos clientes atrasa o pagamento por mais de 90 dias. Quando isso acontece, o valor emprestado vira prejuízo.

Este projeto estima, **no momento em que o cliente pede o crédito**, a probabilidade de ele se tornar inadimplente. O resultado ajuda o analista a decidir se aprova, recusa ou encaminha o pedido para análise manual.

| | |
|---|---|
| **Tipo de problema** | Classificação binária desbalanceada (≈ 17% de inadimplentes) |
| **Variável-alvo** | `inadimplente` (1 = atraso maior que 90 dias) |
| **Base** | ≈ 3 mil contratos (2021–2024), com erros reais de digitação, duplicatas e inconsistências |
| **Erro mais caro** | **Falso negativo**: aprovar quem não paga custa o valor emprestado (≈ R$ 14 mil); recusar um bom pagador custa só a margem de juros |
| **Modelo final** | Regressão Logística com `class_weight="balanced"` |
| **Entrega** | Pipeline serializado com `joblib` + interface web em Streamlit |

---

## 🏗️ Arquitetura

Os dados passam por um **Data Lakehouse** na **arquitetura medalhão**, armazenado em Parquet. Cada camada tem um papel claro, e qualquer etapa pode ser reprocessada a partir da anterior.

```text
  Sistema de crédito (CSV exportado)
           │  ingestão
           ▼
  🥉 BRONZE   dado bruto, exatamente como chegou + metadados de linhagem
           │  limpeza com regras fixas
           ▼
  🥈 PRATA    dado limpo, deduplicado, tipado e padronizado
           │  seleção de atributos + remoção de vazamento
           ▼
  🥇 OURO     tabela de atributos: só o que existe na hora da decisão
           │
           ▼
  🤖 PIPELINE scikit-learn  (limpeza → atributos → imputação → escala → encoding → modelo)
           │  joblib.dump
           ▼
  🌐 APP STREAMLIT   o analista digita o cliente e recebe a probabilidade de risco
```

### O que acontece em cada camada

**🥉 Bronze**: o CSV entra sem nenhuma alteração. São adicionados apenas metadados de ingestão (quando e de onde veio), o que permite reprocessar tudo se uma regra de limpeza estiver errada.

**🥈 Prata**: correções determinísticas, que não aprendem nada com os dados:

| Problema encontrado | Tratamento |
|---|---|
| 25 linhas duplicadas | Removidas **antes** da separação treino/teste |
| `estado_civil` com 13 grafias para 4 categorias | `strip` + `capitalize` + `Viuvo → Viúvo` |
| `idade` = −1, 0, 146, 999 | Vira ausente (será imputada no pipeline) |
| `renda_mensal` negativa | Vira ausente |
| `prazo` informado em anos | Convertido para meses |

**🥇 Ouro**: fica só o que o banco conhece no momento da concessão.

- ❌ `qtd_cobrancas` é removida: as cobranças só existem **depois** do atraso. É vazamento do alvo, e em uma versão anterior do estudo essa coluna levava a AUC artificialmente para 1,0.
- ❌ `id_cliente` é removido: não tem poder preditivo e é dado pessoal (LGPD).

### Engenharia de atributos

| Atributo | Fórmula | Intuição |
|---|---|---|
| `comprometimento` | (valor do empréstimo ÷ prazo) ÷ renda mensal | Fração da renda que vai para a parcela |
| `log_renda` | log(1 + renda mensal) | Reduz a assimetria da renda |

As duas são fórmulas linha a linha, sem estatísticas do conjunto, por isso não vazam informação do teste.

---

## 🛡️ Prevenção de vazamento de dados

Este foi o cuidado central do projeto. Um modelo com vazamento parece ótimo no notebook e falha em produção.

1. **Atributo do futuro removido**: `qtd_cobrancas` sai já na camada ouro.
2. **Duplicatas removidas antes do split**: a mesma linha não aparece no treino e no teste.
3. **Tudo que aprende fica dentro do `Pipeline`**: imputação, padronização e codificação são ajustadas só no treino.
4. **Validação cruzada recebe o pipeline inteiro**: cada fold reajusta o pré-processamento com seus próprios dados.
5. **A limpeza também está dentro do pipeline** (`FunctionTransformer`): um dado novo digitado no app passa exatamente pelas mesmas regras do treino.
6. **O conjunto de teste é usado uma única vez**, na avaliação final.

### Pipeline do scikit-learn

| Etapa | Colunas | Transformação |
|---|---|---|
| `prepara` | todas | Regras de limpeza + criação de `comprometimento` e `log_renda` |
| numérico | idade, renda, veículos, dependentes, valor, prazo, comprometimento, log_renda | `SimpleImputer(median, add_indicator=True)` → `StandardScaler` |
| ordinal | escolaridade | Imputação pela moda → `OrdinalEncoder` (Fundamental < Médio < Superior < Pós) |
| nominal | sexo, estado civil, emprego, moradia, mudança recente, cidade | Imputação → `OneHotEncoder(handle_unknown="ignore")` |
| `clf` | — | `LogisticRegression(class_weight="balanced")` |

---

## 🤖 Modelagem

Foram comparados três algoritmos e um modelo de referência, todos com `class_weight="balanced"` (o erro na classe rara pesa mais no treino).

| Modelo | Por que testar |
|---|---|
| **Dummy** (`most_frequent`) | Referência: sempre prevê "adimplente". Mostra se os outros aprenderam algo |
| **Regressão Logística** | Linear, interpretável e padrão de mercado em *credit scoring* |
| **Random Forest** | *Bagging* de árvores: captura não linearidades e interações |
| **HistGradientBoosting** | *Boosting* de árvores, geralmente forte em dados tabulares |

### Métricas escolhidas

A **acurácia foi descartada**: o Dummy, que nunca encontra um inadimplente, já teria ≈ 83%.

| Métrica | O que mede | Por que usar |
|---|---|---|
| **ROC-AUC** | Capacidade de ordenar clientes por risco | O modelo é um score de risco; independe do limiar |
| **PR-AUC** | Precisão × recall na classe positiva | Robusta ao desbalanceamento (a base é 0,165) |
| **Recall** | Inadimplentes encontrados ÷ inadimplentes reais | Mede diretamente o erro caro (falso negativo) |

---

## 📊 Resultados

### Teste final (holdout estratificado 75/25)

| Modelo | ROC-AUC | PR-AUC | Recall | AUC no treino |
|---|:---:|:---:|:---:|:---:|
| Dummy | 0,500 | 0,165 | 0,000 | 0,500 |
| **Regressão Logística** ✅ | **0,697** | **0,416** | **0,524** | 0,761 |
| Random Forest | 0,681 | 0,384 | 0,516 | 0,919 |
| HistGradientBoosting | 0,657 | 0,360 | 0,492 | 0,878 |

### Robustez

| Validação | ROC-AUC da Regressão Logística | Melhor modelo? |
|---|:---:|:---:|
| Validação cruzada (5 folds, treino) | 0,718 ± 0,038 | ✅ |
| Teste no holdout | 0,697 | ✅ |
| Teste temporal (treino 2021–23, teste 2024) | 0,722 | ✅ |

### Por que a Regressão Logística venceu

- **Melhor nas três métricas**, e o resultado se repete na validação cruzada e no teste temporal: não foi sorte da divisão.
- **Menor sobreajuste**: diferença de 0,06 entre treino e teste, contra 0,22–0,24 dos modelos de árvore, que decoraram o treino. Com 3 mil linhas e uma relação de risco quase linear, o modelo simples generaliza melhor.
- **Interpretável**: cada coeficiente vira um *odds ratio*. Isso permite explicar uma recusa ao cliente, como prevê o **art. 20 da LGPD** (direito à revisão de decisões automatizadas).

### O que mais pesa no risco

| Fator | *Odds ratio* | Efeito |
|---|:---:|---|
| Desempregado | 2,52 | 🔺 aumenta o risco |
| Comprometimento de renda (+1 desvio-padrão) | 1,82 | 🔺 |
| Mora de aluguel | 1,29 | 🔺 |
| Mais dependentes | 1,23 | 🔺 |
| Maior escolaridade | 0,76 | 🔻 reduz o risco |
| Maior idade | 0,69 | 🔻 |
| Empregado | 0,64 | 🔻 |

### Ajuste do limiar ao custo do erro

O app usa o limiar 0,5, mas o banco pode baixá-lo para capturar mais inadimplentes, aceitando revisar mais pedidos:

| Limiar | Recall | Precisão | % de clientes sinalizados |
|:---:|:---:|:---:|:---:|
| 0,3 | 83,9% | 19,5% | 71,1% |
| 0,4 | 69,4% | 22,5% | 50,9% |
| **0,5** | **52,4%** | **26,7%** | **32,4%** |
| 0,6 | 43,5% | 37,0% | 19,5% |

> Com ROC-AUC ≈ 0,70, o modelo é **apoio à decisão**, para priorizar a análise manual, e não um mecanismo de aprovação automática.

---

## 🌐 Deploy

- O **pipeline inteiro** (limpeza + pré-processamento + modelo) é salvo com `joblib`, não só o estimador. O arquivo final tem cerca de 9 KB.
- `modelo_meta.json` registra métricas, limiar, lista de cidades e as versões exatas das bibliotecas.
- `features.py` é um módulo separado porque o `joblib` guarda apenas uma *referência* às funções do `FunctionTransformer`. O app precisa importar as mesmas funções usadas no treino.
- O app Streamlit recebe os dados do cliente e mostra a **probabilidade de inadimplência**, a **faixa de risco** e o **comprometimento de renda**. A barra lateral exibe as métricas e as versões do modelo.

Exemplo: um cliente digitado com `estado_civil = "solteiro "` e `prazo = 1` (em anos) é corrigido automaticamente pelo pipeline antes da predição.

---

## 🚀 Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app abre em `http://localhost:8501`. Em **"Preencher com exemplo"**, use os botões **"Baixo risco"** e **"Alto risco"** para ver o modelo funcionando.

Para reproduzir o treino, execute o notebook `N3_Modelo_Preditivo_Inadimplencia.ipynb` (localmente ou no Google Colab).

> ⚠️ **Versões:** o `.joblib` foi salvo com scikit-learn 1.9.1 e Python 3.13. Um arquivo joblib depende da versão da biblioteca que o gerou, por isso o notebook gera o modelo e o `requirements.txt` juntos. Use sempre os dois da mesma execução.
>
> 🔒 Só carregue arquivos pickle/joblib de fontes confiáveis: eles podem executar código ao serem abertos.

---

## 📁 Estrutura do repositório

```text
risco-credito-lakehouse/
├── N3_Modelo_Preditivo_Inadimplencia.ipynb   # Notebook completo e já executado
├── features.py                               # Limpeza e engenharia de atributos (treino e app)
├── app.py                                    # Interface Streamlit
├── modelo_inadimplencia.joblib               # Pipeline treinado
├── modelo_meta.json                          # Métricas, limiar, cidades e versões
├── requirements.txt                          # Versões exatas do ambiente de treino
├── credito_sujo.csv                          # Base de origem
├── lakehouse/
│   ├── bronze/contratos_credito.parquet
│   ├── prata/contratos_credito.parquet
│   └── ouro/features_inadimplencia.parquet
└── roteiro-apresentação.md                   # Roteiro da apresentação acadêmica
```

---

## 💡 Aprendizados

- **Vazamento de dados é o erro mais perigoso**: uma única coluna "do futuro" levou a AUC a 1,0. Pensar em *o que eu sei no momento da decisão* guiou toda a seleção de atributos.
- **Modelo mais complexo não é modelo melhor**: com poucos dados, os modelos de árvore sobreajustaram e a Regressão Logística generalizou melhor.
- **A métrica tem que refletir o custo do negócio**: em crédito, acurácia engana; ROC-AUC, PR-AUC e recall contam a história certa.
- **Deploy começa no treino**: colocar a limpeza dentro do pipeline e versionar as dependências é o que faz o modelo funcionar fora do notebook.

---

<div align="center">

**Maria A. Giuliari** · **Mariele Vieira**

Projeto da disciplina de Análise Preditiva · Engenharia de Software · Católica SC · 2026

Orientação: Prof. Luiz C. Camargo, PhD

</div>
