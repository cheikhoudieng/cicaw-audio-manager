# Documentation : audio_processor.py

`audio_processor.py` est un script de post-production audio complet, conçu pour traiter et améliorer des enregistrements vocaux de manière professionnelle. Il peut fonctionner sur un fichier unique (audio ou vidéo) ou, de manière plus puissante, sur un dossier entier de segments audio pour les assembler en un seul fichier propre et masterisé.

C'est l'outil idéal pour les voix off, les podcasts ou pour extraire et améliorer la bande-son d'une vidéo.

## Cas d'Usage Principaux

-   **Assemblage de Voix Off** : Vous enregistrez votre voix en plusieurs prises (fichiers WAV, MP3...). Ce script les assemble dans le bon ordre, nettoie les silences entre les phrases et produit un fichier unique et cohérent.
-   **Nettoyage de Podcast** : Traite un enregistrement de podcast pour enlever les longues pauses et homogénéiser le volume.
-   **Extraction et Amélioration Audio de Vidéo** : Extrait la piste son d'une vidéo, la nettoie et l'améliore pour une utilisation séparée.

## Fonctionnalités

1.  **Traitement par lot (dossier)** : Combine tous les fichiers audio d'un dossier (par ordre alphabétique) en une seule piste.
2.  **Suppression des Silences** : Détecte et supprime intelligemment les pauses et hésitations pour un rendu plus dynamique.
3.  **Amélioration Audio Professionnelle (2-Passes)** :
    -   **Passe 1 (Analyse)** : Le script analyse l'audio pour mesurer son volume perçu (LUFS), sa plage dynamique (LRA) et ses pics (True Peak).
    -   **Passe 2 (Application)** : En se basant sur l'analyse, il applique une chaîne de filtres (EQ, compresseur, de-esser, anti-bruit) et une normalisation précise pour atteindre les standards des plateformes de streaming (-16 LUFS), garantissant un son fort et clair sans distorsion.
4.  **Mixage Musical (Ducking)** : Ajoute une musique de fond dont le volume baisse automatiquement lorsque la voix est présente.

## Utilisation

Assurez-vous que les prérequis (`Python`, `FFmpeg` et les dépendances dans `requirements.txt`) sont installés.

### Exemple 1 : Traiter un dossier de voix off (Recommandé)

Imaginez un dossier `enregistrements/` contenant `01_intro.wav`, `02_partie1.wav`, `03_conclusion.wav`.

```bash
python audio_processor.py ./enregistrements/ -o voix_off_finale.mp3
```

Le script va coller les 3 fichiers, supprimer les silences et produire `voix_off_finale.mp3` avec une qualité professionnelle.

### Exemple 2 : Traiter un fichier unique et ajouter une musique

```bash
python audio_processor.py ma_video_brute.mp4 -o audio_final.mp3 -m musique_d_ambiance.mp3
```

Ce commando va extraire l'audio de `ma_video_brute.mp4`, le nettoyer, l'améliorer, et y mixer `musique_d_ambiance.mp3`.

### Arguments de la ligne de commande

-   `input_path` : Chemin vers le fichier ou le dossier à traiter.
-   `-o, --output-file` : Chemin du fichier de sortie `.mp3`.
-   `-m, --music` : (Optionnel) Chemin vers la musique de fond.
-   `--music-volume` : (Optionnel) Volume de la musique en dB (ex: `-25.0`).
-   `--no-audio-filters` : (Optionnel) Désactive toute la chaîne d'amélioration audio.
