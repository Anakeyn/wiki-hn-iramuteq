# wiki-hn-iramuteq

Les humanités numériques vues par Wikipédia : décrire et analyser avec [IRaMuTeQ](https://pratinaud.gitpages.huma-num.fr/iramuteq-website/) le corpus des 45 articles de la catégorie « Humanités numériques » de la Wikipédia en français.

Ce dépôt accompagne l'article de blog du même nom. Il fait suite à [wiki2iramuteq](https://github.com/Anakeyn/wiki2iramuteq), l'outil qui a constitué le corpus.

## Sommaire

1. [Fichiers prêts à l'emploi](#1-fichiers-prêts-à-lemploi--aucune-commande-nécessaire)
2. [Ce que fait `decrire_corpus.py`](#2-ce-que-fait-decrire_corpuspy)
3. [Utiliser le script](#3-utiliser-le-script)
4. [Pourquoi trois tailles, et pourquoi ces seuils ?](#4-pourquoi-trois-tailles-et-pourquoi-ces-seuils-)
5. [Licences et citation](#5-licences-et-citation)

## 1. Fichiers prêts à l'emploi : aucune commande nécessaire

| Fichier | Contenu |
|---|---|
| `corpus/hn_fr/wikipedia_fr_humanites_numeriques.txt` | Le corpus d'origine, extrait le 20 octobre 2026 avec wiki2iramuteq |
| `corpus/hn_fr/wikipedia_fr_humanites_numeriques_metadonnees.csv` | Ses métadonnées : titre, URL, révision, nombre de mots |
| `resultats/wikipedia_fr_humanites_numeriques_taille.txt` | **Le corpus enrichi** de la variable `*taille_`, à ouvrir dans IRaMuTeQ |
| `resultats/wikipedia_fr_humanites_numeriques_longueurs.png` | Le graphique des longueurs d'articles |

**Pour récupérer un fichier :** sur GitHub, cliquez sur le fichier, puis sur le bouton de téléchargement (*Download raw file*). Vous pouvez aussi récupérer tout le dépôt avec le bouton vert **Code → Download ZIP**.

**Pour l'ouvrir dans IRaMuTeQ :** *Fichier → Ouvrir un corpus*, encodage **utf-8**, langue **français**.

Le corpus enrichi est identique au corpus d'origine. Seule change la ligne d'en-tête de chaque article, qui reçoit une variable de plus :

```
**** *art_Lexicometrie *id_Lexicometrie *cat_Humanites_numeriques *prof_0 *lang_fr *taille_courte
```

## 2. Ce que fait `decrire_corpus.py`

Le script suit huit étapes, repérées par des blocs `# %%` dans le code :

1. Il charge le fichier de métadonnées et ne garde que les articles présents dans le corpus.
2. Il calcule les statistiques de longueur : moyenne, médiane, quartiles.
3. Il mesure la concentration : combien d'articles font la moitié du texte.
4. Il estime le nombre de segments que chaque article fournira à IRaMuTeQ.
5. Il trace le graphique des longueurs, avec la part cumulée du corpus.
6. Il découpe les articles en trois tailles d'effectifs égaux (terciles).
7. Il ajoute la variable `*taille_courte`, `*taille_moyenne` ou `*taille_longue` dans l'en-tête de chaque article.
8. Il vérifie le corpus produit.

Sur le corpus des humanités numériques, il montre que **7 articles sur 45 font plus de la moitié du texte**. L'article « Humanités numériques » en fait à lui seul 15 %.

## 3. Utiliser le script

### Prérequis

Il faut Python 3.8 ou plus récent, avec les bibliothèques `pandas` et `matplotlib` :

```bash
pip install -r requirements.txt
```

- **Linux, macOS** : les commandes s'utilisent telles quelles.
- **Windows** : installez Python depuis [python.org](https://www.python.org/downloads/) en cochant *Add Python to PATH*. Dans les commandes, remplacez `python3` par `python`.

Téléchargez le dépôt (**Code → Download ZIP**), décompressez-le, puis ouvrez un terminal dans ce dossier.

### Sur le corpus des humanités numériques

```bash
python3 decrire_corpus.py
```

### Sur un autre corpus produit par wiki2iramuteq

Donnez le chemin du fichier `.txt`. Le script cherche le fichier `_metadonnees.csv` dans le même dossier :

```bash
python3 decrire_corpus.py ../wiki2iramuteq/corpus/num_br/wikipedia_br_numerique_filtre.txt
```

Les résultats sont écrits dans le dossier `resultats/`, au nom du corpus.

## 4. Pourquoi trois tailles, et pourquoi ces seuils ?

**Pourquoi une variable de taille ?** La classification de Reinert d'IRaMuTeQ ne travaille pas sur les articles, mais sur des segments d'environ 40 mots. Un article de 6 500 mots fournit environ 160 segments, un article de 60 mots un seul. Les articles longs pèsent donc beaucoup plus dans la formation des classes. Avec la variable `*taille_`, on vérifie après coup si une classe est surtout portée par les articles longs : elle traduit alors un effet de volume plutôt qu'un thème partagé par le corpus.

**Pourquoi des terciles ?** Les seuils coupent la distribution à 1/3 et 2/3, soit ici 360 et 832 mots. Ce choix a trois avantages :
- **Des effectifs équilibrés.** Chaque modalité compte 15 articles, ce qui garde interprétables les tests du chi² d'IRaMuTeQ.
- **Pas de seuil arbitraire.** Les bornes viennent de la distribution elle-même et se recalculent sur n'importe quel autre corpus.
- **Une robustesse aux valeurs extrêmes.** La moyenne (966 mots) est tirée vers le haut par quelques articles très longs, alors que la médiane est de 538 mots. Un découpage par rangs n'y est pas sensible.

| Taille | Articles | Mots | Part du texte |
|---|---|---|---|
| courte | 15 | 58 à 348 | 7,4 % |
| moyenne | 15 | 366 à 821 | 19,5 % |
| longue | 15 | 855 à 6 508 | 73,1 % |

**La limite :** les trois tailles ont le même nombre d'articles, mais pas le même poids. Les 15 articles longs font 73 % du texte. C'est précisément ce déséquilibre que la variable rend visible dans les résultats.

## 5. Licences et citation

- **Code** (`*.py`) : GPL-3.0-or-later, voir le fichier `LICENSE`.
- **Corpus** (dossiers `corpus/` et `resultats/`) : textes issus de Wikipédia, sous licence [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.fr). Les auteurs sont les contributeurs et contributrices de Wikipédia. Le fichier `*_metadonnees.csv` donne l'URL et le numéro de révision de chaque article. Toute réutilisation doit citer la source et rester sous la même licence.

**Pour citer ce travail :** Pierre Rouarch (Anakeyn), *wiki-hn-iramuteq : les humanités numériques vues par Wikipédia*, 2026, https://github.com/Anakeyn/wiki-hn-iramuteq.

Auteur : Pierre Rouarch, Anakeyn.

## Pour en savoir plus

- L'article de blog qui présente l'analyse pas à pas, avec le code commenté : *Les humanités numériques vues par Wikipédia : décrire et analyser un corpus avec IRaMuTeQ* (lien à venir).
- L'outil qui a constitué le corpus : [wiki2iramuteq](https://github.com/Anakeyn/wiki2iramuteq), et son [article de blog](https://www.anakeyn.com/2026/10/21/creer-des-corpus-iramuteq-a-partir-de-wikipedia-avec-python-wiki2iramuteq/).
