# 🎧 SC Coups de Cœur Extractor

**SC Coups de Cœur Extractor** est un outil Python permettant d’extraire automatiquement les albums d’une ou plusieurs **listes SensCritique**, afin de les exporter sous forme de CSV exploitables (par exemple pour créer des playlists Spotify).

> 🚀 Objectif futur : permettre à tout le monde de générer automatiquement une **playlist Spotify** à partir d’une liste SensCritique.

---

## ✨ Fonctionnalités

- 🧭 Extraction automatique des albums d’une liste SensCritique.  
- 📄 Export CSV contenant :
  - le titre de l’album  
  - le(s) artiste(s)  
  - le lien SensCritique  
  - la période du “coup de cœur”  
- 📂 Traitement possible de **plusieurs listes** en une seule commande via un fichier texte.  
- 📸 Captures d’écran automatiques en cas d’erreur pour faciliter le debug.

---

## 🧱 Prérequis

### ✅ Python 3.10 ou supérieur

Vérifie la version installée :
```bash
python --version
```

### ✅ Dépendances Python

Les dépendances principales sont :
- **Playwright** (automatisation du navigateur)
- **Pandas** (manipulation de CSV)

Installe-les automatiquement via `requirements.txt` :
```bash
pip install -r requirements.txt
```

Fichier `requirements.txt` :
```txt
pandas
playwright
```

Installe ensuite les navigateurs Playwright :
```bash
playwright install
```

---

## ⚙️ Installation complète (première fois)

### 1️⃣ Cloner le dépôt
```bash
git clone https://github.com/marccharton/sc_coups_de_coeur_extractor.git
cd sc_coups_de_coeur_extractor
```

### 2️⃣ Créer un environnement virtuel (recommandé)
```bash
python -m venv .venv
```

Active-le :
- **Windows :**
  ```bash
  .venv\Scripts\Activate
  ```
- **macOS / Linux :**
  ```bash
  source .venv/bin/activate
  ```

### 3️⃣ Installer les dépendances
```bash
pip install -r requirements.txt
```

### 4️⃣ Installer les navigateurs Playwright
```bash
playwright install
```

---

## ▶️ Utilisation

### 🔹 Mode simple — une seule liste
```bash
python sc_list_scraper.py "https://www.senscritique.com/liste/coups_de_coeur_2025_2026/4046513"
```

Cela génère un fichier `senscritique_albums.csv` dans le dossier courant.

---

### 🔹 Mode multi-listes — via un fichier `lists.txt`

1. Crée un fichier `lists.txt` :
   ```
   https://www.senscritique.com/liste/coups_de_coeur_2025_2026/4046513
   https://www.senscritique.com/liste/coups_de_coeur_2023_2024/3753982
   ...
   ```

2. Lance la commande :
   ```bash
   python sc_list_scraper.py lists.txt
   ```

3. Chaque liste sera exportée automatiquement dans le dossier `exports/`,  
   sous un nom du type :
   ```
   albums_2025-2026.csv
   albums_2023-2024.csv
   ...
   ```

---

## 🧩 Structure du projet

```
.
├── sc_list_scraper.py    # Script principal
├── lists.txt             # (Optionnel) fichier contenant plusieurs liens SensCritique
├── exports/              # Dossier de sortie des CSV
├── screenshots/          # Captures automatiques en cas d’erreur
├── requirements.txt      # Dépendances du projet
└── README.md             # Documentation
```

---

## ⚙️ Options disponibles

| Option | Description |
|--------|--------------|
| `--headful` | Ouvre le navigateur (utile pour le debug) |
| `--outdir` | Dossier de sortie (par défaut : `exports/`) |
| `--max-scrolls` | Nombre max de scrolls pour charger toute la liste |
| `--scroll-wait` | Délai entre deux scrolls (en ms) |
| `--nav-timeout` | Timeout de navigation (en ms) |
| `--screenshots` | Dossier pour les captures d’écran en cas d’erreur |

**Exemple :**
```bash
python sc_list_scraper.py lists.txt --headful --max-scrolls 20 --scroll-wait 300
```

---

## 🧪 Exemple de résultat CSV

| album_title | artist | sc_album_url | year_label | sc_list_url |
|--------------|---------|---------------|-------------|--------------|
| Alligator Bites Never Heal | Doechii | https://www.senscritique.com/album/alligator_bites_never_heal/98112635 | 2025-2026 | https://www.senscritique.com/liste/coups_de_coeur_2025_2026/4046513 |
| Habib Galbi | A‐WA | https://www.senscritique.com/album/Habib_Galbi/19033197 | 2025-2026 | ... |

---

## 🚧 Roadmap

- 🎵 Génération automatique de playlists Spotify depuis les CSV.  
- 🧩 Interface web simple : coller un lien SensCritique → obtenir la playlist Spotify.  
- 🧠 Détection améliorée des artistes et labels.

---

## 🤝 Contribution

Les contributions sont les bienvenues !

1. Fork le dépôt  
2. Crée une branche (`git checkout -b feature/ma-fonctionnalite`)  
3. Commit (`git commit -m "Ajout de ma fonctionnalité"`)  
4. Push (`git push origin feature/ma-fonctionnalite`)  
5. Ouvre une Pull Request 🚀

---

## 📜 Licence

MIT © 2025 [Marc Charton](https://github.com/marccharton)

---

## 💬 Remerciements

Projet initialement développé pour faciliter la documentation et la création de playlists musicales personnelles.  
Merci à la communauté SensCritique pour l’inspiration et aux contributeurs Playwright pour leur outil magique ✨
