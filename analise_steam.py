"""
Análise do Mercado Gamer na Steam
Autor: Leonardo Carrer Lemos
Dataset: Steam Games Dataset — Kaggle (fronkongames)
Ferramentas: Python, Pandas, Matplotlib, Seaborn
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from matplotlib.patches import Patch
import os

# ── Configurações visuais ──────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams.update({
    "figure.facecolor": "#F8F9FA",
    "axes.facecolor":   "#F8F9FA",
    "font.family":      "DejaVu Sans",
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.labelsize":   11,
})
os.makedirs("graficos", exist_ok=True)
plt.rcParams["text.usetex"] = False
plt.rcParams["mathtext.default"] = "regular"

# ── 1. Carregando os dados ─────────────────────────────────────────────────────
print("Carregando dataset...")
df_raw = pd.read_csv("games.csv", index_col=False, low_memory=False)

# Posições confirmadas pelo diagnóstico do CS2:
# 01 = Name
# 06 = Price
# 10 = Supported languages (lista de idiomas reais)
# 23 = Negative
# 24 = Positive (estava como "Score rank" no header mas contém avaliações positivas)
# 36 = Tags (contém gêneros reais: Action, RPG, etc.)
# 04 = Peak CCU

df = pd.DataFrame({
    "Name":      df_raw.iloc[:, 1],
    "Price":     df_raw.iloc[:, 6],
    "Idiomas":   df_raw.iloc[:, 10],
    "Negative":  df_raw.iloc[:, 23],
    "Positive":  df_raw.iloc[:, 24],
    "Genres":    df_raw.iloc[:, 36],
    "Peak_CCU":  df_raw.iloc[:, 4],
})

print(f"✅ Dataset carregado: {len(df):,} jogos")

# Verificação com CS2
cs2 = df[df["Name"] == "Counter-Strike 2"]
if len(cs2) > 0:
    row = cs2.iloc[0]
    print(f"Verificação CS2:")
    print(f"  Positive:  {row['Positive']:,}")
    print(f"  Negative:  {row['Negative']:,}")
    print(f"  Idiomas:   {str(row['Idiomas'])[:80]}...")
    print(f"  Genres:    {row['Genres']}\n")

# ── 2. Limpeza dos dados ───────────────────────────────────────────────────────
print("=" * 55)
print("  LIMPEZA DOS DADOS")
print("=" * 55)

df = df.dropna(subset=["Name"])
df["Price"]    = pd.to_numeric(df["Price"],    errors="coerce").fillna(0)
df["Positive"] = pd.to_numeric(df["Positive"], errors="coerce").fillna(0)
df["Negative"] = pd.to_numeric(df["Negative"], errors="coerce").fillna(0)

# Corrige inversão: usa o maior valor como "positivas"
df["Pos_real"] = df[["Positive", "Negative"]].max(axis=1)
df["Neg_real"] = df[["Positive", "Negative"]].min(axis=1)
df["Total_Reviews"] = df["Pos_real"] + df["Neg_real"]
df_aval = df[df["Total_Reviews"] > 100].copy()
df_aval["Aprovacao"] = (df_aval["Pos_real"] / df_aval["Total_Reviews"] * 100).round(1)
df["Tipo"] = df["Price"].apply(lambda x: "Gratuito" if x == 0 else "Pago")

print(f"\n✅ Jogos com mais de 100 avaliações: {len(df_aval):,}")
print(f"✅ Jogos gratuitos: {(df['Tipo'] == 'Gratuito').sum():,}")
print(f"✅ Jogos pagos:     {(df['Tipo'] == 'Pago').sum():,}")

# ── 3. Mercado Brasileiro ──────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  MERCADO BRASILEIRO")
print("=" * 55)

df_ptbr = df[df["Idiomas"].str.contains("Portuguese", case=False, na=False)]
print(f"\n✅ Jogos com suporte a Português: {len(df_ptbr):,}")
print(f"   ({len(df_ptbr)/len(df)*100:.1f}% do total)")

df_ptbr_aval = df_ptbr[df_ptbr["Total_Reviews"] > 100].copy()
df_ptbr_aval["Pos_real"] = df_ptbr_aval[["Positive", "Negative"]].max(axis=1)
df_ptbr_aval["Aprovacao"] = (
    df_ptbr_aval["Pos_real"] / df_ptbr_aval["Total_Reviews"] * 100
).round(1)

top_ptbr = df_ptbr_aval.nlargest(10, "Total_Reviews")[
    ["Name", "Price", "Aprovacao", "Total_Reviews"]
]
print(f"\nTop 10 jogos com PT-BR por avaliações:")
print(top_ptbr.to_string(index=False))

# ── 4. Gêneros ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  ANÁLISE DE GÊNEROS")
print("=" * 55)

generos = df["Genres"].dropna().str.split(",").explode().str.strip()
generos_validos = ["Indie", "Casual", "Action", "Adventure", "Simulation",
                   "Strategy", "RPG", "Free To Play", "Early Access",
                   "Sports", "Racing", "Massively Multiplayer", "Puzzle",
                   "Horror", "Platformer", "Shooter", "Fighting"]
top_generos = generos[generos.isin(generos_validos)].value_counts().head(12)
print(f"\nTop gêneros:")
print(top_generos.to_string())

# ── 5. Gráficos ────────────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  GERANDO GRÁFICOS")
print("=" * 55)

COR_PRINCIPAL = "#2563EB"
COR_VERDE     = "#10B981"
COR_LARANJA   = "#F59E0B"

# Gráfico 1 — Gêneros mais comuns
if len(top_generos) > 0:
    fig, ax = plt.subplots(figsize=(11, 6))
    cores = [COR_PRINCIPAL if i < 3 else "#94A3B8" for i in range(len(top_generos))]
    ax.barh(top_generos.index[::-1], top_generos.values[::-1],
            color=cores[::-1], edgecolor="white")
    for i, val in enumerate(top_generos.values[::-1]):
        ax.text(val + 100, i, f"{val:,}", va="center", fontsize=9, color="#374151")
    ax.set_title("Gêneros Mais Comuns na Steam")
    ax.set_xlabel("Número de Jogos")
    ax.set_xlim(0, top_generos.max() * 1.18)
    plt.tight_layout()
    plt.savefig("graficos/01_generos_mais_comuns.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Gráfico 1 salvo")

# Gráfico 2 — Distribuição de preços (apenas jogos com preço >= US$ 0.99)
fig, ax = plt.subplots(figsize=(10, 5))
df_pagos = df[(df["Price"] >= 0.99) & (df["Price"] <= 60)]
ax.hist(df_pagos["Price"], bins=40, color=COR_PRINCIPAL, edgecolor="white", linewidth=0.5)
ax.set_title("Distribuicao de Precos dos Jogos Pagos na Steam (de USD 0.99 a USD 60)")
ax.set_xlabel("Preço (US$)")
ax.set_ylabel("Número de Jogos")
ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"US$ {x:.0f}"))
for preco in [4.99, 9.99, 19.99, 29.99]:
    ax.axvline(preco, color="#E24B4A", linewidth=0.8, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.savefig("graficos/02_distribuicao_precos.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Gráfico 2 salvo")

# Gráfico 3 — Gratuito vs Pago
fig, ax = plt.subplots(figsize=(6, 6))
tipo_counts = df["Tipo"].value_counts()
ax.pie(tipo_counts, labels=tipo_counts.index, autopct="%1.1f%%",
       colors=[COR_VERDE, COR_LARANJA], startangle=90,
       wedgeprops=dict(edgecolor="white", linewidth=2))
ax.set_title("Proporção de Jogos Gratuitos vs Pagos na Steam")
plt.tight_layout()
plt.savefig("graficos/03_gratuito_vs_pago.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Gráfico 3 salvo")

# Gráfico 4 — Taxa de aprovação gratuito vs pago
df_aval_tipo = df_aval.copy()
df_aval_tipo["Tipo"] = df_aval_tipo["Price"].apply(
    lambda x: "Gratuito" if x == 0 else "Pago")
fig, ax = plt.subplots(figsize=(8, 5))
sns.boxplot(data=df_aval_tipo, x="Tipo", y="Aprovacao",
            hue="Tipo", palette={"Gratuito": COR_VERDE, "Pago": COR_LARANJA},
            width=0.4, linewidth=1.2, legend=False, ax=ax)
ax.set_title("Taxa de Aprovação: Jogos Gratuitos vs Pagos")
ax.set_xlabel("Tipo de Jogo")
ax.set_ylabel("Taxa de Aprovação (%)")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.0f}%"))
plt.tight_layout()
plt.savefig("graficos/04_aprovacao_gratuito_pago.png", dpi=150, bbox_inches="tight")
plt.close()
print("✅ Gráfico 4 salvo")

# Gráfico 5 — Top 10 jogos PT-BR
if len(df_ptbr_aval) > 0:
    fig, ax = plt.subplots(figsize=(12, 7))
    top10 = df_ptbr_aval.nlargest(10, "Total_Reviews").reset_index(drop=True)

    nomes      = [str(n)[:40] + "..." if len(str(n)) > 40 else str(n)
                  for n in top10["Name"].tolist()]
    avaliacoes = [int(v) for v in top10["Total_Reviews"].tolist()]
    aprovacoes = [float(v) for v in top10["Aprovacao"].tolist()]
    posicoes   = list(range(len(nomes)))

    cores_ptbr = ["#1D9E75" if ap >= 80 else "#F59E0B" if ap >= 60 else "#E24B4A"
                  for ap in aprovacoes]

    bars = ax.barh(posicoes, avaliacoes, color=cores_ptbr, edgecolor="white", height=0.6)
    ax.set_yticks(posicoes)
    ax.set_yticklabels(nomes, fontsize=10)

    for bar, ap in zip(bars, aprovacoes):
        ax.text(bar.get_width() * 1.01,
                bar.get_y() + bar.get_height() / 2,
                f"{ap:.0f}% aprovação", va="center", fontsize=9, color="#374151")

    ax.set_title("Top 10 Jogos com Suporte a Português — Por Número de Avaliações")
    ax.set_xlabel("Total de Avaliações")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}K"))
    ax.set_xlim(0, max(avaliacoes) * 1.30)
    legenda = [Patch(color="#1D9E75", label="≥ 80% aprovação"),
               Patch(color="#F59E0B", label="60–79%"),
               Patch(color="#E24B4A", label="< 60%")]
    ax.legend(handles=legenda, loc="upper center",
              bbox_to_anchor=(0.5, -0.12), ncol=3, framealpha=0.9)
    plt.tight_layout(pad=2.0)
    plt.savefig("graficos/05_top_jogos_ptbr.png", dpi=150, bbox_inches="tight")
    plt.close()
    print("✅ Gráfico 5 salvo")

# ── 6. Insights finais ─────────────────────────────────────────────────────────
print("\n" + "=" * 55)
print("  INSIGHTS PRINCIPAIS")
print("=" * 55)

media_pago     = df[df["Tipo"] == "Pago"]["Price"].median()
aprov_gratuito = df_aval_tipo[df_aval_tipo["Tipo"] == "Gratuito"]["Aprovacao"].mean()
aprov_pago     = df_aval_tipo[df_aval_tipo["Tipo"] == "Pago"]["Aprovacao"].mean()
top1 = df_ptbr_aval.nlargest(1, "Total_Reviews")["Name"].values[0] \
       if len(df_ptbr_aval) > 0 else "N/A"

print(f"\n💡 Total de jogos analisados:         {len(df):,}")
print(f"💡 Preço mediano dos jogos pagos:     US$ {media_pago:.2f}")
print(f"💡 Jogos com suporte a Português:     {len(df_ptbr):,} ({len(df_ptbr)/len(df)*100:.1f}%)")
print(f"💡 Aprovação média — Gratuitos:       {aprov_gratuito:.1f}%")
print(f"💡 Aprovação média — Pagos:           {aprov_pago:.1f}%")
print(f"💡 Jogo PT-BR mais avaliado:          {top1}")
print(f"\n✅ Análise completa! Verifique a pasta 'graficos/' para os visuais.")
