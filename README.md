# Suite Complète de Post-Production Vidéo et Audio

Bienvenue dans la documentation complète de la suite d'outils de post-production. Ce document couvre l'ensemble des fonctionnalités, des cas d'usage et des configurations avancées pour chaque script du projet.

## Table des Matières

1.  [Présentation Générale](#présentation-générale)
2.  [Prérequis et Installation](#prérequis-et-installation)
3.  [Partie 1 : L'Éditeur Vidéo (`main.py`)](#partie-1--léditeur-vidéo-mainpy)
    -   [Objectif et Fonctionnalités](#objectif-et-fonctionnalités)
    -   [Guide d'Utilisation de `main.py`](#guide-dutilisation-de-mainpy)
4.  [Partie 2 : Les Outils de Traitement Audio](#partie-2--les-outils-de-traitement-audio)
    -   [`audio_processor.py` : Le Studio par Lot](#audio_processorpy--le-studio-par-lot)
    -   [`audio_enhancer.py` : L'Améliorateur Rapide](#audio_enhancerpy--laméliorateur-rapide)
    -   [Guide d'Utilisation des Outils Audio](#guide-dutilisation-des-outils-audio)
5.  [Partie 3 : Configuration Avancée (Le Dictionnaire `CONFIG`)](#partie-3--configuration-avancée-le-dictionnaire-config)
    -   [Paramètres de Détection de Silence](#paramètres-de-détection-de-silence)
    -   [Configuration des Filtres Audio (dans `main.py`)](#configuration-des-filtres-audio-dans-mainpy)
    -   [Configuration des Filtres Audio Professionnels (dans les outils audio)](#configuration-des-filtres-audio-professionnels-dans-les-outils-audio)
    -   [Configuration du Mixage Musical (Ducking)](#configuration-du-mixage-musical-ducking)
    -   [Configuration de l'Encodage Vidéo](#configuration-de-lencodage-vidéo)
6.  [Licence](#licence)

---

## Présentation Générale

Ce projet n'est pas une seule application, mais une **suite de trois scripts en ligne de commande** conçus pour automatiser les tâches les plus fastidieuses de la post-production. Chaque script a un rôle précis :

-   **`main.py`** : Pour le traitement **vidéo**.
-   **`audio_processor.py`** : Pour le traitement **audio** par lot (dossiers).
-   **`audio_enhancer.py`** : Pour le traitement **audio** de fichiers uniques.

## Prérequis et Installation

La procédure d'installation est commune à tous les scripts.

### Prérequis

1.  **Python 3.8+**
2.  **FFmpeg** : C'est le moteur de tous les scripts. Il doit être installé et accessible depuis votre terminal.
    -   **Ubuntu/Debian** : `sudo apt update && sudo apt install ffmpeg`
    -   **macOS (Homebrew)** : `brew install ffmpeg`
    -   **Windows** : Téléchargez-le depuis le [site officiel](https://ffmpeg.org/download.html), décompressez-le, et ajoutez le chemin vers le dossier `bin` à vos variables d'environnement (`PATH`).

### Installation

1.  Clonez ce dépôt :
    ```bash
    git clone https://github.com/VOTRE_NOM_UTILISATEUR/video-cut.git
    cd video-cut
    ```

2.  Créez et activez un environnement virtuel (recommandé) :
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur Linux/macOS
    # .\venv\Scripts\Activate.ps1  # Sur Windows PowerShell
    ```

3.  Installez les dépendances Python :
    ```bash
    pip install -r requirements.txt
    ```

---

## Partie 1 : L'Éditeur Vidéo (`main.py`)

### Objectif et Fonctionnalités

Ce script est l'outil principal pour le **montage vidéo automatisé**. Il prend une vidéo brute et la transforme en un contenu dynamique et prêt à être publié.

-   **Jump Cuts Automatiques** : Supprime les silences de la vidéo pour un rythme plus soutenu.
-   **Amélioration Audio Intégrée** : Applique une chaîne de filtres à la piste audio de la vidéo pour améliorer la clarté de la voix.
-   **Fiabilité sur VFR** : Gère les vidéos à cadence d'images variable (VFR), typiques des enregistrements d'écran ou de smartphones, grâce à une option de pré-encodage qui prévient la désynchronisation audio/vidéo.
-   **Mixage Musical** : Ajoute une musique de fond avec un effet de *ducking* (le volume de la musique baisse quand la personne parle).

### Guide d'Utilisation de `main.py`

#### Commande de base

```bash
python main.py <fichier_entree> -o <fichier_sortie>
```

#### Cas 1 : Nettoyer un tutoriel enregistré avec OBS

Les enregistrements d'écran ont souvent une cadence d'images variable. L'option `--pre-encode-cfr` est **essentielle** pour éviter que le son et l'image ne se décalent.

```bash
python main.py "tuto_brut.mkv" -o "tuto_final.mp4" --pre-encode-cfr
```

#### Cas 2 : Ajouter une musique de fond à un vlog

```bash
python main.py "vlog_face_camera.mp4" -o "vlog_avec_musique.mp4" -m "musique_cool.mp3" --pre-encode-cfr
```

#### Cas 3 : Désactiver les filtres audio

Si vous souhaitez uniquement couper les silences sans toucher à l'audio.

```bash
python main.py "video.mp4" -o "video_coupee.mp4" --no-audio-filters
```

---

## Partie 2 : Les Outils de Traitement Audio

Ces deux scripts sont dédiés à la **post-production audio professionnelle**. Ils partagent la même technologie d'amélioration sonore (normalisation en 2 passes), mais pour des usages différents.

### `audio_processor.py` : Le Studio par Lot

C'est l'outil le plus puissant pour les projets de voix off. Il prend un **dossier complet** de fichiers audio, les assemble, puis les traite comme une seule piste.

-   **Idéal pour** : Les livres audio, les podcasts enregistrés en chapitres, les voix off de documentaires.

### `audio_enhancer.py` : L'Améliorateur Rapide

C'est une version simplifiée qui ne traite qu'**un seul fichier** à la fois. Il peut extraire l'audio d'une vidéo si nécessaire.

-   **Idéal pour** : Masteriser rapidement une interview, un mémo vocal, ou extraire et améliorer le son d'une vidéo pour l'utiliser ailleurs.

### Guide d'Utilisation des Outils Audio

#### Cas 1 : Assembler et masteriser une voix off (avec `audio_processor.py`)

Votre dossier `ma_voix_off/` contient `01_intro.wav`, `02_partie1.wav`, etc.

```bash
python audio_processor.py ./ma_voix_off/ -o voix_off_complete.mp3
```

Le script va créer un seul fichier `voix_off_complete.mp3`, nettoyé et masterisé.

#### Cas 2 : Améliorer une interview (avec `audio_enhancer.py`)

```bash
python audio_enhancer.py interview_brute.wav -o interview_masterisee.mp3
```

#### Cas 3 : Extraire l'audio d'une vidéo et y ajouter une musique

```bash
python audio_enhancer.py video_conference.mp4 -o audio_conference.mp3 -m musique_discrete.mp3
```

---

## Partie 3 : Configuration Avancée (Le Dictionnaire `CONFIG`)

Pour un contrôle total, vous pouvez modifier le dictionnaire `CONFIG` au début de chaque script. Ces changements seront permanents pour toutes les exécutions futures de ce script.

### Paramètres de Détection de Silence

Ces paramètres sont présents dans les trois scripts.

-   `SILENCE_THRESH_DB`: `(valeur en dB, ex: -40)`
    Seuil de volume en décibels (dBFS) en dessous duquel un son est considéré comme un silence. Une valeur plus proche de 0 (ex: -30) ne coupera que les silences les plus profonds. Une valeur plus basse (ex: -50) coupera plus agressivement, y compris les respirations.

-   `MIN_SILENCE_LEN_MS`: `(valeur en millisecondes, ex: 500)`
    Durée minimale d'un silence pour qu'il soit détecté et coupé. Augmentez cette valeur pour éviter de couper des pauses naturelles et courtes dans votre élocution.

-   `CHUNK_PADDING_MS` ou `CHUNK_KEEP_SILENCE_MS`: `(valeur en millisecondes, ex: 250)`
    Marge de sécurité ajoutée au début et à la fin de chaque segment sonore conservé. Cela évite que les coupures ne soient trop abruptes et ne coupent le début ou la fin d'un mot.

### Configuration des Filtres Audio (dans `main.py`)

La section `AUDIO_FILTERS` de `main.py` utilise une chaîne de filtres simple mais efficace.

-   `highpass=f=100`: **Filtre Coupe-Bas**. Supprime les fréquences très graves en dessous de 100 Hz, qui correspondent souvent à des bruits de micro, des vibrations ou des "pops".
-   `equalizer=...`: **Égaliseur**. Modifie le "timbre" de la voix. Ici, il réduit légèrement les fréquences autour de 300 Hz (qui peuvent rendre la voix boueuse) et augmente celles autour de 3000 Hz (pour plus de clarté et de présence).
-   `afftdn=...`: **Anti-bruit**. Réduit le bruit de fond constant (souffle de l'ordinateur, climatisation).
-   `deesser=...`: **De-esseur**. Cible et atténue les sifflements désagréables produits par les sons "S".
-   `acompressor=...`: **Compresseur**. Réduit l'écart entre les parties les plus fortes et les plus faibles de votre voix, pour un volume plus homogène.
-   `loudnorm`: **Normalisation du Volume**. Ajuste le volume global pour qu'il soit à un niveau standard pour le web, sans jamais saturer.

### Configuration des Filtres Audio Professionnels (dans les outils audio)

`audio_processor.py` et `audio_enhancer.py` utilisent une méthode plus avancée en deux passes, configurée via `PRO_AUDIO_FILTERS`.

-   `loudness_targets`: C'est le cœur du système. Il vise des standards de l'industrie.
    -   `integrated_lufs: -16.0`: **Volume Perçu Cible**. Le LUFS (Loudness Units Full Scale) est la mesure standard du volume perçu. -16 LUFS est un excellent niveau pour YouTube, Spotify et les podcasts. C'est plus fort et plus présent que la normalisation classique.
    -   `true_peak: -1.5`: **Pic Maximal Autorisé**. Garantit qu'aucun son, même le plus bref, ne dépassera -1.5 dB. Cela empêche la distorsion (clipping) sur tous les systèmes d'écoute.
    -   `lufs_range: 7.0`: **Plage Dynamique**. Contrôle la différence de volume entre les sons faibles et forts. Une valeur autour de 7 est naturelle pour la voix.

### Configuration du Mixage Musical (Ducking)

Présent dans tous les scripts.

-   `threshold`: Sensibilité de la détection de la voix. Une valeur plus faible rend la détection plus sensible.
-   `ratio`: Facteur de réduction du volume de la musique. Un ratio de `5` signifie que le volume de la musique sera divisé par 5 lorsque la voix est détectée.

### Configuration de l'Encodage Vidéo

Dans `main.py`, la section `FFMPEG_PRESETS` contrôle la qualité de la vidéo de sortie.

-   `cfr_preset`: Vitesse d'encodage. `ultrafast` est le plus rapide (fichier plus gros, qualité plus faible), `medium` est un bon équilibre, `slow` est très lent (fichier plus petit, meilleure qualité).
-   `cfr_crf`: **Facteur de Qualité Constante (CRF)**. C'est le paramètre le plus important pour la qualité. `0` est sans perte, `23` est le défaut, `18` est une excellente qualité visuelle (fichier plus gros), `28` est une qualité plus faible. Une plage de 18 à 24 est généralement recommandée.

---

## Licence

Ce projet est sous licence MIT. Vous êtes libre de l'utiliser, de le modifier et de le distribuer.