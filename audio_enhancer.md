# Documentation : audio_enhancer.py

`audio_enhancer.py` est un script spécialisé dans l'amélioration de la qualité d'une piste audio unique. Il prend en entrée un fichier audio ou vidéo, en extrait la piste son, la nettoie et l'optimise pour obtenir un rendu professionnel, conforme aux standards de l'industrie (podcasts, YouTube, streaming).

Ce script est une version légèrement simplifiée de `audio_processor.py`, se concentrant sur un seul fichier à la fois.

## Cas d'Usage Principaux

-   **Amélioration d'une Interview** : Améliorer la qualité sonore d'un enregistrement d'interview unique.
-   **Mastering d'un Fichier Vocal** : Prendre un enregistrement vocal brut et le transformer en une version masterisée prête à l'emploi.
-   **Extraction et Amélioration Rapide** : Extraire rapidement le son d'une vidéo et l'améliorer sans les options de traitement par lot.

## Fonctionnalités

1.  **Extraction Audio** : Si un fichier vidéo est fourni, sa piste audio est automatiquement extraite.
2.  **Suppression des Silences** : Détecte et supprime les pauses pour rendre l'audio plus concis.
3.  **Amélioration Audio Professionnelle (2-Passes)** :
    -   **Passe 1 (Analyse)** : Analyse l'audio pour mesurer ses caractéristiques précises (LUFS, True Peak, LRA).
    -   **Passe 2 (Application)** : Applique une chaîne de filtres sur mesure (EQ, compresseur, etc.) et une normalisation de volume pour atteindre les cibles des plateformes de streaming (-16 LUFS). Le résultat est un son puissant, clair et sans saturation.
4.  **Mixage Musical (Ducking)** : Permet d'ajouter une musique de fond qui s'atténue automatiquement en présence de voix.

## Utilisation

Assurez-vous que les prérequis (`Python`, `FFmpeg` et les dépendances dans `requirements.txt`) sont installés.

### Exemple 1 : Améliorer l'audio d'une vidéo

```bash
python audio_enhancer.py ma_conference.mp4 -o voix_amelioree.mp3
```

Cette commande va extraire l'audio de `ma_conference.mp4`, enlever les silences, appliquer l'amélioration professionnelle et sauvegarder le résultat dans `voix_amelioree.mp3`.

### Exemple 2 : Traiter un fichier audio et ajouter une musique

```bash
python audio_enhancer.py mon_podcast_brut.wav -o podcast_final.mp3 -m jingle.mp3
```

Ici, le script améliore `mon_podcast_brut.wav` et y ajoute `jingle.mp3` en fond sonore.

### Arguments de la ligne de commande

-   `input_file` : Chemin vers le fichier audio ou vidéo à traiter.
-   `-o, --output-file` : Chemin du fichier de sortie `.mp3`.
-   `-m, --music` : (Optionnel) Chemin vers la musique de fond.
-   `--music-volume` : (Optionnel) Volume de la musique en dB (ex: `-25.0`).
-   `--no-audio-filters` : (Optionnel) Désactive la chaîne d'amélioration audio.
