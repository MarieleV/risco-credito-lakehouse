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
# Estilo
# ---------------------------------------------------------------------------
# Cada faixa de risco: (texto, fundo suave, cor do trilho da régua)
CORES_RISCO = {
    "baixo": ("#23704F", "#E3F0E9", "#4E9C77"),
    "moderado": ("#94650B", "#F6EDD9", "#D7A637"),
    "alto": ("#A83434", "#F6E3E1", "#C9504F"),
}

st.html("""
<style>
  :root {
    --tinta: #12302F; --grafite: #4D5B5A; --linha: #D5DDD9; --papel: #F3F5F2;
    --branco: #FFFFFF; --suave: #C5D8D3;
    --titulo: "Familjen Grotesk", "Public Sans", sans-serif;
    --raio: 14px;
  }
  .block-container { padding-top: 0; padding-bottom: 3rem; max-width: 1200px; }

  /* Barra do Streamlit transparente sobre a faixa escura */
  [data-testid="stHeader"] { background: transparent; color: var(--branco); }
  [data-testid="stHeader"] button { color: var(--branco); }

  /* ---- Cabeçalho: faixa verde-petróleo de ponta a ponta ---- */
  .st-key-cabecalho { background: var(--tinta); box-shadow: 0 0 0 100vmax var(--tinta);
                      clip-path: inset(0 -100vmax); padding: 4.25rem 0 2.5rem; margin-bottom: 2.25rem; }
  .st-key-cabecalho h1 { color: var(--branco); letter-spacing: -0.02em; line-height: 1.05;
                         padding: 0; }
  .st-key-cabecalho .abertura { color: var(--suave); font-size: 1.05rem; line-height: 1.55;
                                max-width: 60ch; margin: .6rem 0 0; }
  .st-key-cabecalho .rotulo-exemplo { color: var(--suave); font-size: .9rem; margin: 0 0 .1rem; }
  .st-key-cabecalho button { background: transparent; border: 1px solid rgba(255,255,255,.4);
                             color: var(--branco); }
  .st-key-cabecalho button p { color: var(--branco); }
  .st-key-cabecalho button:hover { background: rgba(255,255,255,.1); border-color: var(--branco);
                                   color: var(--branco); }
  .st-key-cabecalho button:focus-visible { outline: 2px solid var(--branco); outline-offset: 2px; }

  /* ---- Painéis: formulário e parecer lado a lado, mesma altura ---- */
  [data-testid="stForm"] { background: var(--branco); border: 1px solid var(--linha);
                           border-radius: var(--raio); padding: 1.75rem 1.75rem 1.5rem; }
  [data-testid="stForm"] h3 { font-size: 1.05rem; font-weight: 600; color: var(--tinta);
                              padding: 0; margin: 1.1rem 0 .1rem; }
  [data-testid="stForm"] [data-testid="stElementContainer"]:first-child h3 { margin-top: 0; }
  [data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] { display: none; }
  [data-testid="stFormSubmitButton"] { margin-top: .9rem; }

  [data-testid="stLayoutWrapper"]:has(> .st-key-lado_parecer) { flex: 1; }
  .st-key-lado_parecer, .st-key-lado_parecer > [data-testid="stElementContainer"],
  .st-key-lado_parecer [data-testid="stHtml"] { height: 100%; }
  .st-key-lado_parecer > [data-testid="stElementContainer"] { flex: 1; }

  /* Parecer */
  .parecer { box-sizing: border-box; height: 100%; color: var(--tinta);
             background: linear-gradient(var(--cor), var(--cor)) top / 100% 6px no-repeat, var(--branco);
             border: 1px solid var(--linha); border-radius: var(--raio);
             padding: 1.9rem 1.75rem 1.5rem; display: flex; flex-direction: column; }
  .parecer .faixa { align-self: flex-start; margin: 0; padding: .3rem .75rem; border-radius: 99px;
                    background: var(--fundo); color: var(--cor); font-weight: 600; font-size: .9rem; }
  .parecer .prob { font-family: var(--titulo); font-weight: 700; color: var(--cor);
                   font-size: clamp(3.4rem, 6vw, 4.8rem); line-height: 1; margin: 1rem 0 .3rem;
                   font-variant-numeric: tabular-nums; letter-spacing: -0.03em; }
  .parecer .prob-legenda { color: var(--grafite); margin: 0 0 1.5rem; }
  .parecer .recomendacao { line-height: 1.5; margin: 1.25rem 0 0; padding: .9rem 1rem;
                           background: var(--papel); border-radius: 8px; }

  /* Régua de risco: 0% a 100%, com zonas, média da carteira e limiar */
  .regua { position: relative; height: 5rem; margin: 0 .2rem; }
  .regua .trilho { position: absolute; top: 1.6rem; left: 0; right: 0; height: .7rem;
                   border-radius: 99px; overflow: hidden; display: flex; gap: 2px; }
  .regua .ponteiro { position: absolute; top: 0; width: 0;
                     animation: desliza .9s cubic-bezier(.2,.8,.2,1); }
  .regua .ponteiro::before { content: ""; position: absolute; left: -1.5px; top: .45rem; width: 3px;
                             height: 2.05rem; background: var(--tinta); border-radius: 2px; }
  .regua .ponteiro::after { content: ""; position: absolute; left: -.45rem; top: 0;
                            border: .45rem solid transparent; border-top-color: var(--tinta); }
  .regua .marca { position: absolute; top: 2.75rem; font-size: .8rem; color: var(--grafite);
                  white-space: nowrap; line-height: 1.3; font-variant-numeric: tabular-nums;
                  transform: translateX(-50%); text-align: center; }
  .regua .marca.inicio { transform: none; text-align: left; }
  .regua .marca.fim { transform: translateX(-100%); text-align: right; }
  @keyframes desliza { from { left: 0; } }
  @media (prefers-reduced-motion: reduce) { .regua .ponteiro { animation: none; } }

  /* Números de apoio */
  .apoio { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem 1.5rem; margin: 1.5rem 0 0; }
  .apoio dt { color: var(--grafite); font-size: .85rem; margin: 0; }
  .apoio dd { margin: .15rem 0 0; font-family: var(--titulo); font-weight: 600; font-size: 1.4rem;
              font-variant-numeric: tabular-nums; }

  /* Dados enviados (recolhível, dentro do parecer) */
  .enviados { margin-top: auto; padding-top: 1.25rem; }
  .enviados summary { cursor: pointer; color: var(--grafite); font-size: .9rem;
                      border-top: 1px solid var(--linha); padding-top: 1rem; }
  .enviados summary:focus-visible { outline: 2px solid var(--tinta); outline-offset: 3px; }
  .lista { display: grid; grid-template-columns: 1fr 1fr; gap: .35rem 1.5rem; margin: .9rem 0 .75rem;
           font-size: .9rem; }
  .lista div { display: flex; justify-content: space-between; gap: .75rem;
               border-bottom: 1px solid var(--papel); padding-bottom: .3rem; }
  .lista dt { color: var(--grafite); }
  .lista dd { margin: 0; font-weight: 600; text-align: right; font-variant-numeric: tabular-nums;
              white-space: nowrap; }

  /* Estado vazio */
  .vazio { box-sizing: border-box; height: 100%; min-height: 20rem; display: flex;
           flex-direction: column; justify-content: center; padding: 2rem 2.25rem;
           border: 1.5px dashed var(--linha); border-radius: var(--raio);
           color: var(--grafite); line-height: 1.6; }
  .vazio strong { color: var(--tinta); font-family: var(--titulo); font-size: 1.3rem;
                  margin-bottom: .4rem; }
  .vazio p { margin: 0; max-width: 36ch; }

  /* ---- Rodapé: sobre o modelo ---- */
  .rodape { margin-top: 3rem; padding-top: 2rem; border-top: 1px solid var(--linha);
            display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 1.5rem 3rem;
            align-items: start; }
  .rodape h2 { font-family: var(--titulo); font-size: 1.25rem; font-weight: 600;
               margin: 0 0 .5rem; padding: 0; color: var(--tinta); }
  .nota { color: var(--grafite); font-size: .875rem; line-height: 1.6; max-width: 62ch; margin: 0 0 .5rem; }
  .metricas { display: flex; flex-wrap: wrap; gap: 1.25rem 2.25rem; margin: 0; }
  .metricas dt { color: var(--grafite); font-size: .85rem; }
  .metricas dd { margin: .15rem 0 0; font-family: var(--titulo); font-weight: 600; font-size: 1.5rem;
                 font-variant-numeric: tabular-nums; color: var(--tinta); }

  /* zera o recuo que o Streamlit aplica a listas */
  .apoio, .lista, .metricas, .apoio dt, .apoio dd, .lista dt, .lista dd, .metricas dt, .metricas dd {
    padding-inline: 0 !important; margin-inline: 0 !important; }

  @media (max-width: 900px) {
    .rodape { grid-template-columns: 1fr; }
  }
  @media (max-width: 640px) {
    .block-container { padding-left: 1rem; padding-right: 1rem; }
    .st-key-cabecalho { padding-top: 3.75rem; }
    [data-testid="stForm"], .parecer { padding-left: 1.1rem; padding-right: 1.1rem; }
    .lista { grid-template-columns: 1fr; }
    .apoio dd { font-size: 1.2rem; }
  }
</style>
""")


