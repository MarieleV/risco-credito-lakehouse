# 🎤 Roteiro de Apresentação · N3 Modelo Preditivo de Inadimplência

Análise Preditiva · Engenharia de Software · Católica SC · Prof. Luiz C. Camargo
Alunas: Maria A. Giuliari e Mariele Vieira · **Apresentação: 27/11/2026** · Duração: **≈ 10 min**

> **Como usar este arquivo**
>
> 1. Leia a **Cola rápida** até saber os números de cabeça.
> 2. Treine as **falas** de cada seção em voz alta, cronometrando. Não precisa decorar palavra por palavra: decore a **frase-chave** 🔑 de cada parte.
> 3. Ensaie a **demonstração** pelo menos uma vez no computador da apresentação.
> 4. Estude as **perguntas do professor** em dupla: uma pergunta, a outra responde.

---

## 📋 Cola rápida (decorar)

| O quê | Valor |
|---|---|
| Base | ≈ 3 mil contratos, 2021–2024, mesma base da N2 |
| Inadimplentes | ≈ 17% (16,5% no teste), atraso > 90 dias |
| Custo do erro caro (FN) | ≈ R$ 14 mil (valor médio emprestado) |
| Duplicatas removidas | 25 |
| Grafias de `estado_civil` | 13 → 4 categorias |
| Coluna com vazamento | `qtd_cobrancas` (na N2 levou a AUC a 1,0) |
| Separação | 75/25 estratificado, `random_state=42`, CV de 5 folds no treino |
| **Modelo escolhido** | **Regressão Logística** |
| ROC-AUC / PR-AUC / Recall (teste) | **0,697 / 0,416 / 0,524** |
| ROC-AUC na validação cruzada | 0,718 ± 0,038 |
| ROC-AUC no teste temporal (2024) | 0,722 |
| Gap treino − teste | LR **0,06** · RF 0,24 · HGB 0,22 |
| Matriz de confusão (teste) | Achou **65 de 124** inadimplentes · 59 falsos negativos |
| Fator de maior risco | Desempregado: *odds ratio* **2,52** |
| Limiar 0,4 | Recall ≈ 69%, mas sinaliza ≈ 51% dos clientes |
| Acurácia do Dummy | ≈ 83%, com recall 0 |

### Pontos da avaliação

| Item | Peso | Onde está |
|---|:---:|---|
| 1 · Domínio | 1,0 | Seção 1 do roteiro |
| 2 · Pipeline de dados | 2,0 | Seção 2 do roteiro |
| 3.1 · Modelos | 2,0 | Seção 3.1 do roteiro |
| 3.2 · Métricas | 2,0 | Seção 3.2 do roteiro |
| 3.3 · Comparação e escolha | 1,0 | Seção 3.3 do roteiro |
| 4 · Deploy | 2,0 | Seção 4 do roteiro |

---

## ✅ Checklist antes de apresentar

**Na véspera**
- [ ] Rodar `pip install -r requirements.txt` no computador da apresentação.
- [ ] Rodar `streamlit run app.py` e testar os dois botões de exemplo.
- [ ] Deixar o notebook aberto **já executado**, com as saídas visíveis (não rodar ao vivo).
- [ ] Ensaiar cronometrando: se passar de 11 min, cortar fala, não slide.

**10 minutos antes**
- [ ] Terminal aberto na pasta do projeto com o Streamlit **já rodando** em `localhost:8501`.
- [ ] Abas na ordem: notebook (§1) → navegador com o app.
- [ ] Zoom do navegador e do notebook em 125–150% para o fundo da sala enxergar.
- [ ] Notificações do computador desligadas.

### Divisão sugerida entre as duas

| Parte | Quem | Tempo |
|---|---|---|
| Abertura + 1 · Domínio + 2 · Pipeline | Pessoa A | ≈ 4 min |
| 3.1 · Modelos + 3.2 · Métricas + 3.3 · Escolha | Pessoa B | ≈ 4 min |
| 4 · Deploy (demo) + Fechamento | Pessoa A ou B | ≈ 2 min |

> Combinem a frase de passagem: *"Agora a [nome] vai mostrar como treinamos e escolhemos o modelo."*

---

## 🗣️ Roteiro com falas

### 0 · Abertura (≈ 30 s)

🖥️ **Tela:** topo do notebook (título e tabela de itens).

> "Bom dia, professor. Nosso projeto é um modelo para prever **inadimplência** em empréstimos pessoais, usando a mesma base da N2. Vamos seguir os itens da avaliação: domínio, pipeline de dados, modelos e métricas, e no final o deploy funcionando."

---

