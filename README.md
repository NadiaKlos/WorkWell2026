# 🎡 Tirage au Sort par Groupes

Application **Streamlit** de répartition aléatoire de participants dans des groupes, sans remise — inspirée de Wheel of Names.

---

## 🚀 Lancement rapide

```bash
pip install -r requirements.txt
streamlit run app.py
```

---

## ✨ Fonctionnalités

| Fonctionnalité | Description |
|---|---|
| **Saisie des participants** | Un nom par ligne dans un champ texte |
| **Groupes configurables** | Nom + capacité modifiables, nombre de groupes dynamique |
| **Tirage sans remise** | Chaque place et chaque participant ne sont tirés qu'une seule fois |
| **Roue de la fortune** | Roue HTML/CSS/JS animée affichant les participants restants |
| **Historique temps réel** | Tableau Pandas mis à jour après chaque tirage |
| **Barre de progression** | Avancement visuel du tirage |
| **Export CSV** | Téléchargement des résultats en un clic |
| **Résumé final** | Tableau récapitulatif par groupe à la fin du tirage |
| **Session persistante** | `st.session_state` — le rechargement ne perd pas les données |

---

## ⚙️ Configuration par défaut

| Groupe | Places |
|---|---|
| La Crypte | 4 |
| L'Immortel | 3 |

Le nombre total de places **doit correspondre** au nombre de participants avant de lancer le tirage.

---

## 📁 Structure du projet

```
tirage/
│
├── app.py            ← Application principale
├── requirements.txt  ← Dépendances Python
└── README.md         ← Ce fichier
```

---

## 🎲 Déroulement du tirage

1. Saisissez les noms des participants (un par ligne).
2. Configurez les groupes et leur capacité.
3. Cliquez sur **🚀 Commencer le tirage**.
4. Cliquez sur **🎲 Tirer au sort** autant de fois que nécessaire.
5. Chaque clic attribue un participant aléatoire à un groupe aléatoire.
6. Une fois tous les participants attribués, le résultat final s'affiche.
7. Téléchargez les résultats en CSV si besoin.

---

## 🛠️ Technologies

- [Streamlit](https://streamlit.io/) — interface web
- [Pandas](https://pandas.pydata.org/) — gestion des données
- HTML / CSS / JavaScript — roue de la fortune animée (via `st.components.v1.html`)
