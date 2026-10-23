# -*- coding: utf-8 -*-
"""
Décrire un corpus IRaMuTeQ avant de l'analyser, puis lui ajouter
une variable étoilée *taille_ (courte / moyenne / longue).

Fonctionne avec tout corpus produit par wiki2iramuteq :
le fichier .txt et son fichier _metadonnees.csv, dans le même dossier.

Usage :
    python3 decrire_corpus.py                       (corpus des humanités numériques)
    python3 decrire_corpus.py chemin/vers/corpus.txt

Sorties, dans le dossier resultats/ :
  - <corpus>_longueurs.png : graphique des longueurs
  - <corpus>_taille.txt    : corpus enrichi de la variable *taille_
"""

# %% 1. Charger les métadonnées
import sys
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# Corpus à décrire : celui des humanités numériques par défaut,
# ou celui passé en argument sur la ligne de commande.
FICHIER_CORPUS = Path(sys.argv[1] if len(sys.argv) > 1
                      else "corpus/hn_fr/wikipedia_fr_humanites_numeriques.txt")
# wiki2iramuteq range les métadonnées à côté du corpus, avec le suffixe _metadonnees.csv
FICHIER_META = FICHIER_CORPUS.with_name(FICHIER_CORPUS.stem + "_metadonnees.csv")

DOSSIER_RESULTATS = Path("resultats")
DOSSIER_RESULTATS.mkdir(exist_ok=True)
FICHIER_GRAPHIQUE = DOSSIER_RESULTATS / (FICHIER_CORPUS.stem + "_longueurs.png")
FICHIER_SORTIE = DOSSIER_RESULTATS / (FICHIER_CORPUS.stem + "_taille.txt")

meta = pd.read_csv(FICHIER_META, encoding="utf-8")
# Le CSV liste aussi les articles écartés lors de la constitution du corpus
# (colonne retenu = 0) : on ne garde que ceux présents dans le corpus.
meta = meta[meta["retenu"] == 1].reset_index(drop=True)
print(f"Nombre d'articles : {len(meta)}")
print(meta[["titre", "mots"]].head())


# %% 2. Statistiques descriptives sur la longueur des articles
print("\nLongueur des articles (en mots) :")
print(meta["mots"].describe().round(0))
print(f"Total : {meta['mots'].sum()} mots")

# Une moyenne très supérieure à la médiane signale une distribution
# asymétrique : quelques articles très longs tirent la moyenne vers le haut.
print(f"Moyenne : {meta['mots'].mean():.0f} - Médiane : {meta['mots'].median():.0f}")


# %% 3. Mesurer la concentration : quelle part du texte font les plus longs articles ?
tri = meta.sort_values("mots", ascending=False).reset_index(drop=True)
tri["part_%"] = 100 * tri["mots"] / tri["mots"].sum()
tri["part_cumulee_%"] = tri["part_%"].cumsum()
print("\nLes articles les plus longs :")
print(tri[["titre", "mots", "part_%", "part_cumulee_%"]].head(6).round(1))

# Nombre d'articles nécessaires pour atteindre la moitié du texte
n_moitie = (tri["part_cumulee_%"] < 50).sum() + 1
print(f"\n{n_moitie} articles sur {len(tri)} font la moitié du corpus.")


# %% 4. Estimer le poids de chaque article dans une classification Reinert
# IRaMuTeQ découpe les textes en segments d'environ 40 mots, et c'est sur
# ces segments que travaille la classification. Un article long fournit
# donc beaucoup plus de segments qu'un article court.
TAILLE_SEGMENT = 40
meta["segments_estimes"] = (meta["mots"] / TAILLE_SEGMENT).round().astype(int)
courts = meta[meta["segments_estimes"] < 5]
print(f"\nArticles de moins de 5 segments ({len(courts)}) :")
print(courts[["titre", "mots", "segments_estimes"]].to_string(index=False))


# %% 5. Visualiser la distribution des longueurs
fig, ax = plt.subplots(figsize=(11, 5))
ax.bar(range(len(tri)), tri["mots"], color="#4C78A8")
ax.set_xlabel("Articles, du plus long au plus court")
ax.set_ylabel("Nombre de mots")
ax.set_title(f"Longueur des {len(tri)} articles du corpus {FICHIER_CORPUS.stem}")
ax.set_xticks(range(len(tri)))
# Les titres trop longs sont raccourcis pour garder le graphique lisible
etiquettes = [t if len(t) <= 35 else t[:33] + "…" for t in tri["titre"]]
ax.set_xticklabels(etiquettes, rotation=90, fontsize=7)

# Courbe de part cumulée sur un second axe
ax2 = ax.twinx()
ax2.plot(range(len(tri)), tri["part_cumulee_%"], color="#E45756", marker=".")
ax2.axhline(50, color="#E45756", linestyle=":", linewidth=1)
ax2.set_ylabel("Part cumulée du corpus (%)", color="#E45756")
ax2.set_ylim(0, 105)
fig.tight_layout()
fig.savefig(FICHIER_GRAPHIQUE, dpi=150)
print(f"\nGraphique enregistré : {FICHIER_GRAPHIQUE}")


# %% 6. Découper la longueur en trois classes : les terciles
# On coupe à 1/3 et 2/3 de la distribution, ce qui donne trois groupes
# d'effectifs égaux. Ce choix est justifié plus bas dans l'article.
seuil_bas, seuil_haut = meta["mots"].quantile([1 / 3, 2 / 3])
print(f"\nSeuils des terciles : {seuil_bas:.0f} mots et {seuil_haut:.0f} mots")

meta["taille"] = pd.qcut(meta["mots"], q=3, labels=["courte", "moyenne", "longue"])

# Vérification : effectifs et part du texte par classe
bilan = meta.groupby("taille", observed=True).agg(
    articles=("titre", "count"),
    mots_min=("mots", "min"),
    mots_max=("mots", "max"),
    mots_total=("mots", "sum"),
)
bilan["part_du_texte_%"] = (100 * bilan["mots_total"] / meta["mots"].sum()).round(1)
print(bilan)


# %% 7. Ajouter la variable étoilée *taille_ dans le corpus IRaMuTeQ
# Chaque texte commence par une ligne "**** *var_modalite ...".
# On retrouve l'article grâce à sa variable *id_, puis on ajoute
# *taille_courte, *taille_moyenne ou *taille_longue en fin de ligne.
taille_par_id = dict(zip(meta["id"], meta["taille"].astype(str)))

lignes_sorties = []
modifiees = 0
with open(FICHIER_CORPUS, encoding="utf-8") as f:
    for ligne in f:
        if ligne.startswith("****"):
            variables = ligne.split()
            # On cherche la variable *id_ et on extrait l'identifiant
            ident = next(v[len("*id_"):] for v in variables if v.startswith("*id_"))
            # On supprime une éventuelle ancienne variable *taille_
            variables = [v for v in variables if not v.startswith("*taille_")]
            variables.append(f"*taille_{taille_par_id[ident]}")
            ligne = " ".join(variables) + "\n"
            modifiees += 1
        lignes_sorties.append(ligne)

with open(FICHIER_SORTIE, "w", encoding="utf-8") as f:
    f.writelines(lignes_sorties)

print(f"\n{modifiees} en-têtes enrichis -> {FICHIER_SORTIE}")


# %% 8. Vérifier le résultat
with open(FICHIER_SORTIE, encoding="utf-8") as f:
    entetes = [l.strip() for l in f if l.startswith("****")]
print(f"Nombre de textes : {len(entetes)}")
for e in entetes[:3]:
    print(e)