def brl(valor: float) -> str:
    """Formata em reais no padrão brasileiro: R$ 1.234,56."""
    return "R$ " + f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def dec(valor: float, casas: int = 3) -> str:
    """Formata decimal com vírgula: 0,697."""
    return f"{valor:.{casas}f}".replace(".", ",")


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
# Cabeçalho
# ---------------------------------------------------------------------------
with st.container(key="cabecalho"):
    h1, h2 = st.columns([2.1, 1], gap="large", vertical_alignment="bottom")
    with h1:
        st.title("Avaliação de risco de inadimplência")
        st.html('<p class="abertura">Preencha a solicitação de crédito e o modelo estima a chance '
                'de o cliente atrasar mais de 90 dias. O resultado apoia a decisão do analista, '
                'não a substitui.</p>')
    with h2:
        st.html('<p class="rotulo-exemplo">Preencher com um exemplo</p>')
        e1, e2 = st.columns(2)
        for col, (rotulo, dados) in zip((e1, e2), EXEMPLOS.items()):
            if col.button(rotulo, width="stretch", key=f"exemplo_{rotulo}"):
                st.session_state.cliente = dados
                st.rerun()

c = st.session_state.cliente
ESTADOS = ["Casado", "Solteiro", "Divorciado", "Viúvo"]
ESCOLAS = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
MORADIAS = ["Própria", "Alugada", "Financiada", "Com os pais"]
CIDADES = meta["cidades"]
PRAZOS = [12, 24, 36, 48, 60]
OPCOES_EMP = ["Sim", "Não", "Não informado"]

