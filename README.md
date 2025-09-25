# Video Cut - Outil d'Automatisation de Montage Vidéo

**Video Cut** est un script Python en ligne de commande conçu pour automatiser les tâches de montage vidéo répétitives. Il permet de transformer rapidement une vidéo brute en un contenu dynamique et professionnel, prêt à être publié.

Cet outil est idéal pour les créateurs de contenu, les formateurs, les youtubeurs ou toute personne souhaitant accélérer son flux de production vidéo.

## Fonctionnalités Principales

- **Jump Cuts Automatiques** : Détecte et supprime automatiquement les silences dans une vidéo pour la rendre plus rythmée.
- **Amélioration Vocale Professionnelle** : Applique une chaîne de filtres audio (Égaliseur, Compresseur, De-esser, Anti-bruit, etc.) pour obtenir une voix claire, présente et normalisée aux standards du web (YouTube, Spotify).
- **Musique de Fond Intelligente** : Ajoute une musique de fond avec un effet de *sidechain compression* (ducking), qui baisse automatiquement le volume de la musique lorsque la personne parle.
- **Haute Performance et Fiabilité** : Intègre une stratégie de pré-encodage pour gérer les vidéos à cadence d'images variable (VFR), un problème courant (enregistrements d'écran, smartphones) qui cause des désynchronisations audio/vidéo.
- **Hautement Configurable** : Tous les paramètres (seuils de silence, filtres audio, qualité d'encodage) sont centralisés et facilement modifiables.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants installés sur votre système :

1.  **Python 3.8+**
2.  **FFmpeg** : C'est la dépendance la plus importante. Le script l'utilise pour toutes les manipulations vidéo et audio.
    -   Pour l'installer sur **Ubuntu/Debian** : `sudo apt update && sudo apt install ffmpeg`
    -   Pour l'installer sur **macOS** (avec [Homebrew](https://brew.sh/)) : `brew install ffmpeg`
    -   Pour l'installer sur **Windows** : Téléchargez une version depuis le [site officiel de FFmpeg](https://ffmpeg.org/download.html) et ajoutez le dossier `bin` à votre `PATH` système.

## Installation

1.  Clonez ce dépôt sur votre machine locale :
    ```bash
    git clone https://github.com/VOTRE_NOM_UTILISATEUR/video-cut.git
    cd video-cut
    ```

2.  Il est fortement recommandé de créer un environnement virtuel Python pour isoler les dépendances du projet :
    ```bash
    python3 -m venv venv
    ```

3.  Activez l'environnement virtuel :
    -   Sur **Linux/macOS** :
        ```bash
        source venv/bin/activate
        ```
    -   Sur **Windows** (PowerShell) :
        ```powershell
        .\venv\Scripts\Activate.ps1
        ```

4.  Installez les bibliothèques Python requises :
    ```bash
    pip install -r requirements.txt
    ```

## Utilisation

L'utilisation se fait via la ligne de commande. Voici les cas d'usage les plus courants.

### Cas 1 : Couper les silences et améliorer la voix

C'est l'usage de base. Le script va traiter la vidéo, supprimer les moments de silence et appliquer les filtres sur la voix.

```bash
python main.py "chemin/vers/ma_video.mp4" -o "chemin/vers/video_editee.mp4"
```

> **Note** : Si votre vidéo provient d'un enregistrement d'écran ou d'un smartphone, il est très probable qu'elle ait une cadence d'images variable (VFR). Utilisez l'option `--pre-encode-cfr` pour éviter les problèmes de synchronisation.

### Cas 2 : Utilisation recommandée (avec pré-encodage)

Pour une fiabilité maximale, surtout avec des enregistrements d'écran (OBS, etc.) ou des vidéos de smartphone.

```bash
python main.py "ma_video_vfr.mp4" -o "video_finale.mp4" --pre-encode-cfr
```

### Cas 3 : Ajouter une musique de fond

Pour ajouter une musique qui se baissera automatiquement lorsque vous parlez.

```bash
python main.py "ma_video.mp4" -o "video_avec_musique.mp4" -m "chemin/vers/musique.mp3" --pre-encode-cfr
```

### Options disponibles

-   `input_file` : (Obligatoire) Le chemin vers la vidéo à traiter.
-   `-o, --output-file` : (Optionnel) Le chemin du fichier de sortie. Si non fourni, une sortie est générée dans le dossier `videos_enhanced`.
-   `-m, --music` : (Optionnel) Le chemin vers un fichier audio à utiliser comme musique de fond.
-   `--music-volume` : (Optionnel) Règle le volume de la musique de fond en dB (défaut : -15.0).
-   `--pre-encode-cfr` : **[Recommandé]** Pré-encode la vidéo à une cadence d'images constante pour éviter les désynchronisations.
-   `--no-audio-filters` : Désactive tous les filtres d'amélioration de la voix.

## Structure du Projet

```
.
├── main.py                 # Script principal, orchestre tout le processus.
├── audio_processor.py      # (À venir) Logique de traitement audio spécialisée.
├── audio_enhancer.py       # (À venir) Logique d'amélioration audio.
├── requirements.txt        # Liste des dépendances Python.
└── README.md               # Ce fichier.
```

## Comment ça marche ?

Le script suit un processus en plusieurs étapes pour garantir la qualité et la robustesse du traitement :

1.  **(Optionnel) Pré-encodage** : La vidéo est d'abord convertie en une version à cadence d'images constante (CFR) pour fiabiliser la suite.
2.  **Extraction Audio** : La piste audio est extraite dans un format non compressé (WAV).
3.  **Détection des Silences** : L'audio est analysée pour identifier tous les segments où le volume est en dessous d'un certain seuil.
4.  **Découpage et Concaténation** : La vidéo est découpée en gardant uniquement les segments "parlés", puis ces segments sont ré-assemblés. Durant cette étape, la voix est traitée avec la chaîne de filtres audio.
5.  **(Optionnel) Mixage Musical** : Si une musique est fournie, elle est mixée avec la piste vocale améliorée en utilisant l'effet de *ducking*.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` for plus de détails.