### 1 · Domínio do problema · 1,0 ponto · ≈ 1 min

🖥️ **Tela:** §1 do notebook.

> "Uma instituição financeira de Santa Catarina concede empréstimos, e parte dos clientes atrasa mais de 90 dias. Quando o cliente pede o crédito, o analista não sabe se ele vai pagar.
>
> O objetivo é estimar, **no momento da solicitação**, a probabilidade de inadimplência, para apoiar a decisão de aprovar, recusar ou mandar para análise manual.
>
> O alvo é `inadimplente`: 1 se atrasou mais de 90 dias. É uma **classificação binária desbalanceada**, com cerca de 17% de inadimplentes.
>
> E os erros não custam o mesmo. **Aprovar quem não paga, o falso negativo**, custa o valor emprestado, uns 14 mil reais. Recusar um bom pagador custa só a margem de juros. Por isso o **falso negativo é o erro mais caro**, e isso guiou a escolha das métricas."

🔑 **Frase-chave:** *"Prever, na hora do pedido, quem vai atrasar mais de 90 dias; o erro caro é o falso negativo."*

---

### 2 · Pipeline de dados · 2,0 pontos · ≈ 2min30

🖥️ **Tela:** §2, no diagrama bronze → prata → ouro. Depois §2.6 (tabela do pipeline) e o resumo de vazamento.

> "Organizamos os dados num **Data Lakehouse com arquitetura medalhão**, em arquivos Parquet.
>
> Na **bronze**, o CSV entra exatamente como veio, só com metadados de ingestão. Se uma regra de limpeza estiver errada, dá para reprocessar a partir daqui.
>
> Na **prata**, aplicamos as correções da N2: removemos **25 duplicatas**, padronizamos as **13 grafias** de estado civil, idades e rendas impossíveis viraram ausentes para serem imputadas, e o prazo que estava em anos virou meses.
>
> Na **ouro**, fica só o que existe **na hora da decisão**. Tiramos `qtd_cobrancas`, porque cobrança só existe **depois** do atraso: é vazamento do alvo, e na N2 ela levou a AUC a 1,0. Tiramos também o `id_cliente`, que não tem poder preditivo e é dado pessoal.
>
> Criamos dois atributos: o **comprometimento**, que é parcela dividida pela renda, e o **log da renda**.
>
> Separamos **75/25 estratificado**, com semente 42, e usamos validação cruzada de 5 folds só no treino.
>
> O principal cuidado foi o **vazamento**. Imputação, padronização e encoding ficam **dentro do `Pipeline`**, então são ajustados só com o treino. E até a limpeza está dentro do pipeline, com um `FunctionTransformer`. Assim, um dado novo digitado no app passa pelas mesmas regras do treino."

🔑 **Frase-chave:** *"Bronze guarda, prata limpa, ouro só tem o que existe na hora da decisão; tudo que aprende fica dentro do pipeline."*

**Os 6 cuidados contra vazamento** (se o professor pedir para listar):
1. `qtd_cobrancas` removida.
2. Duplicatas removidas **antes** do split.
3. Imputação, escala e encoding ajustados só no treino (dentro do `Pipeline`).
4. Validação cruzada recebe o pipeline inteiro.
5. Atributos criados são fórmulas linha a linha (não usam média nem mediana do conjunto).
6. Teste usado uma única vez.

---

### 3.1 · Modelos · 2,0 pontos · ≈ 1min30

🖥️ **Tela:** §3.1, tabela dos modelos e depois a tabela de validação cruzada.

> "Comparamos três algoritmos e um modelo de referência.
>
> O **Dummy** sempre diz 'adimplente'. Ele serve para provar que os outros aprenderam alguma coisa além do óbvio.
>
> A **Regressão Logística** é linear, interpretável e padrão em *credit scoring*.
>
> A **Random Forest** é um conjunto de árvores por *bagging*, que captura relações não lineares.
>
> E o **HistGradientBoosting** é *boosting* de árvores, geralmente forte em dados tabulares.
>
> Todos usam `class_weight='balanced'`: o erro na classe rara pesa mais no treino. Sem isso, o modelo tenderia a prever sempre 'adimplente'."

🔑 **Frase-chave:** *"Um baseline, um linear interpretável e dois de árvores, todos balanceados."*

---

### 3.2 · Métricas · 2,0 pontos · ≈ 1min30

🖥️ **Tela:** §3.2.

