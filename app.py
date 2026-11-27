"""
app.py — Interface Streamlit do modelo de inadimplência (Avaliação N3).

Como rodar (na pasta com app.py, features.py, modelo_inadimplencia.joblib e modelo_meta.json):
    pip install -r requirements.txt
    streamlit run app.py

O tema (cores e fontes) fica em .streamlit/config.toml; os detalhes visuais extras,
no bloco CSS abaixo.

SEGURANÇA: joblib/pickle pode executar código ao carregar. Este app só carrega o
arquivo gerado pelo nosso próprio notebook (fonte confiável).
"""
import json
from html import escape
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

import features  # necessário: o pipeline salvo referencia features.preparar_entrada  # noqa: F401

PASTA = Path(__file__).parent
ARQ_MODELO = PASTA / "modelo_inadimplencia.joblib"
ARQ_META = PASTA / "modelo_meta.json"

st.set_page_config(page_title="Risco de Inadimplência", page_icon="💳", layout="wide")

# ---------------------------------------------------------------------------
# Estilo: escala de risco, régua e ajustes finos que o tema não cobre
# ---------------------------------------------------------------------------
CORES_RISCO = {
    "baixo": ("#2E7D5B", "#E3F0E9"),     # (tinta, fundo)
    "moderado": ("#B07A12", "#F6EDD9"),
    "alto": ("#B23A3A", "#F6E3E1"),
}

st.html("""
<style>
  :root {
    --tinta: #12302F; --grafite: #4D5B5A; --linha: #C9D2CE; --papel: #F3F5F2;
    --titulo: "Familjen Grotesk", "Public Sans", sans-serif;
  }
  .block-container { padding-top: 2.5rem; max-width: 1240px; }
  h1 { letter-spacing: -0.02em; line-height: 1.05; }
  h3 { margin-top: .5rem; }

  .abertura { max-width: 62ch; color: var(--grafite); font-size: 1.05rem; line-height: 1.55;
              margin: -.25rem 0 1.25rem; }

  /* Parecer: o elemento de destaque da página */
  .parecer { border-radius: 10px; padding: 1.5rem 1.5rem 1.25rem; background: var(--fundo);
             color: var(--tinta); }
  .parecer .faixa { font-family: var(--titulo); font-weight: 600; font-size: 1.05rem;
                    color: var(--cor); margin: 0; }
  .parecer .prob { font-family: var(--titulo); font-weight: 700; color: var(--cor);
                   font-size: clamp(3.2rem, 6vw, 4.6rem); line-height: 1; margin: .35rem 0 .2rem;
                   font-variant-numeric: tabular-nums; letter-spacing: -0.03em; }
  .parecer .prob-legenda { color: var(--grafite); margin: 0 0 1.4rem; font-size: .95rem; }
  .parecer .recomendacao { font-size: 1rem; line-height: 1.5; margin: 1.4rem 0 0; }

  /* Régua de risco: 0% a 100%, com zonas, média da carteira e limiar */
  .regua { position: relative; height: 4.6rem; margin: 0 .25rem; }
  .regua .trilho { position: absolute; top: 1.6rem; left: 0; right: 0; height: .55rem;
                   border-radius: 99px; overflow: hidden; display: flex; }
  .regua .trilho span { height: 100%; opacity: .55; }
  .regua .ponteiro { position: absolute; top: 0; width: 0; animation: desliza .9s cubic-bezier(.2,.8,.2,1); }
  .regua .ponteiro::before { content: ""; position: absolute; left: -1px; top: .35rem; width: 3px;
                             height: 2.1rem; background: var(--tinta); border-radius: 2px; }
  .regua .ponteiro::after { content: ""; position: absolute; left: -.4rem; top: 0;
                            border: .4rem solid transparent; border-top-color: var(--tinta); }
  .regua .marca { position: absolute; top: 2.15rem; font-size: .78rem; color: var(--grafite);
                  white-space: nowrap; line-height: 1.25; font-variant-numeric: tabular-nums; }
  .regua .marca::before { content: ""; display: block; width: 1px; height: .55rem;
                          background: var(--grafite); margin-bottom: .2rem; }
  .regua .marca.direita { transform: translateX(-100%); text-align: right; }
  .regua .marca.direita::before { margin-left: auto; }
  @keyframes desliza { from { left: 0; } }
  @media (prefers-reduced-motion: reduce) { .regua .ponteiro { animation: none; } }

  /* Números de apoio */
  .apoio { display: grid; grid-template-columns: 1fr 1fr; gap: .9rem 1.5rem; margin: 1.25rem 0 0;
           padding: 1.1rem 0 0; border-top: 1px solid var(--linha); }
  /* zera o recuo que o Streamlit aplica a listas */
  .apoio, .ficha, .apoio dt, .apoio dd, .ficha dt, .ficha dd {
    padding-inline: 0 !important; margin-inline: 0 !important; }
  .apoio dt { color: var(--grafite); font-size: .85rem; margin: 0; }
  .apoio dd { margin: .1rem 0 0; font-family: var(--titulo); font-weight: 600; font-size: 1.35rem;
              font-variant-numeric: tabular-nums; }

  /* Estado vazio do parecer */
  .vazio { border: 1px dashed var(--linha); border-radius: 10px; padding: 2rem 1.5rem;
           color: var(--grafite); line-height: 1.55; }
  .vazio strong { color: var(--tinta); font-family: var(--titulo); font-size: 1.15rem;
                  display: block; margin-bottom: .35rem; }

  /* Barra lateral */
  .ficha { margin: 0 0 1rem; display: grid; grid-template-columns: 1fr auto; gap: .5rem 1rem;
           align-items: baseline; }
  .ficha dt { color: var(--grafite); font-size: .9rem; }
  .ficha dd { margin: 0; text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
  .nota { color: var(--grafite); font-size: .85rem; line-height: 1.5; }

  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .apoio { grid-template-columns: 1fr; }
  }
</style>
""")


