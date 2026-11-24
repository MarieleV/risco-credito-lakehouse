"""
app.py — Interface Streamlit do modelo de inadimplência (Avaliação N3).

Como rodar (na pasta com app.py, features.py, modelo_inadimplencia.joblib e modelo_meta.json):
    pip install -r requirements.txt
    streamlit run app.py

SEGURANÇA: joblib/pickle pode executar código ao carregar. Este app só carrega o
arquivo gerado pelo nosso próprio notebook (fonte confiável).
"""
import json
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

import features  # necessário: o pipeline salvo referencia features.preparar_entrada  # noqa: F401

PASTA = Path(__file__).parent
ARQ_MODELO = PASTA / "modelo_inadimplencia.joblib"
ARQ_META = PASTA / "modelo_meta.json"

st.set_page_config(page_title="Risco de Inadimplência", page_icon="💳", layout="wide")


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

# ---------------------------------------------------------------------------
# Exemplos prontos (para a demonstração em aula)
# ---------------------------------------------------------------------------
EXEMPLOS = {
    "Cliente de baixo risco": dict(
        idade=42, sexo="F", estado_civil="Casado", escolaridade="Superior", renda_mensal=6500.0,
        empregado="Sim", tipo_moradia="Própria", mudou_recentemente="Não", num_veiculos=1,
        dependentes=1, cidade="Blumenau", valor_emprestimo=8000.0, prazo=36),
    "Cliente de alto risco": dict(
        idade=23, sexo="M", estado_civil="Solteiro", escolaridade="Fundamental", renda_mensal=1400.0,
        empregado="Não", tipo_moradia="Alugada", mudou_recentemente="Sim", num_veiculos=0,
        dependentes=3, cidade="Joinville", valor_emprestimo=15000.0, prazo=12),
}
if "cliente" not in st.session_state:
    st.session_state.cliente = EXEMPLOS["Cliente de baixo risco"]

# ---------------------------------------------------------------------------
# Barra lateral: informações do modelo
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Sobre o modelo")
    st.markdown(f"**Algoritmo:** {meta['modelo']}")
    st.markdown(f"**Protocolo:** {meta['protocolo']} (random_state={meta['random_state']})")
    st.markdown("**Métricas no conjunto de teste**")
    m = meta["metricas_teste"]
    c1, c2, c3 = st.columns(3)
    c1.metric("ROC-AUC", f"{m['ROC-AUC']:.3f}")
    c2.metric("PR-AUC", f"{m['PR-AUC']:.3f}")
    c3.metric("Recall", f"{m['Recall']:.3f}")
    st.caption(f"Limiar de decisão: {LIMIAR:.2f} · treinado em {meta['treinado_em']}")
    st.divider()
    st.markdown("**Versões das bibliotecas**")
    st.code("\n".join(f"{k}=={v}" for k, v in meta["versoes"].items()), language="text")
    st.caption("⚠️ Só carregue arquivos .joblib/.pickle de fontes confiáveis.")

# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
st.title("💳 Avaliação de risco de inadimplência")
st.write("Preencha os dados da **solicitação de crédito**. O modelo estima a probabilidade de o "
         "cliente atrasar mais de 90 dias. É uma ferramenta de **apoio** à decisão do analista.")

cols = st.columns(len(EXEMPLOS) + 1)
for col, (rotulo, dados) in zip(cols, EXEMPLOS.items()):
    if col.button(f"Carregar: {rotulo}", width="stretch"):
        st.session_state.cliente = dados
        st.rerun()

c = st.session_state.cliente
ESTADOS = ["Casado", "Solteiro", "Divorciado", "Viúvo"]
ESCOLAS = ["Fundamental", "Médio", "Superior", "Pós-graduação"]
MORADIAS = ["Própria", "Alugada", "Financiada", "Com os pais"]
CIDADES = meta["cidades"]