> "Não usamos acurácia. O Dummy teria **83% de acurácia** e não encontraria nenhum inadimplente.
>
> Escolhemos três métricas pelo custo do erro:
>
> **ROC-AUC** mede se o modelo **ordena** bem os clientes por risco. Vai de 0 a 1, 0,5 é chute, e acima de 0,7 já é útil em crédito. Não depende do limiar.
>
> **PR-AUC** olha só para a classe positiva, precisão contra recall. É **robusta ao desbalanceamento**: a linha de base é a própria proporção de inadimplentes, 0,165.
>
> **Recall** é quantos inadimplentes o modelo encontra entre todos os que existem. Ele mede **direto o erro caro**, o falso negativo."

| Métrica | Mede | Faixa / bom valor | Por que usar |
|---|---|---|---|
| **ROC-AUC** | Ordenação por risco | 0–1; 0,5 = chute; > 0,7 útil | Score de risco, independe do limiar |
| **PR-AUC** | Precisão × recall na classe positiva | 0–1; base = 0,165 | Robusta ao desbalanceamento |
| **Recall** | VP ÷ (VP + FN) | 0–1; Dummy = 0 | Mede o falso negativo |

🔑 **Frase-chave:** *"ROC-AUC ordena, PR-AUC aguenta o desbalanceamento, recall mede o erro caro."*

---

### 3.3 · Comparação e escolha · 1,0 ponto · ≈ 1 min

🖥️ **Tela:** §3.3, tabela de resultados no teste.

| Modelo | ROC-AUC | PR-AUC | Recall | AUC treino | Gap |
|---|:---:|:---:|:---:|:---:|:---:|
| Dummy | 0,500 | 0,165 | 0,000 | 0,500 | 0 |
| **Regressão Logística** | **0,697** | **0,416** | **0,524** | 0,761 | **0,06** |
| Random Forest | 0,681 | 0,384 | 0,516 | 0,919 | 0,24 |
| HistGradientBoosting | 0,657 | 0,360 | 0,492 | 0,878 | 0,22 |

> "Escolhemos a **Regressão Logística** por quatro motivos.
>
> Um: foi a **melhor nas três métricas** no teste, e a validação cruzada aponta o mesmo.
>
> Dois: continua a melhor no **teste temporal**, treinando até 2023 e testando em 2024, com ROC-AUC de 0,72.
>
> Três: tem o **menor sobreajuste**. A Random Forest tem 0,92 no treino e 0,68 no teste: decorou os dados.
>
> Quatro: é **interpretável**. Cada coeficiente vira um *odds ratio*. Por exemplo, estar desempregado multiplica a chance de inadimplência por 2,5. Isso permite explicar uma recusa ao cliente, como pede o **artigo 20 da LGPD**.
>
> Sendo honestas: um AUC de 0,70 é **moderado**. O modelo serve como **apoio** à decisão, não como aprovação automática."

🔑 **Frase-chave:** *"Melhor nas três métricas, estável no tempo, menor sobreajuste e explicável."*

---

### 4 · Deploy · 2,0 pontos · ≈ 1min30

🖥️ **Tela:** §4 rapidamente → navegador com o app.

> "Para o deploy, salvamos com `joblib` o **pipeline inteiro**: limpeza, pré-processamento e modelo, não só o estimador. Junto vão o `modelo_meta.json`, com métricas e limiar, e o `requirements.txt` com as **versões exatas**, porque um arquivo joblib depende da versão do scikit-learn que o gerou.
>
> O `features.py` é separado porque o joblib salva só uma **referência** às funções de limpeza, e o app precisa importar as mesmas funções.
>
> Agora a interface em Streamlit."

**Demonstração passo a passo**
1. Rolar até a seção **"Sobre o modelo"**, no fim da página: métricas do modelo, limiar e versões.
2. No topo, clicar em **"Baixo risco"** → **Calcular risco** → 🟢 baixo risco.
   > "Cliente de 42 anos, empregada, casa própria, parcela pequena em relação à renda."
3. No topo, clicar em **"Alto risco"** → **Calcular risco** → 🔴 alto risco.
   > "Cliente de 23 anos, desempregado, aluguel, três dependentes e uma parcela que consome quase 90% da renda."
4. Apontar a **régua de risco** (onde o cliente fica em relação à média da carteira e ao limiar), a **renda comprometida** e o **risco em relação à média**.
5. Abrir **"Dados enviados ao modelo"**, no fim do parecer: é exatamente o que entra no pipeline salvo.

> "Um último cuidado: arquivo pickle ou joblib **só de fonte confiável**, porque ele pode executar código ao ser carregado."

🛟 **Plano B, se o app não abrir:** ir para a célula de demonstração no fim do §4 do notebook. Ela carrega o `.joblib` e prevê dois clientes (14,9% e 99,3%). Destaque que o cliente 2 foi digitado com `"solteiro "` e prazo `1` (em anos), e o pipeline corrigiu tudo sozinho.