def brl(valor: float) -> str:
    """Formata em reais no padrão brasileiro: R$ 1.234,56."""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor: float, casas: int = 1) -> str:
    """Formata percentual com vírgula decimal: 16,6%."""
    return f"{valor:.{casas}%}".replace(".", ",")


@st.cache_resource
def carregar_modelo():
    """Carrega o pipeline completo (limpeza + pré-processamento + regressão logística)."""
    modelo = joblib.load(ARQ_MODELO)  # fonte confiável: gerado pelo nosso notebook
    meta = json.loads(ARQ_META.read_text(encoding="utf-8"))
    return modelo, meta


if not ARQ_MODELO.exists() or not ARQ_META.exists():
    st.error("Arquivos do modelo não encontrados. Rode o notebook para gerar "
             "`modelo_inadimplencia.joblib` e `modelo_meta.json` nesta pasta.")
    st.stop()

modelo, meta = carregar_modelo()
LIMIAR = meta["limiar"]
TAXA_BASE = meta["taxa_inadimplencia_treino"]

# ---------------------------------------------------------------------------
# Exemplos prontos (para a demonstração em aula)
# ---------------------------------------------------------------------------
EXEMPLOS = {
    "Baixo risco": dict(
        idade=42, sexo="F", estado_civil="Casado", escolaridade="Superior", renda_mensal=6500.0,
        empregado="Sim", tipo_moradia="Própria", mudou_recentemente="Não", num_veiculos=1,
        dependentes=1, cidade="Blumenau", valor_emprestimo=8000.0, prazo=36),
    "Alto risco": dict(
        idade=23, sexo="M", estado_civil="Solteiro", escolaridade="Fundamental", renda_mensal=1400.0,
        empregado="Não", tipo_moradia="Alugada", mudou_recentemente="Sim", num_veiculos=0,
        dependentes=3, cidade="Joinville", valor_emprestimo=15000.0, prazo=12),
}
if "cliente" not in st.session_state:
    st.session_state.cliente = EXEMPLOS["Baixo risco"]

