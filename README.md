# Suite d'Outils de Post-Production Vidéo et Audio

Ce projet est une collection de scripts Python puissants conçus pour automatiser et simplifier la post-production de contenus vidéo et audio. Que vous souhaitiez dynamiser une vidéo en coupant les silences ou masteriser une voix off pour un podcast, cette suite fournit l'outil adapté.

## Les Outils

Le projet se compose de trois scripts principaux, chacun avec un rôle spécifique :

### 1. `main.py` - L'Éditeur Vidéo Automatique

C'est l'outil central pour le **traitement vidéo**. Il prend un fichier vidéo en entrée et automatise le montage pour le rendre plus dynamique.

-   **Fonction** : Coupe les silences d'une **vidéo**, améliore la piste audio de cette vidéo, et peut y ajouter une musique de fond.
-   **Idéal pour** : Les créateurs de contenu vidéo (tutoriels, vlogs, cours en ligne) qui veulent accélérer leur montage.
-   **Usage** : `python main.py ma_video.mp4 -o video_finale.mp4 --pre-encode-cfr`

### 2. `audio_processor.py` - Le Studio de Post-Production Audio

C'est l'outil le plus complet pour le **traitement audio par lot**. Il est conçu pour gérer des projets de voix off complexes à partir de plusieurs fichiers.

-   **Fonction** : Assemble plusieurs fichiers audio d'un **dossier**, supprime les silences, et applique une amélioration vocale de qualité professionnelle (normalisation LUFS).
-   **Idéal pour** : Les podcasteurs, les narrateurs de livres audio, ou pour toute voix off enregistrée en plusieurs segments.
-   **Usage** : `python audio_processor.py ./mon_dossier_voix/ -o voix_off_complete.mp3`
-   **Documentation détaillée** : [Lisez le README de `audio_processor.py`](./audio_processor.md)

### 3. `audio_enhancer.py` - L'Améliorateur Audio Rapide

Un script spécialisé pour traiter et améliorer **un seul fichier audio** à la fois.

-   **Fonction** : Extrait l'audio d'un fichier (vidéo ou audio), supprime les silences et applique la même amélioration vocale professionnelle que `audio_processor.py`.
-   **Idéal pour** : Masteriser rapidement un enregistrement unique, comme une interview ou un mémo vocal.
-   **Usage** : `python audio_enhancer.py interview.wav -o interview_masterisee.mp3`
-   **Documentation détaillée** : [Lisez le README de `audio_enhancer.py`](./audio_enhancer.md)

## Prérequis Communs

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre système :

1.  **Python 3.8+**
2.  **FFmpeg** : Dépendance cruciale pour toutes les manipulations média.
    -   **Ubuntu/Debian** : `sudo apt update && sudo apt install ffmpeg`
    -   **macOS (Homebrew)** : `brew install ffmpeg`
    -   **Windows** : Téléchargez-le depuis le [site officiel](https://ffmpeg.org/download.html) et ajoutez le dossier `bin` à votre `PATH` système.

## Installation

La procédure est la même pour tous les outils de la suite.

1.  Clonez ce dépôt :
    ```bash
    git clone https://github.com/VOTRE_NOM_UTILISATEUR/video-cut.git
    cd video-cut
    ```

2.  Créez et activez un environnement virtuel :
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # Sur Linux/macOS
    # .\venv\Scripts\Activate.ps1  # Sur Windows PowerShell
    ```

3.  Installez les dépendances Python :
    ```bash
    pip install -r requirements.txt
    ```

## Licence

Ce projet est sous licence MIT. N'hésitez pas à l'utiliser et à le modifier selon vos besoins.