🔑 **Frase-chave:** *"Salvamos o pipeline inteiro, com as versões, e o app usa exatamente as mesmas regras do treino."*

---

### 5 · Fechamento (≈ 30 s)

> "Resumindo: um pipeline de dados em camadas com cuidado contra vazamento, quatro modelos comparados com métricas adequadas ao custo do erro, a Regressão Logística escolhida por desempenho, estabilidade e interpretabilidade, e o modelo funcionando numa aplicação. Obrigada, estamos à disposição para perguntas."

---

## ❓ Perguntas que o professor pode fazer

### Sobre métricas e resultados

**"Por que não usar acurácia?"**
O Dummy, que sempre diz "adimplente", tem ≈ 83% de acurácia e não encontra nenhum inadimplente. Com classes desbalanceadas, a acurácia engana.

**"Um AUC de 0,70 é bom?"**
É moderado. Serve como **apoio** para priorizar a análise manual, não como decisão automática. Baixando o limiar para 0,4, o recall sobe para ≈ 69%, mas o modelo sinaliza metade dos clientes.

**"Explique a matriz de confusão."**
No teste, com limiar 0,5: dos **124 inadimplentes**, o modelo achou **65** (recall 52%) e deixou passar **59** (falsos negativos). Dos 626 adimplentes, 448 foram aprovados corretamente e 178 foram sinalizados à toa (falsos positivos).

| | Previsto adimplente | Previsto inadimplente |
|---|:---:|:---:|
| **Real adimplente** | 448 (VN) | 178 (FP) |
| **Real inadimplente** | 59 (FN) | 65 (VP) |

**"Por que o limiar é 0,5? Não deveria ser menor, já que o FN é caro?"**
Mantivemos 0,5 para avaliar todos os modelos igual. Mas mostramos a tabela de limiares: com 0,3, o recall vai a 84%, só que 71% dos clientes seriam sinalizados. A escolha final é do negócio, e o app mostra a probabilidade para o analista decidir.

| Limiar | Recall | Precisão | % sinalizados |
|:---:|:---:|:---:|:---:|
| 0,3 | 84% | 20% | 71% |
| 0,4 | 69% | 23% | 51% |
| **0,5** | **52%** | **27%** | **32%** |
| 0,6 | 44% | 37% | 20% |

**"Qual a diferença entre ROC-AUC e PR-AUC?"**
A ROC usa a taxa de falsos positivos, que fica pequena quando há muitos negativos, então ela pode parecer otimista em base desbalanceada. A PR-AUC usa a precisão, que sente diretamente os falsos positivos, e sua linha de base é a prevalência (0,165), não 0,5.

### Sobre os modelos

**"Por que a Random Forest perdeu, se é mais poderosa?"**
Ela sobreajustou: AUC 0,92 no treino e 0,68 no teste. Com 3 mil linhas e uma relação de risco quase linear, o modelo simples generaliza melhor.

**"O que significa `class_weight='balanced'`?"**
Os erros na classe rara pesam mais no treino, na proporção inversa da frequência. Sem isso, o modelo tenderia a prever sempre a classe majoritária.

**"Por que não usaram SMOTE / oversampling?"**
O `class_weight` resolve o mesmo problema sem criar dados sintéticos. E se o oversampling for feito antes do split, causa vazamento. Seria preciso colocá-lo dentro do pipeline, com `imblearn`.

**"O que é *odds ratio*? Como lê o 2,52?"**
É quanto um fator multiplica a **chance** (*odds*) de inadimplência. Estar desempregado multiplica a chance por 2,52. Acima de 1 aumenta o risco, abaixo de 1 reduz. Nas variáveis numéricas, o efeito é por 1 desvio-padrão, porque elas foram padronizadas.

**"Fizeram ajuste de hiperparâmetros?"**
Não fizemos busca exaustiva. Usamos valores conservadores para controlar o sobreajuste (árvores com `min_samples_leaf=10`, boosting com `max_depth=3`). Um próximo passo seria um `GridSearchCV` dentro da validação cruzada.

### Sobre dados e vazamento

**"O que é vazamento de dados no seu projeto?"**
O caso clássico é `qtd_cobrancas`: cobranças só existem depois do atraso. Na N2, ela levou a AUC a 1,0. O outro tipo seria ajustar imputação ou escala antes do split; evitamos colocando tudo dentro do `Pipeline`.

