# 📈 Projet Big Data — Affichage Boursier (2019-2024)

Ce projet permet de visualiser les données boursières de 2019 à 2024 avec plusieurs outils graphiques :
- 📉 **Graphique linéaire** (line chart)
- 📊 **Bougies** (candlestick)
- 📈 **Bandes de Bollinger**  

Fonctionnalités supplémentaires:
- 🔎 **Zoom interactif** pour explorer les détails du graphique
- 📉 **Matrice de corrélation** pour analyser les relations entre différentes actions (voir la partie "Matrice de corrélation" ci-dessous)

## 📊 Matrice de Corrélation
Concrètement, que signifie la valeur dans une case ?
- Corrélation ➔ 1 : les deux actions évoluent dans le même sens (si l'une monte, l'autre monte aussi, au même rythme).
- Corrélation ➔ 0 :  pas de lien clair entre les deux (leurs mouvements sont indépendants).
- Corrélation ➔ -1 :  les deux actions évoluent en sens opposé (si l'une monte, l'autre descend).

**En couleurs :**
- Jaune/vert clair ➔ Corrélation positive forte (très liées).
- Bleu/violet ➔ Corrélation négative ou faible.

## 🚀 Lancer le projet

1. **Modifier le `docker-compose.yml`**  
   Remplacer la valeur du volume de données par le chemin correct vers vos fichiers de données.

2. **Lancer le projet**
   ```bash
   make all
   ```

3. Le projet sera accessible sur :  
   ```
   http://localhost:8050
   ```

## 📂 Pré-requis

- `docker` et `docker-compose`
- `make