# ---------------------------------------------------------------------------
# Barra lateral: informações do modelo
# ---------------------------------------------------------------------------
with st.sidebar:
    st.subheader("Sobre o modelo")
    m = meta["metricas_teste"]
    st.html(f"""
      <dl class="ficha">
        <dt>Algoritmo</dt><dd>{escape(meta['modelo'])}</dd>
        <dt>ROC-AUC</dt><dd>{m['ROC-AUC']:.3f}</dd>
        <dt>PR-AUC</dt><dd>{m['PR-AUC']:.3f}</dd>
        <dt>Recall</dt><dd>{m['Recall']:.3f}</dd>
        <dt>Limiar de decisão</dt><dd>{pct(LIMIAR, 0)}</dd>
        <dt>Inadimplência média</dt><dd>{pct(TAXA_BASE)}</dd>
      </dl>
      <p class="nota">Métricas medidas no conjunto de teste ({escape(meta['protocolo'])},
      random_state={meta['random_state']}). Treinado em {escape(meta['treinado_em'])}.</p>
    """)
    with st.expander("Versões das bibliotecas"):
        st.code("\n".join(f"{k}=={v}" for k, v in meta["versoes"].items()), language="text")
    st.caption("Só carregue arquivos .joblib ou .pickle de fontes confiáveis: "
               "ao abrir, eles podem executar código.")

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("Avaliação de risco de inadimplência")
st.html('<p class="abertura">Preencha a solicitação de crédito e o modelo estima a chance de o '
        'cliente atrasar mais de 90 dias. O resultado apoia a decisão do analista, '
        'não a substitui.</p>')

e0, e1, e2, _ = st.columns([1.3, 1, 1, 3], vertical_alignment="center")
e0.markdown("Preencher com exemplo:")
for col, (rotulo, dados) in zip((e1, e2), EXEMPLOS.items()):
    if col.button(rotulo, width="stretch"):
        st.session_state.cliente = dados
        st.rerun()

c = st.session_state.cliente
ESTADOS = ["Casado", "Solteiro", "Divorciado", "Viúvo"]
ESCOLAS = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
MORADIAS = ["Própria", "Alugada", "Financiada", "Com os pais"]
CIDADES = meta["cidades"]
PRAZOS = [12, 24, 36, 48, 60]
OPCOES_EMP = ["Sim", "Não", "Não informado"]

esquerda, direita = st.columns([1.35, 1], gap="large")

# ---------------------------------------------------------------------------
# Formulário
# ---------------------------------------------------------------------------
with esquerda:
    with st.form("solicitacao", border=False):
        st.subheader("Cliente")
        a1, a2 = st.columns(2)
        idade = a1.number_input("Idade", 18, 100, int(c["idade"]))
        sexo = a2.selectbox("Sexo", ["F", "M"], index=["F", "M"].index(c["sexo"]))
        a3, a4 = st.columns(2)
        estado_civil = a3.selectbox("Estado civil", ESTADOS, index=ESTADOS.index(c["estado_civil"]))
        escolaridade = a4.selectbox("Escolaridade", ESCOLAS, index=ESCOLAS.index(c["escolaridade"]))
        a5, a6 = st.columns(2)
        cidade = a5.selectbox("Cidade (SC)", CIDADES, index=CIDADES.index(c["cidade"]))
        tipo_moradia = a6.selectbox("Moradia", MORADIAS, index=MORADIAS.index(c["tipo_moradia"]))
        a7, a8 = st.columns(2)
        dependentes = a7.number_input("Dependentes", 0, 10, int(c["dependentes"]))
        mudou = a8.radio("Mudou de endereço no último ano?", ["Não", "Sim"],
                         index=["Não", "Sim"].index(c["mudou_recentemente"]), horizontal=True)

        st.subheader("Renda e empréstimo")
        b1, b2 = st.columns(2)
        empregado = b1.selectbox("Está empregado?", OPCOES_EMP,
                                 index=OPCOES_EMP.index(c["empregado"]))
        renda = b2.number_input("Renda mensal (R$)", 0.0, 500000.0, float(c["renda_mensal"]),
                                step=100.0)
        b3, b4, b5 = st.columns(3)
        valor = b3.number_input("Valor pedido (R$)", 100.0, 500000.0,
                                float(c["valor_emprestimo"]), step=500.0)
        prazo = b4.selectbox("Prazo (meses)", PRAZOS, index=PRAZOS.index(int(c["prazo"])))
        num_veiculos = b5.number_input("Veículos", 0, 10, int(c["num_veiculos"]))

        enviar = st.form_submit_button("Calcular risco", type="primary", width="stretch")