**"Por que holdout estratificado, se na N2 vocês defenderam a divisão temporal?"**
O enunciado pede `stratify`. Mesmo assim, fizemos a checagem temporal (treino 2021–23, teste 2024), e a Regressão Logística continua a melhor (ROC-AUC 0,722).

**"Por que estratificar?"**
Para manter os ≈ 17% de inadimplentes iguais no treino e no teste. Sem isso, o teste poderia ficar com proporção diferente por acaso e distorcer as métricas.

**"Por que imputar pela mediana?"**
A renda e a idade têm valores extremos, e a mediana não é puxada por eles como a média. O `add_indicator=True` também cria uma coluna dizendo que o valor faltava, porque o fato de faltar pode ser informativo.

**"E se aparecer uma cidade nova no app?"**
O `OneHotEncoder` usa `handle_unknown="ignore"`: a cidade desconhecida vira tudo zero e o modelo continua funcionando com os outros atributos.

**"Por que o `log_renda`?"**
A renda é muito assimétrica (poucas rendas muito altas). O log aproxima a distribuição e ajuda um modelo linear.

**"Por que Lakehouse e Parquet?"**
O Parquet é colunar, compacto e guarda os tipos das colunas (o CSV não guarda). O lakehouse separa dado bruto, limpo e pronto para o modelo, então dá para auditar e reprocessar qualquer etapa.

**"O modelo usa `sexo`. Isso não é discriminatório?"**
É uma boa pergunta. A coluna estava na base e não aparece entre os fatores mais fortes. Em produção, o correto seria testar o modelo sem ela e medir se as taxas de recusa são justas entre os grupos, seguindo o princípio de **não discriminação da LGPD** (art. 6º, IX).

### Sobre o deploy

**"Por que `features.py` separado?"**
O joblib salva só uma referência às funções do `FunctionTransformer`. O app precisa importar as mesmas funções para carregar o modelo.

**"Por que salvar o pipeline inteiro e não só o modelo?"**
Porque o dado novo precisa passar pelas mesmas transformações do treino (limpeza, imputação com a mediana do treino, escala, encoding). Salvando só o estimador, o app teria que refazer tudo à mão, com risco de erro.

**"Qual o risco do joblib/pickle?"**
Ele pode executar código ao ser carregado. Só se deve abrir arquivo de fonte confiável.

**"Como manteriam o modelo em produção?"**
Monitorando a taxa de inadimplência real e a distribuição dos dados de entrada (*data drift*). Se mudarem, retreinamos com dados novos, sempre gerando o `.joblib` e o `requirements.txt` juntos.

**"Como melhorariam o modelo?"**
Mais dados, ajuste de hiperparâmetros, calibração das probabilidades e variáveis externas como histórico de crédito ou score de bureau.

---

## 📖 Glossário rápido

| Termo | Em uma linha |
|---|---|
| **Vazamento (*leakage*)** | Informação que não existiria na hora da previsão entrando no treino |
| **Sobreajuste (*overfitting*)** | Modelo decora o treino e vai mal em dados novos (gap grande treino × teste) |
| **Holdout** | Separar uma parte dos dados só para o teste final |
| **Validação cruzada** | Dividir o treino em *k* partes e treinar/avaliar *k* vezes, alternando |
| **Estratificação** | Manter a proporção das classes em cada parte |
| **Falso negativo (FN)** | Modelo diz "vai pagar" e o cliente não paga |
| **Falso positivo (FP)** | Modelo diz "não vai pagar" e o cliente pagaria |
| **Limiar** | Probabilidade a partir da qual o cliente é classificado como inadimplente |
| ***Odds ratio*** | Quanto um fator multiplica a chance do evento |
| **Arquitetura medalhão** | Camadas bronze (bruto), prata (limpo) e ouro (pronto para uso) |
| **`FunctionTransformer`** | Transforma uma função Python comum em etapa do pipeline |
| ***Data drift*** | Mudança na distribuição dos dados ao longo do tempo |

---

## ⚠️ Erros a evitar

- **Não ler o slide/notebook.** Olhe para o professor e use a tela só para apontar.
- **Não dizer "o modelo acerta 70%".** ROC-AUC não é taxa de acerto. Diga: *"em 70% das vezes, o modelo dá um risco maior a um inadimplente sorteado do que a um bom pagador sorteado"*.
- **Não vender o modelo como perfeito.** Mostrar a limitação (AUC moderado, apoio à decisão) conta a favor.
- **Não rodar o notebook ao vivo.** Ele já está executado; rodar de novo pode demorar ou dar erro de versão.
- **Se não souber uma resposta:** *"Não testamos isso, mas a forma de verificar seria..."* é melhor do que inventar.
