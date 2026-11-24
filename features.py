"""
features.py — regras de limpeza e engenharia de atributos do projeto N3.

Este módulo é importado tanto pelo notebook (treino) quanto pelo app Streamlit (deploy).
Isso é necessário porque o pipeline salvo com joblib guarda apenas uma *referência*
às funções usadas no FunctionTransformer: quem carrega o modelo precisa conseguir
importar `features.preparar_entrada`.

Todas as funções aqui são regras FIXAS, aplicadas linha a linha. Nenhuma delas
aprende estatísticas com os dados (média, mediana, percentil...), portanto
não causam vazamento de dados.
"""
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Colunas usadas pelo modelo (o que existe no momento da concessão do crédito)
# ---------------------------------------------------------------------------
COLUNAS_ENTRADA = [
    "idade", "sexo", "estado_civil", "escolaridade", "renda_mensal", "empregado",
    "tipo_moradia", "mudou_recentemente", "num_veiculos", "dependentes", "cidade",
    "valor_emprestimo", "prazo",
]

NUMERICAS = ["idade", "renda_mensal", "num_veiculos", "dependentes",
             "valor_emprestimo", "prazo", "comprometimento", "log_renda"]
ORDINAIS = ["escolaridade"]
NOMINAIS = ["sexo", "estado_civil", "empregado", "tipo_moradia",
            "mudou_recentemente", "cidade"]
ORDEM_ESCOLARIDADE = [["Fundamental", "Médio", "Superior", "Pós-graduação"]]

# Colunas que NUNCA entram no modelo
#  - id_cliente: identificador, não tem poder preditivo (e é dado pessoal)
#  - data_contrato: usada só para auditoria/validação temporal
#  - qtd_cobrancas: VAZAMENTO DO ALVO (só existe depois do atraso)
COLUNAS_PROIBIDAS = ["id_cliente", "data_contrato", "qtd_cobrancas", "inadimplente"]


def regras_limpeza(d: pd.DataFrame) -> pd.DataFrame:
    """Correções determinísticas (as mesmas da atividade de pré-processamento da N2)."""
    d = d.copy()
    # idade fora do domínio plausível -> ausente (será imputada no pipeline)
    if "idade" in d:
        d["idade"] = pd.to_numeric(d["idade"], errors="coerce")
        d.loc[~d["idade"].between(18, 100), "idade"] = np.nan
    # renda negativa -> ausente
    if "renda_mensal" in d:
        d["renda_mensal"] = pd.to_numeric(d["renda_mensal"], errors="coerce")
        d.loc[d["renda_mensal"] < 0, "renda_mensal"] = np.nan
    # prazo informado em anos -> meses
    if "prazo" in d:
        d["prazo"] = pd.to_numeric(d["prazo"], errors="coerce")
        d["prazo"] = np.where(d["prazo"] < 12, d["prazo"] * 12, d["prazo"])
    # grafias inconsistentes de estado civil
    if "estado_civil" in d:
        d["estado_civil"] = (d["estado_civil"].astype("string").str.strip()
                             .str.capitalize().replace({"Viuvo": "Viúvo"}))
    return d


def criar_atributos(d: pd.DataFrame) -> pd.DataFrame:
    """Engenharia de atributos linha a linha."""
    d = d.copy()
    # fração da renda comprometida com a parcela (sem juros)
    d["comprometimento"] = (d["valor_emprestimo"] / d["prazo"]) / d["renda_mensal"]
    d["comprometimento"] = d["comprometimento"].replace([np.inf, -np.inf], np.nan)
    # log da renda: reduz a assimetria (outliers de 150 e 230 mil)
    d["log_renda"] = np.log1p(d["renda_mensal"])
    return d


def preparar_entrada(d: pd.DataFrame) -> pd.DataFrame:
    """Primeiro passo do pipeline salvo: limpeza + atributos novos.

    Fica DENTRO do pipeline para que um dado novo (ex.: digitado no Streamlit)
    passe exatamente pelas mesmas regras usadas no treino.
    """
    d = regras_limpeza(d)
    d = criar_atributos(d)
    # garante NaN "puro" do numpy nas categóricas (o SimpleImputer não aceita pd.NA)
    for c in NOMINAIS + ORDINAIS:
        if c in d:
            d[c] = d[c].astype(object).where(d[c].notna(), np.nan)
    return d