# ---------------------------------------------------------------------------
# Parecer
# ---------------------------------------------------------------------------
def regua(prob: float) -> str:
    """Régua horizontal de 0% a 100% com as zonas de risco, a média da carteira e o limiar."""
    zonas = [(TAXA_BASE, "baixo"), (LIMIAR - TAXA_BASE, "moderado"), (1 - LIMIAR, "alto")]
    trilho = "".join(f'<span style="width:{w:.1%};background:{CORES_RISCO[k][0]}"></span>'
                     for w, k in zonas)
    return f"""
      <div class="regua" role="img"
           aria-label="Probabilidade de {pct(prob)}; média da carteira {pct(TAXA_BASE)}; limiar {pct(LIMIAR, 0)}">
        <div class="trilho">{trilho}</div>
        <div class="ponteiro" style="left:{min(prob, 1):.2%}"></div>
        <div class="marca" style="left:{TAXA_BASE:.1%}">média da<br>carteira {pct(TAXA_BASE)}</div>
        <div class="marca" style="left:{LIMIAR:.1%}">limiar<br>{pct(LIMIAR, 0)}</div>
        <div class="marca direita" style="left:100%">100%</div>
      </div>"""


with direita:
    if not enviar:
        st.html("""
          <div class="vazio">
            <strong>O parecer aparece aqui</strong>
            Confira os dados ao lado e clique em <em>Calcular risco</em>. Para ver o modelo em ação
            sem digitar, use um dos exemplos acima.
          </div>""")
    else:
        novo = pd.DataFrame([{
            "idade": idade, "sexo": sexo, "estado_civil": estado_civil, "escolaridade": escolaridade,
            "renda_mensal": renda, "empregado": None if empregado == "Não informado" else empregado,
            "tipo_moradia": tipo_moradia, "mudou_recentemente": mudou, "num_veiculos": num_veiculos,
            "dependentes": dependentes, "cidade": cidade, "valor_emprestimo": valor, "prazo": prazo,
        }])
        prob = float(modelo.predict_proba(novo)[:, 1][0])
        parcela = valor / prazo
        comprometimento = parcela / renda if renda > 0 else None

        if prob >= LIMIAR:
            faixa, titulo = "alto", "Alto risco"
            recomendacao = "Recusar ou encaminhar para análise manual."
        elif prob >= TAXA_BASE:
            faixa, titulo = "moderado", "Risco moderado"
            recomendacao = "Acima da média da carteira. Aprovar com cautela."
        else:
            faixa, titulo = "baixo", "Baixo risco"
            recomendacao = "Abaixo da média da carteira. Aprovar."
        cor, fundo = CORES_RISCO[faixa]

        st.html(f"""
          <section class="parecer" style="--cor:{cor};--fundo:{fundo}" aria-live="polite">
            <p class="faixa">{titulo}</p>
            <p class="prob">{pct(prob)}</p>
            <p class="prob-legenda">de chance de atraso acima de 90 dias</p>
            {regua(prob)}
            <p class="recomendacao"><strong>Recomendação:</strong> {recomendacao}</p>
            <dl class="apoio">
              <div><dt>Parcela estimada, sem juros</dt><dd>{brl(parcela)}</dd></div>
              <div><dt>Renda comprometida</dt>
                   <dd>{"sem renda" if comprometimento is None else pct(comprometimento)}</dd></div>
              <div><dt>Risco em relação à média</dt><dd>{f"{prob / TAXA_BASE:.1f}".replace(".", ",")}×</dd></div>
              <div><dt>Inadimplência média</dt><dd>{pct(TAXA_BASE)}</dd></div>
            </dl>
          </section>""")

        with st.expander("Dados enviados ao modelo"):
            st.dataframe(novo, hide_index=True, width="stretch")
            st.caption("O pipeline aplica sozinho as regras de limpeza, cria `comprometimento` e "
                       "`log_renda`, imputa faltantes e codifica as categorias, exatamente como "
                       "no treino.")