# ---------------------------------------------------------------------------
# Formulário
# ---------------------------------------------------------------------------
with st.form("solicitacao"):
    st.subheader("👤 Perfil do cliente")
    a1, a2, a3, a4 = st.columns(4)
    idade = a1.number_input("Idade", 18, 100, int(c["idade"]))
    sexo = a2.selectbox("Sexo", ["F", "M"], index=["F", "M"].index(c["sexo"]))
    estado_civil = a3.selectbox("Estado civil", ESTADOS, index=ESTADOS.index(c["estado_civil"]))
    escolaridade = a4.selectbox("Escolaridade", ESCOLAS, index=ESCOLAS.index(c["escolaridade"]))

    b1, b2, b3, b4 = st.columns(4)
    cidade = b1.selectbox("Cidade (SC)", CIDADES, index=CIDADES.index(c["cidade"]))
    tipo_moradia = b2.selectbox("Moradia", MORADIAS, index=MORADIAS.index(c["tipo_moradia"]))
    mudou = b3.radio("Mudou de endereço no último ano?", ["Não", "Sim"],
                     index=["Não", "Sim"].index(c["mudou_recentemente"]), horizontal=True)
    dependentes = b4.number_input("Dependentes", 0, 10, int(c["dependentes"]))

    st.subheader("💰 Situação financeira e empréstimo")
    d1, d2, d3, d4, d5 = st.columns(5)
    opcoes_emp = ["Sim", "Não", "Não informado"]
    empregado = d1.selectbox("Empregado?", opcoes_emp, index=opcoes_emp.index(c["empregado"]))
    renda = d2.number_input("Renda mensal (R$)", 0.0, 500000.0, float(c["renda_mensal"]), step=100.0)
    num_veiculos = d3.number_input("Nº de veículos", 0, 10, int(c["num_veiculos"]))
    valor = d4.number_input("Valor do empréstimo (R$)", 100.0, 500000.0,
                            float(c["valor_emprestimo"]), step=500.0)
    prazo = d5.selectbox("Prazo (meses)", [12, 24, 36, 48, 60],
                         index=[12, 24, 36, 48, 60].index(int(c["prazo"])))

    enviar = st.form_submit_button("Calcular risco", type="primary", width="stretch")

# ---------------------------------------------------------------------------
# Predição
# ---------------------------------------------------------------------------
if enviar:
    novo = pd.DataFrame([{
        "idade": idade, "sexo": sexo, "estado_civil": estado_civil, "escolaridade": escolaridade,
        "renda_mensal": renda, "empregado": None if empregado == "Não informado" else empregado,
        "tipo_moradia": tipo_moradia, "mudou_recentemente": mudou, "num_veiculos": num_veiculos,
        "dependentes": dependentes, "cidade": cidade, "valor_emprestimo": valor, "prazo": prazo,
    }])
    prob = float(modelo.predict_proba(novo)[:, 1][0])
    taxa_base = meta["taxa_inadimplencia_treino"]
    parcela = valor / prazo
    comprometimento = parcela / renda if renda > 0 else float("nan")

    st.divider()
    r1, r2, r3 = st.columns([1.2, 1, 1])
    with r1:
        if prob >= LIMIAR:
            st.error(f"### 🔴 ALTO RISCO\nProbabilidade de inadimplência: **{prob:.1%}**")
            st.write("Recomendação: **recusar ou encaminhar para análise manual**.")
        elif prob >= taxa_base:
            st.warning(f"### 🟡 RISCO MODERADO\nProbabilidade de inadimplência: **{prob:.1%}**")
            st.write("Acima da média da carteira. Recomendação: **aprovar com cautela**.")
        else:
            st.success(f"### 🟢 BAIXO RISCO\nProbabilidade de inadimplência: **{prob:.1%}**")
            st.write("Recomendação: **aprovar**.")
        st.progress(min(prob, 1.0))
    r2.metric("Parcela estimada (sem juros)", f"R$ {parcela:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    r2.metric("Comprometimento da renda", "—" if comprometimento != comprometimento else f"{comprometimento:.1%}")
    r3.metric("Taxa média da carteira", f"{taxa_base:.1%}")
    r3.metric("Risco vs. média", f"{prob / taxa_base:.1f}×")

    with st.expander("Dados enviados ao modelo"):
        st.dataframe(novo, hide_index=True, width="stretch")
        st.caption("O pipeline aplica sozinho as regras de limpeza, cria `comprometimento` e "
                   "`log_renda`, imputa faltantes e codifica as categorias, exatamente como no treino.")