esquerda, direita = st.columns([1.3, 1], gap="large")

# ---------------------------------------------------------------------------
# Formulário
# ---------------------------------------------------------------------------
with esquerda:
    with st.form("solicitacao", border=False):
        # Grade única de 3 colunas; [1, 2] e [2, 1] ocupam 1 e 2 colunas dela.
        st.subheader("Perfil")
        a1, a2, a3 = st.columns(3)
        idade = a1.number_input("Idade", 18, 100, int(c["idade"]))
        sexo = a2.selectbox("Sexo", ["F", "M"], index=["F", "M"].index(c["sexo"]))
        estado_civil = a3.selectbox("Estado civil", ESTADOS, index=ESTADOS.index(c["estado_civil"]))
        a4, a5, a6 = st.columns(3)
        escolaridade = a4.selectbox("Escolaridade", ESCOLAS, index=ESCOLAS.index(c["escolaridade"]))
        dependentes = a5.number_input("Dependentes", 0, 10, int(c["dependentes"]))
        cidade = a6.selectbox("Cidade (SC)", CIDADES, index=CIDADES.index(c["cidade"]))

        st.subheader("Moradia e renda")
        b1, b2, b3 = st.columns(3)
        tipo_moradia = b1.selectbox("Moradia", MORADIAS, index=MORADIAS.index(c["tipo_moradia"]))
        num_veiculos = b2.number_input("Veículos", 0, 10, int(c["num_veiculos"]))
        empregado = b3.selectbox("Está empregado?", OPCOES_EMP,
                                 index=OPCOES_EMP.index(c["empregado"]))
        b4, b5 = st.columns([1, 2])
        renda = b4.number_input("Renda mensal (R$)", 0.0, 500000.0, float(c["renda_mensal"]),
                                step=100.0, format="%.0f")
        mudou = b5.radio("Mudou de endereço no último ano?", ["Não", "Sim"],
                         index=["Não", "Sim"].index(c["mudou_recentemente"]), horizontal=True)

        st.subheader("Pedido de crédito")
        d1, d2 = st.columns([2, 1])
        valor = d1.number_input("Valor pedido (R$)", 100.0, 500000.0,
                                float(c["valor_emprestimo"]), step=500.0, format="%.0f")
        prazo = d2.selectbox("Prazo (meses)", PRAZOS, index=PRAZOS.index(int(c["prazo"])))

        enviar = st.form_submit_button("Calcular risco", type="primary", width="stretch")


