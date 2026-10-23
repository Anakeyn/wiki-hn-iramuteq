# -*- coding: utf-8 -*-
"""
nettoyer_corpus.py — Nettoie un corpus IRaMuTeQ issu de wiki2iramuteq
avant l'analyse.

Deux opérations :
1. supprimer les lignes de bibliographie (listes de publications des
   articles biographiques : ISBN, paginations « 368 p. ») ;
2. souder les noms composés et les noms de personnes avec un tiret bas,
   pour qu'IRaMuTeQ les traite comme une seule forme
   (« États-Unis » ne devient plus « unir », « Marin Dacos » ne donne
   plus le nom commun « marin »).

Usage :
    python3 nettoyer_corpus.py corpus/hn_fr/corpus.txt corpus/hn_fr/corpus_nettoye.txt

Licence du code : celle du dépôt. Textes : Wikipédia, CC BY-SA 4.0.
"""

# %% 1. Imports et arguments
import re
import sys
from pathlib import Path

if len(sys.argv) != 3:
    sys.exit("Usage : python3 nettoyer_corpus.py ENTREE.txt SORTIE.txt")

entree = Path(sys.argv[1])
sortie = Path(sys.argv[2])
lignes = entree.read_text(encoding="utf-8").splitlines()
print(f"{len(lignes)} lignes lues dans {entree}")

# %% 2. Repérer les lignes de bibliographie
# Une ligne est considérée comme une référence bibliographique si :
# - elle contient « ISBN » ;
# - ou elle contient une pagination (« 368 p. », « pp.465-476 »)
#   ET une année (1800-2099), et reste courte (moins de 400 caractères).
# Les lignes d'en-tête IRaMuTeQ (« **** *art_... ») ne sont jamais touchées.

RE_ISBN = re.compile(r"\bISBN\b", re.IGNORECASE)
RE_PAGES = re.compile(r"\b\d{1,4}\s?p\.|\bpp\.\s?\d")
RE_ANNEE = re.compile(r"\b(18|19|20)\d{2}\b")


RE_PARENTHESES = re.compile(r"\([^()]*\)")


def ressemble_a_une_reference(texte: str) -> bool:
    return (
        bool(RE_PAGES.search(texte))
        and bool(RE_ANNEE.search(texte))
        and len(texte) < 400
    )


def est_bibliographique(ligne: str) -> bool:
    if ligne.startswith("****"):
        return False
    if RE_ISBN.search(ligne):
        return True
    if not ressemble_a_une_reference(ligne):
        return False
    # Cas d'une phrase de prose qui cite un ouvrage entre parenthèses :
    # si, une fois les parenthèses retirées, la ligne ne ressemble plus
    # à une référence, ce n'est pas une ligne de bibliographie.
    return ressemble_a_une_reference(RE_PARENTHESES.sub("", ligne))


def retirer_references_entre_parentheses(ligne: str) -> str:
    """Dans une ligne de prose, supprime les parenthèses qui contiennent
    une référence (année + pagination), et garde le reste."""
    def remplacer(m):
        return "" if ressemble_a_une_reference(m.group(0)) else m.group(0)
    return re.sub(r"\s?\([^()]*\)", remplacer, ligne)


# %% 3. Souder les expressions à garder en une seule forme
# IRaMuTeQ considère le tiret bas comme un caractère de mot :
# « Marin_Dacos » reste une seule forme, classée « nr » (non reconnue).
# La liste est volontairement courte : on ne soude que ce que les
# statistiques ont montré comme mal lemmatisé.

A_SOUDER = [
    "États-Unis",
    "Marin Dacos",
    "Pierre Mounier",
    "Damon Mayaffre",
    "Étienne Brunet",
    "Clarisse Bardiot",
    "Franco Moretti",
    "Roberto Busa",
]


def souder(ligne: str) -> str:
    for expr in A_SOUDER:
        soude = re.sub(r"[\s\-]+", "_", expr)
        ligne = re.sub(re.escape(expr), soude, ligne)
    return ligne


# %% 4. Appliquer et compter
gardees, supprimees = [], []
article = None
par_article = {}

for ligne in lignes:
    if ligne.startswith("****"):
        article = ligne.split()[1] if len(ligne.split()) > 1 else ligne
        gardees.append(ligne)
        continue
    if est_bibliographique(ligne):
        supprimees.append(ligne)
        par_article[article] = par_article.get(article, 0) + 1
    else:
        gardees.append(souder(retirer_references_entre_parentheses(ligne)))

# %% 5. Écrire le corpus nettoyé et un journal des suppressions
sortie.write_text("\n".join(gardees) + "\n", encoding="utf-8")
journal = sortie.with_name(sortie.stem + "_lignes_supprimees.txt")
journal.write_text("\n".join(supprimees) + "\n", encoding="utf-8")

# %% 6. Écrire les métadonnées du corpus nettoyé
# decrire_corpus.py lit la longueur des articles dans la colonne « mots »
# du fichier <corpus>_metadonnees.csv. On recompte donc les mots de chaque
# article dans le texte nettoyé, pour que les terciles portent sur le texte
# réellement analysé. Le comptage (mots séparés par des espaces) est le même
# pour tous les articles, ce qui garde les longueurs comparables entre elles.
import csv

meta_entree = entree.with_name(entree.stem + "_metadonnees.csv")
meta_sortie = sortie.with_name(sortie.stem + "_metadonnees.csv")

mots_par_id, ident = {}, None
for ligne in gardees:
    if ligne.startswith("****"):
        ident = next((v[len("*id_"):] for v in ligne.split()
                      if v.startswith("*id_")), None)
        mots_par_id[ident] = 0
    elif ident is not None:
        mots_par_id[ident] += len(ligne.split())

if meta_entree.exists():
    with meta_entree.open(encoding="utf-8", newline="") as f:
        lecteur = csv.DictReader(f)
        champs = lecteur.fieldnames
        lignes_meta = list(lecteur)
    for m in lignes_meta:
        if m["id"] in mots_par_id:
            m["mots"] = mots_par_id[m["id"]]
    with meta_sortie.open("w", encoding="utf-8", newline="") as f:
        ecrivain = csv.DictWriter(f, fieldnames=champs)
        ecrivain.writeheader()
        ecrivain.writerows(lignes_meta)
    total = sum(mots_par_id.values())
    print(f"Métadonnées recalculées ({total} mots) : {meta_sortie}")
else:
    print(f"Attention : {meta_entree} introuvable, métadonnées non écrites.")

print(f"{len(supprimees)} lignes bibliographiques supprimées :")
for art, n in sorted(par_article.items(), key=lambda x: -x[1]):
    print(f"  {art} : {n}")
print(f"Corpus nettoyé : {sortie}")
print(f"Lignes supprimées (à relire) : {journal}")
