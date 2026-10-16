# Prog FFLogs → image à lien fixe

Un petit programme Windows qui surveille les logs envoyés sur FFLogs par l'application **Archon**,
calcule la progression du static (meilleurs % et boss/phases vaincus) et publie une image PNG sur
**GitHub Pages**, gratuitement, à une adresse qui ne change jamais :

```
https://<utilisateur>.github.io/<depot>/prog.png
```

## Fonctionnement

1. Au démarrage de Windows, `prog_tracker.py` se lance en arrière-plan (icône orange dans la barre des tâches).
2. Toutes les 2 minutes quand Archon (ou ACT) est ouvert, sinon toutes les 15 minutes, il demande à
   l'API FFLogs la liste des rapports du static pour le contenu sélectionné.
3. S'il y a un nouveau rapport (ou si un rapport en direct a grandi), il récupère les combats,
   calcule la progression et génère l'image :
   - image du contenu et de chaque boss (visuels officiels FFLogs),
   - meilleur pourcentage atteint par boss (et la phase pour les fights à phases),
   - nombre de boss vaincus (raid) ou de phases franchies (ultime).
4. Si la progression a changé, l'image est poussée dans la branche `gh-pages` du dépôt. GitHub Pages
   la sert à la même adresse.

Le menu de l'icône permet de **changer de contenu** (ex. *AAC Heavyweight*), de forcer une mise à
jour et d'ouvrir l'image.

## Installation

### 1. Dépôt GitHub (hébergement)

1. Créez un dépôt **public** (ex. `fflogs-prog`) et poussez-y ce code.
2. Créez un jeton : *Settings → Developer settings → Fine-grained tokens* → accès au seul dépôt
   `fflogs-prog`, permission **Contents : Read and write**.
3. Lancez une première fois le programme (étape 3) : il crée la branche `gh-pages`.
4. Dans le dépôt : *Settings → Pages → Source : Deploy from a branch → `gh-pages` / `(root)`*.

### 2. Accès à l'API FFLogs

Sur <https://www.fflogs.com/api/clients/>, créez un client (nom libre, URL de redirection
`http://localhost`) et notez le *Client ID* et le *Client Secret*.

### 3. Sur le PC Windows

Prérequis : [Python 3.10+](https://www.python.org/downloads/) (cocher « Add to PATH »).

```powershell
powershell -ExecutionPolicy Bypass -File install.ps1
```

Le premier lancement crée `config.json` et l'ouvre dans le Bloc-notes. Remplissez :

| Clé | Valeur |
|---|---|
| `team_name` | Texte affiché sous le titre (ex. `Wipe Lotus`) |
| `zone_id` | Contenu suivi (modifiable ensuite depuis l'icône) |
| `difficulty` | `101` = Sadique, `100` = Normal, `null` = tout (ignoré pour les ultimes) |
| `fflogs.client_id` / `client_secret` | Étape 2 |
| `fflogs.guild_name` / `server` / `region` | Guilde FFLogs qui contient le static |
| `fflogs.static_tag_id` | ID du static « Wipe Lotus » (voir ci-dessous), `null` = toute la guilde |
| `github.token` / `repo` | Étape 1 (`repo` = `utilisateur/fflogs-prog`) |

Pour trouver l'ID de la guilde, du static et des contenus :

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

- **Logs privés** : l'API en mode « client » ne voit que les rapports publics ou non listés. Les
  rapports *privés* n'apparaîtront pas.
- **Cache** : GitHub Pages met en cache ~10 minutes, et Discord garde longtemps les images déjà
  affichées. Pour Discord, ajouter un paramètre au lien (`prog.png?v=2`) force le rechargement.
- **Désinstaller** : supprimez le raccourci `Prog FFLogs` du dossier `shell:startup`.