# ---------------------------------------------------------------------------
# Parecer
# ---------------------------------------------------------------------------
def regua(prob: float) -> str:
    """Régua horizontal de 0% a 100% com as zonas de risco, a média da carteira e o limiar."""
    zonas = [(TAXA_BASE, "baixo"), (LIMIAR - TAXA_BASE, "moderado"), (1 - LIMIAR, "alto")]
    trilho = "".join(f'<span style="flex:{w:.4f};background:{CORES_RISCO[k][2]}"></span>'
                     for w, k in zonas)
    return f"""
      <div class="regua" role="img"
           aria-label="Probabilidade de {pct(prob)}; média da carteira {pct(TAXA_BASE)}; limiar {pct(LIMIAR, 0)}">
        <div class="trilho">{trilho}</div>
        <div class="ponteiro" style="left:{min(prob, 1):.2%}"></div>
        <div class="marca inicio" style="left:0">0%</div>
        <div class="marca" style="left:{TAXA_BASE:.1%}">média<br>{pct(TAXA_BASE)}</div>
        <div class="marca" style="left:{LIMIAR:.1%}">limiar<br>{pct(LIMIAR, 0)}</div>
        <div class="marca fim" style="left:100%">100%</div>
      </div>"""


def dados_enviados(d: dict) -> str:
    """Lista legível do que foi enviado ao modelo (no lugar da tabela técnica)."""
    itens = [
        ("Idade", f"{d['idade']} anos"), ("Sexo", d["sexo"]), ("Estado civil", d["estado_civil"]),
        ("Escolaridade", d["escolaridade"]), ("Dependentes", d["dependentes"]),
        ("Cidade", d["cidade"]), ("Moradia", d["tipo_moradia"]),
        ("Mudou de endereço", d["mudou_recentemente"]), ("Veículos", d["num_veiculos"]),
        ("Empregado", d["empregado"] or "Não informado"), ("Renda mensal", brl(d["renda_mensal"])),
        ("Valor pedido", brl(d["valor_emprestimo"])), ("Prazo", f"{d['prazo']} meses"),
    ]
    linhas = "".join(f"<div><dt>{escape(k)}</dt><dd>{escape(str(v))}</dd></div>" for k, v in itens)
    return f"""
      <details class="enviados">
        <summary>Dados enviados ao modelo</summary>
        <dl class="lista">{linhas}</dl>
        <p class="nota">O pipeline aplica sozinho as regras de limpeza, calcula o comprometimento
        da renda, imputa faltantes e codifica as categorias, exatamente como no treino.</p>
      </details>"""


with direita, st.container(key="lado_parecer"):
    if not enviar:
        st.html("""
          <div class="vazio">
            <strong>O parecer aparece aqui</strong>
            <p>Confira os dados da solicitação e clique em <em>Calcular risco</em>. Para ver o
            modelo em ação sem digitar, use um dos exemplos no topo da página.</p>
          </div>""")
    else:
        entrada = {
            "idade": idade, "sexo": sexo, "estado_civil": estado_civil, "escolaridade": escolaridade,
            "renda_mensal": renda, "empregado": None if empregado == "Não informado" else empregado,
            "tipo_moradia": tipo_moradia, "mudou_recentemente": mudou, "num_veiculos": num_veiculos,
            "dependentes": dependentes, "cidade": cidade, "valor_emprestimo": valor, "prazo": prazo,
        }
        prob = float(modelo.predict_proba(pd.DataFrame([entrada]))[:, 1][0])
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
        cor, fundo, _ = CORES_RISCO[faixa]

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
              <div><dt>Risco em relação à média</dt><dd>{dec(prob / TAXA_BASE, 1)}×</dd></div>
              <div><dt>Inadimplência média</dt><dd>{pct(TAXA_BASE)}</dd></div>
            </dl>
            {dados_enviados(entrada)}
          </section>""")

# ---------------------------------------------------------------------------
# Sobre o modelo (aparece ao rolar a página)
# ---------------------------------------------------------------------------
m = meta["metricas_teste"]
versoes = ", ".join(f"{k} {v}" for k, v in meta["versoes"].items())
st.html(f"""
  <section class="rodape">
    <div>
      <h2>Sobre o modelo</h2>
      <p class="nota">{escape(meta['modelo'])} treinada em {escape(meta['treinado_em'])}. Métricas
      medidas no conjunto de teste ({escape(meta['protocolo'])}, random_state={meta['random_state']}).</p>
      <p class="nota">Versões: {escape(versoes)}. Só carregue arquivos .joblib ou .pickle de fontes
      confiáveis: ao abrir, eles podem executar código.</p>
    </div>
    <dl class="metricas">
      <div><dt>ROC-AUC</dt><dd>{dec(m['ROC-AUC'])}</dd></div>
      <div><dt>PR-AUC</dt><dd>{dec(m['PR-AUC'])}</dd></div>
      <div><dt>Recall</dt><dd>{dec(m['Recall'])}</dd></div>
      <div><dt>Limiar</dt><dd>{pct(LIMIAR, 0)}</dd></div>
      <div><dt>Inadimplência média</dt><dd>{pct(TAXA_BASE)}</dd></div>
    </dl>
  </section>""")
