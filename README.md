# Prog FFLogs → image à lien fixe

Un petit programme Windows qui surveille les logs envoyés sur FFLogs par l'application **Archon**,
calcule la progression du static (meilleurs % et boss/phases vaincus) et publie une image PNG sur
**GitHub Pages**, gratuitement, à une adresse qui ne change jamais :

```
https://nicolasmelet.github.io/Static_picture_xiv/prog.png
```

## Fonctionnement

1. Au démarrage de Windows, `prog_tracker.py` se lance en arrière-plan (icône orange dans la barre des tâches).
2. Toutes les 5 minutes quand Archon (ou ACT) est ouvert, il demande à l'API FFLogs la liste des
   rapports du static pour le contenu sélectionné, puis une dernière fois à leur fermeture.
   Quand ni Archon ni ACT ne tournent, FFLogs n'est jamais interrogé (seule la liste des
   processus Windows est regardée toutes les 30 s). Le bouton « Mettre à jour maintenant »
   et le changement de contenu interrogent FFLogs immédiatement.
3. S'il y a un nouveau rapport (ou si un rapport en direct a grandi), il récupère les combats,
   calcule la progression et génère l'image :
   - image du contenu et de chaque boss (visuels officiels FFLogs),
   - meilleur pourcentage atteint par boss (et la phase pour les fights à phases),
   - nombre de boss vaincus (raid) ou de phases franchies (ultime).
4. Si la progression a changé, l'image est poussée dans la branche `gh-pages` du dépôt (au plus
   une fois toutes les 10 minutes, voir plus bas). GitHub Pages la sert à la même adresse.

Le menu de l'icône permet de **changer de contenu** (ex. *AAC Heavyweight*), de forcer une mise à
jour et d'ouvrir l'image.

## Installation

### 1. Dépôt GitHub (hébergement)

1. Le code est dans le dépôt public `NicolasMelet/Static_picture_xiv`.
2. Créez un jeton : *Settings → Developer settings → Fine-grained tokens* → accès au seul dépôt
   `Static_picture_xiv`, permission **Contents : Read and write**. Choisissez une date
   d'expiration lointaine : à l'expiration, les publications échouent (voir le journal).
3. La branche `gh-pages` existe déjà : elle ne contient que le site (`prog.png`, une page
   `index.html` qui affiche l'image, et `.nojekyll` pour un déploiement plus rapide).
4. Dans le dépôt : *Settings → Pages → Source : Deploy from a branch → `gh-pages` / `(root)`*.

### 2. Accès à l'API FFLogs

Sur <https://www.fflogs.com/api/clients/>, créez un client (nom libre, URL de redirection
`http://localhost`) et notez le *Client ID* et le *Client Secret*.

### 3. Sur le PC Windows

Prérequis : [Python 3.10+](https://www.python.org/downloads/) (cocher « Add to PATH »).

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Le premier lancement crée deux fichiers et les ouvre dans le Bloc-notes.

**`.env` : les clés secrètes.** Ce fichier est ignoré par git (`.gitignore`) et ne sera jamais
poussé sur GitHub. Seul le modèle `.env.example`, sans valeurs, est dans le dépôt.

| Clé | Valeur |
|---|---|
| `FFLOGS_CLIENT_ID` / `FFLOGS_CLIENT_SECRET` | Étape 2 |
| `GITHUB_TOKEN` | Étape 1 |

**`config.json` : les réglages** (lui aussi ignoré par git, le programme le modifie quand vous
changez de contenu) :

| Clé | Valeur |
|---|---|
| `team_name` | Texte affiché sous le titre (ex. `Wipe Lotus`) |
| `zone_id` | Contenu suivi (modifiable ensuite depuis l'icône) |
| `difficulty` | `101` = Sadique, `100` = Normal, `null` = tout (ignoré pour les ultimes) |
| `fflogs.static_id` | ID du static : le nombre dans l'adresse de sa page FFLogs (`fflogs.com/guild/id/12345`). Laisser `null` pour le retrouver avec les deux lignes suivantes |
| `fflogs.static_name` | Nom du static (`Wipe Lotus`) |
| `fflogs.guild_name` / `server` / `region` | Free Company FFLogs dont dépend le static (inutile si `static_id` est rempli) |
| `fflogs.raid_team_id` | Optionnel : ne suivre qu'une « équipe » (raid team) du static, `null` = tout le static |
| `github.repo` | `NicolasMelet/Static_picture_xiv` |
| `github.min_publish_seconds` | Délai minimal entre deux publications (défaut 600 s) |

Pour trouver les ID de la Free Company, du static et des contenus :

```powershell
.venv\Scripts\python.exe prog_tracker.py --setup
```

Relancez ensuite `install.ps1` : il ajoute le raccourci dans le dossier *Démarrage* et lance le suivi.

Test manuel (génère et publie une fois) :

```powershell
.venv\Scripts\python.exe prog_tracker.py --once
```

Le journal est dans `prog_tracker.log`.

## Bon à savoir

- **Logs privés** : l'API en mode « client » ne voit pas les rapports *privés*. Les rapports
  publics sont pris en compte ; les rapports *non listés* sont lus quand FFLogs les inclut dans
  la liste du static.
- **Désinstaller** : supprimez le raccourci `Prog FFLogs` du dossier `shell:startup`.

## GitHub Pages : ce qu'il faut savoir

GitHub Pages sert gratuitement les fichiers d'une branche d'un dépôt comme un site web statique.
Ici, la branche `gh-pages` contient `prog.png`, servi à
`https://nicolasmelet.github.io/Static_picture_xiv/prog.png`. À chaque fois que le programme
remplace l'image (un commit sur `gh-pages`), GitHub redéploie le site.

- **Délai de mise en ligne** : le déploiement prend en général moins d'une minute (onglet
  *Actions* du dépôt, « pages build and deployment »).
- **Cache** : l'image est mise en cache jusqu'à ~10 minutes par le CDN de GitHub. Discord garde en
  plus très longtemps les images déjà affichées ; ajouter un paramètre au lien (`prog.png?v=2`)
  force le rechargement.
- **Limite de déploiements** : GitHub recommande au plus ~10 déploiements par heure. Le programme
  ne publie donc qu'une fois toutes les 10 minutes au maximum ; une image en attente est publiée
  dès que le délai est écoulé (sans réinterroger FFLogs).
- **Tout est public** : avec un compte gratuit, Pages exige un dépôt public. Le code et l'image
  sont visibles par tous ; les clés, elles, restent dans `.env` sur votre PC.
- **Historique** : chaque mise à jour ajoute un commit sur `gh-pages` (quelques dizaines de Ko).
  Sans importance à l'échelle d'un tier, la limite de taille d'un site Pages étant de 1 Go.
- **La branche `gh-pages`** est indépendante de `main` : elle ne contient que le site, le code
  reste sur `main`. Le programme y remplace seulement `prog.png`. La page
  <https://nicolasmelet.github.io/Static_picture_xiv/> affiche l'image et la recharge toutes les
  5 minutes.
