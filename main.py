#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT DE DÉCOUPE VIDÉO HAUTE PERFORMANCE V3

Ce script automatise le processus de montage vidéo en :
1. Supprimant les silences d'une vidéo (jump cuts automatiques).
2. Améliorant la qualité de la voix avec une chaîne de filtres audio professionnels.
3. Ajoutant une musique de fond avec un effet de "ducking" (le volume de la
   musique baisse automatiquement lorsque quelqu'un parle).

CARACTÉRISTIQUES CLÉS :
- Haute Performance : Utilise une stratégie de "pré-encodage" pour gérer les
  vidéos à cadence variable (VFR) de manière rapide et fiable, évitant la
  désynchronisation audio/vidéo sans ré-encoder chaque petit segment.
- Qualité Audio Pro : Applique des filtres (EQ, compresseur, anti-bruit, de-esser)
  pour une voix claire et professionnelle.
- Extensible : La configuration centrale (CONFIG) permet d'ajuster facilement
  tous les paramètres sans modifier le code source.
- Robuste : Gestion des erreurs à chaque étape et utilisation de répertoires
  temporaires pour un fonctionnement propre.

USAGE (RECOMMANDÉ) :
Pour une vidéo avec une cadence d'images variable (ex: enregistrement d'écran, smartphone) :
$ python this_script.py "ma_video.mp4" -o "video_finale.mp4" -m "musique.mp3" --pre-encode-cfr
"""

import os
import argparse
import logging
import shutil
import tempfile
import subprocess
from pathlib import Path
import shlex

# --- Dépendances tierces ---
try:
    from pydub import AudioSegment
    from pydub.silence import detect_nonsilent
    from tqdm import tqdm
except ImportError:
    print("ERREUR: Des bibliothèques requises sont manquantes.")
    print("Veuillez installer les dépendances avec la commande : pip install pydub tqdm")
    exit(1)

# ==============================================================================
# 1. CONFIGURATION CENTRALE
# ==============================================================================
CONFIG = {
    # Paramètres de détection de silence
    "SILENCE_THRESH_DB": -38,   # Seuil de volume en dB en dessous duquel le son est considéré comme silence.
    "MIN_SILENCE_LEN_MS": 450,  # Durée minimale en ms pour qu'un silence soit détecté.
    "CHUNK_PADDING_MS": 200,    # Marge de sécurité en ms ajoutée au début et à la fin de chaque segment sonore.

    # Répertoire de sortie par défaut
    "OUTPUT_DIR": "videos_enhanced",

    # Chaîne de filtres audio pour une VOIX PRO
    "AUDIO_FILTERS": {
        "enabled": True,
        # 1. Nettoyage des basses fréquences (inchangé)
        "highpass": "highpass=f=100",

        # 2. Clarté et présence (inchangé)
        "equalizer": "equalizer=f=300:width_type=q:w=2:g=-3,equalizer=f=3000:width_type=q:w=2:g=3",

        # 3. Suppression du bruit de fond (inchangé)
        "denoise": "afftdn=nr=12:nf=-25",
        
        # 4. De-esser pour contrôler les sifflements (inchangé)
        "deesser": "deesser=i=0.5:m=0.5:f=0.5",

        # 5. NOUVEAU : Compresseur PLUS FORT pour un volume perçu plus élevé
        # Il s'activera plus tôt (threshold) et compressera plus fort (ratio)
        # pour que les parties faibles de votre voix soient bien audibles.
        "compressor": "acompressor=threshold=0.08:ratio=9:attack=20:release=250",

        # 6. NOUVEAU : Normalisation du volume optimisée pour le web/mobile (BEAUCOUP PLUS FORT)
        # i=-16 : Vise un volume intégré de -16 LUFS (standard pour YouTube/Spotify).
        # tp=-1.5 : Empêche la saturation (clipping) en gardant le pic maximal à -1.5 dB.
        # lra=7 : Garde une plage de volume naturelle mais contrôlée.
        "loudnorm": "loudnorm=i=-16:tp=-1.5:lra=7",
        
        "audio_codec": "aac",
        "audio_bitrate": "256k"
    },
    
    # Mixage musical (Ducking)
    "DUCKING": {
        "threshold": 0.05,  # Sensibilité de la détection de la voix.
        "ratio": 5          # Facteur de réduction du volume de la musique.
    },

    # Paramètres d'encodage FFmpeg
    "FFMPEG_PRESETS": {
        "cfr_preset": "veryfast", # Compromis vitesse/qualité pour le pré-encodage. 'ultrafast' est plus rapide, 'medium' est de meilleure qualité.
        "cfr_crf": "22"           # Facteur de qualité (Constant Rate Factor). 18-28 est une bonne plage. Plus bas = meilleure qualité, fichier plus gros.
    }
}

# ==============================================================================
# 2. CONFIGURATION DU LOGGING
# ==============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# ==============================================================================
# 3. FONCTIONS UTILITAIRES
# ==============================================================================

def check_ffmpeg():
    """Vérifie si FFmpeg est installé et accessible dans le PATH."""
    if shutil.which("ffmpeg") is None:
        logging.error("ERREUR CRITIQUE: FFmpeg n'est pas trouvé. Veuillez l'installer et vous assurer qu'il est dans le PATH de votre système.")
        return False
    return True

def run_command(command: list, cwd: str = None) -> bool:
    """Exécute une commande shell et retourne True en cas de succès."""
    try:
        # Utilisation de shlex.join pour un affichage sécurisé et lisible de la commande
        logging.debug(f"Exécution depuis '{cwd or os.getcwd()}' : {shlex.join(command)}")
        subprocess.run(command, check=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'exécution de la commande : {shlex.join(command)}")
        logging.error(f"Code de retour : {e.returncode}")
        # Affiche la sortie d'erreur de ffmpeg pour un débogage facile
        logging.error(f"Sortie FFmpeg (stdout):\n{e.stdout.decode('utf-8', errors='ignore')}")
        logging.error(f"Sortie FFmpeg (stderr):\n{e.stderr.decode('utf-8', errors='ignore')}")
        return False
    except FileNotFoundError:
        logging.error(f"Commande introuvable : {command[0]}.")
        return False

# ==============================================================================
# 4. FONCTIONS DU PROCESSUS VIDÉO (ÉTAPES)
# ==============================================================================

def pre_encode_to_cfr(input_path: Path, temp_dir: Path, config: dict) -> Path | None:
    """
    Pré-encode la vidéo en Constant Frame Rate (CFR) pour éviter la désynchronisation.
    Cette version inclut des options de robustesse pour gérer les VFR très problématiques.
    """
    logging.info("Étape Préliminaire : Pré-encodage en CFR pour garantir la synchronisation...")
    cfr_video_path = temp_dir / f"stable_cfr_{input_path.name}"
    preset = config["FFMPEG_PRESETS"]
    
    # --- AJOUT DES OPTIONS DE ROBUSTESSE ---
    # -vsync cfr: Force la conformité à la cadence d'images constante.
    # -r 30: Définit une cadence de sortie standard de 30 images/seconde.
    #        C'est une valeur sûre pour les enregistrements d'écran.
    #        Vous pourriez utiliser 60 si la source est très fluide.
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-vsync", "cfr",
        "-r", "30",
        "-c:v", "libx264", 
        "-preset", preset["cfr_preset"], 
        "-crf", preset["cfr_crf"],
        "-c:a", "aac", "-b:a", "192k",
        str(cfr_video_path)
    ]
    
    if run_command(cmd):
        logging.info("Pré-encodage terminé. La suite du processus sera rapide et fiable.")
        return cfr_video_path
    else:
        logging.error("Le pré-encodage a échoué. Le script ne peut continuer en toute sécurité.")
        return None

def extract_audio(video_path: Path, temp_dir: Path) -> Path | None:
    """Extrait la piste audio d'une vidéo vers un fichier WAV temporaire."""
    logging.info("Étape 1 : Extraction de la piste audio pour analyse...")
    audio_path = temp_dir / "audio.wav"
    cmd = ["ffmpeg", "-y", "-i", str(video_path), "-vn", "-acodec", "pcm_s16le", str(audio_path)]
    return audio_path if run_command(cmd) else None

def detect_speech_segments(audio_path: Path, config: dict) -> list[tuple[float, float]] | None:
    """Analyse un fichier audio et retourne les segments contenant de la parole."""
    logging.info("Étape 2 : Analyse de l'audio et détection des silences...")
    try:
        audio_segment = AudioSegment.from_wav(audio_path)
        non_silent_parts = detect_nonsilent(
            audio_segment,
            min_silence_len=config["MIN_SILENCE_LEN_MS"],
            silence_thresh=config["SILENCE_THRESH_DB"]
        )
        if not non_silent_parts:
            logging.warning("Aucun son n'a été détecté dans le fichier audio.")
            return []

        padding = config["CHUNK_PADDING_MS"]
        processed_parts = [
            (max(0, s - padding) / 1000.0, min(len(audio_segment), e + padding) / 1000.0)
            for s, e in non_silent_parts
        ]
        logging.info(f"{len(processed_parts)} segments sonores à conserver.")
        return processed_parts
    except Exception as e:
        logging.error(f"Erreur lors de l'analyse audio avec Pydub : {e}")
        return None

def cut_video_segments(
    source_video: Path,
    segments: list[tuple[float, float]],
    temp_dir: Path,
    # L'argument force_reencode_clips n'est plus utile, car on va toujours ré-encoder.
    # On pourrait le supprimer, mais pour l'instant on l'ignore.
    force_reencode_clips: bool 
) -> Path | None:
    """
    Découpe la vidéo en clips en ré-encodant systématiquement.
    C'est crucial pour garantir que chaque clip, même sans mouvement d'image,
    possède une piste vidéo, résolvant les problèmes de concaténation.
    """
    logging.info("Étape 3 : Découpe et stabilisation des segments vidéo...")
    concat_list_path = temp_dir / "concat_list.txt"
    
    with open(concat_list_path, "w", encoding="utf-8") as f:
        for i, (start, end) in enumerate(tqdm(segments, desc="Découpe des segments")):
            clip_path = temp_dir / f"clip_{i:04d}{source_video.suffix}"
            
            # On ABANDONNE -c copy. On ré-encode toujours pour la robustesse.
            # -preset ultrafast : rend cette étape très rapide.
            # -c:a copy : l'audio n'a pas besoin d'être ré-encodé ici.
            cmd_cut = [
                "ffmpeg", "-y", 
                "-i", str(source_video), 
                "-ss", str(start), 
                "-to", str(end),
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "22",
                "-c:a", "copy",
                "-avoid_negative_ts", "make_zero", 
                str(clip_path)
            ]
            
            if not run_command(cmd_cut):
                logging.error(f"Échec de la découpe du segment {i}. Abandon.")
                return None
            
            f.write(f"file '{clip_path.name}'\n")
    
    return concat_list_path

def concatenate_and_enhance_voice(
    concat_list_path: Path,
    output_path: Path,
    config: dict
) -> bool:
    """
    Concatène les clips en utilisant le FILTRE concat (plus robuste) et applique
    les filtres audio pour la voix.
    """
    logging.info("Étape 4 : Concaténation des clips et amélioration de la voix (méthode robuste)...")
    
    # Lire la liste des fichiers à concaténer
    with open(concat_list_path, "r", encoding="utf-8") as f:
        clip_files = [line.strip().replace("file '", "").replace("'", "") for line in f.readlines()]

    # 1. Préparer les arguments d'entrée pour ffmpeg
    cmd = ["ffmpeg", "-y"]
    for clip in clip_files:
        cmd.extend(["-i", clip])

    # 2. Construire le filtre complexe pour concaténer
    # Exemple pour 3 clips : "[0:v][0:a][1:v][1:a][2:v][2:a]concat=n=3:v=1:a=1[v][a]"
    num_clips = len(clip_files)
    filter_inputs = "".join([f"[{i}:v][{i}:a]" for i in range(num_clips)])
    concat_filter = f"{filter_inputs}concat=n={num_clips}:v=1:a=1[v_out][a_concat]"

    # 3. Ajouter la chaîne de filtres audio APRÈS la concaténation
    af_config = config["AUDIO_FILTERS"]
    if af_config["enabled"]:
        audio_filter_chain = ",".join(filter(None, [
            af_config.get("highpass"), af_config.get("equalizer"),
            af_config.get("denoise"), af_config.get("deesser"),
            af_config.get("compressor"), af_config.get("loudnorm")
        ]))
        # On applique les filtres sur la sortie audio de la concaténation
        final_filter_complex = f"{concat_filter};[a_concat]{audio_filter_chain}[a_out]"
        audio_map_target = "[a_out]"
    else:
        # Si pas de filtre, on utilise directement la sortie audio de la concaténation
        final_filter_complex = f"{concat_filter}"
        audio_map_target = "[a_concat]"

    cmd.extend(["-filter_complex", final_filter_complex])
    
    # 4. Mapper les sorties du filtre vers les flux de sortie
    cmd.extend(["-map", "[v_out]", "-map", audio_map_target])
    
    # 5. Spécifier les codecs de sortie.
    # IMPORTANT : La vidéo doit être ré-encodée avec cette méthode.
    # On utilise les mêmes paramètres que le pré-encodage pour la cohérence.
    preset = config["FFMPEG_PRESETS"]
    cmd.extend([
        "-c:v", "libx264", 
        "-preset", preset["cfr_preset"], 
        "-crf", preset["cfr_crf"]
    ])
    
    if af_config["enabled"]:
        cmd.extend(["-c:a", af_config["audio_codec"], "-b:a", af_config["audio_bitrate"]])
    else:
        cmd.extend(["-c:a", "copy"])

    cmd.append(str(output_path))

    logging.info("La commande de traitement vocal (méthode filtre) suivante va être exécutée :")
    print("-" * 80)
    print(shlex.join(cmd))
    print("-" * 80)
    
    # IMPORTANT: La commande doit être exécutée depuis le répertoire des clips
    return run_command(cmd, cwd=str(concat_list_path.parent))

def add_background_music(
    video_path: Path,
    music_path: Path,
    output_path: Path,
    music_volume_db: float,
    config: dict
) -> bool:
    """Mixe la vidéo avec une musique de fond en utilisant le ducking."""
    logging.info("Étape 5 : Ajout de la musique de fond avec effet ducking...")
    
    duck_config = config["DUCKING"]
    af_config = config["AUDIO_FILTERS"]

    # Ce filtre complexe est robuste :
    # 1. [0:a] et [1:a] sont les pistes audio de la vidéo et de la musique.
    # 2. Elles sont normalisées (aformat) pour être compatibles.
    # 3. La voix [voice_norm] est dupliquée en [voice_main] (pour le mix final)
    #    et [voice_side] (pour le contrôle).
    # 4. [voice_side] est fortement amplifiée pour créer un signal de contrôle clair.
    # 5. sidechaincompress utilise le signal de contrôle pour baisser le volume de la musique.
    # 6. amix mélange la voix originale et la musique "duckée".
    filter_complex = (
        f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[voice_norm];"
        f"[1:a]volume={music_volume_db}dB,aformat=sample_rates=48000:channel_layouts=stereo[bg_norm];"
        f"[voice_norm]asplit[voice_main][voice_side];"
        f"[voice_side]volume=15dB[voice_side_amp];"
        f"[bg_norm][voice_side_amp]sidechaincompress=threshold={duck_config['threshold']}:ratio={duck_config['ratio']}[ducked_bg];"
        f"[voice_main][ducked_bg]amix=inputs=2[a_out]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(music_path),
        "-filter_complex", filter_complex,
        "-map", "0:v", "-map", "[a_out]",
        "-c:v", "copy",
        "-c:a", af_config["audio_codec"],
        "-b:a", af_config["audio_bitrate"],
        "-shortest",
        str(output_path)
    ]
    
    logging.info("La commande de mixage musical suivante va être exécutée :")
    print("-" * 80)
    print(shlex.join(cmd))
    print("-" * 80)
    
    return run_command(cmd)


# ==============================================================================
# 5. CHEF D'ORCHESTRE PRINCIPAL
# ==============================================================================

def process_video(
    input_file: str,
    output_file: str,
    config: dict,
    music_file: str | None,
    music_volume: float,
    pre_encode: bool,
    force_reencode_clips: bool
):
    """
    Orchestre le processus complet de traitement de la vidéo.
    """
    main_input_path = Path(input_file)
    final_output_path = Path(output_file)
    
    with tempfile.TemporaryDirectory(prefix="video_processing_") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        logging.info(f"Utilisation du répertoire temporaire : {temp_dir}")

        source_video_path = main_input_path
        if pre_encode:
            source_video_path = pre_encode_to_cfr(main_input_path, temp_dir, config)
            if not source_video_path: return

        temp_audio_path = extract_audio(source_video_path, temp_dir)
        if not temp_audio_path: return

        segments = detect_speech_segments(temp_audio_path, config)
        if segments is None: return
        if not segments:
            logging.warning("Aucun segment sonore trouvé. Copie du fichier original.")
            shutil.copy(main_input_path, final_output_path)
            return

        concat_list = cut_video_segments(source_video_path, segments, temp_dir, force_reencode_clips)
        if not concat_list: return

        # Le chemin de sortie pour l'étape de concaténation
        # Si de la musique doit être ajoutée, c'est un fichier intermédiaire. Sinon, c'est le fichier final.
        voice_enhanced_video_path = (
            temp_dir / f"enhanced_{main_input_path.name}"
            if music_file
            else final_output_path
        )
        
        if not concatenate_and_enhance_voice(concat_list, voice_enhanced_video_path, config):
            return

        if music_file:
            if add_background_music(voice_enhanced_video_path, Path(music_file), final_output_path, music_volume, config):
                logging.info(f"✅ Succès ! Vidéo finale avec musique sauvegardée dans : '{final_output_path.resolve()}'")
            else:
                logging.error("L'ajout de la musique de fond a échoué.")
        else:
            logging.info(f"✅ Succès ! Vidéo finale sauvegardée dans : '{final_output_path.resolve()}'")


# ==============================================================================
# 6. POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    if not check_ffmpeg():
        exit(1)

    parser = argparse.ArgumentParser(
        description="Coupe les silences, améliore l'audio et ajoute une musique de fond à une vidéo.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("input_file", type=str, help="Fichier vidéo à traiter.")
    parser.add_argument("-o", "--output-file", type=str, help="Chemin du fichier de sortie. Si non spécifié, généré automatiquement.")
    parser.add_argument("--no-audio-filters", action="store_true", help="Désactive tous les filtres d'amélioration de la voix.")
    
    music_group = parser.add_argument_group("Options pour la musique de fond")
    music_group.add_argument("-m", "--music", type=str, help="Fichier audio de musique de fond à ajouter avec ducking.")
    music_group.add_argument("--music-volume", type=float, default=-15.0, help="Volume de la musique de fond en dB (ex: -20). Défaut: -20.0.")

    sync_group = parser.add_argument_group("Options de synchronisation (pour corriger les décalages audio/vidéo)")
    sync_group.add_argument(
        "--pre-encode-cfr", action="store_true",
        help="[RECOMMANDÉ] Pré-encode la vidéo entière à une cadence constante (CFR) avant la découpe.\n"
             "C'est la meilleure solution pour éviter la désynchronisation audio/vidéo avec de bonnes performances."
    )
    sync_group.add_argument(
        "--force-cfr-per-clip", action="store_true", 
        help="[LENT] Force le ré-encodage de chaque segment individuellement. Robuste mais très lent.\n"
             "N'utilisez cette option que si --pre-encode-cfr ne fonctionne pas pour une raison étrange."
    )

    args = parser.parse_args()

    # --- Validation des entrées ---
    input_path = Path(args.input_file)
    if not input_path.is_file():
        logging.error(f"Fichier d'entrée introuvable : '{input_path}'")
        exit(1)

    if args.music:
        music_path = Path(args.music)
        if not music_path.is_file():
            logging.error(f"Fichier de musique introuvable : '{music_path}'")
            exit(1)

    # --- Détermination du chemin de sortie ---
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(CONFIG["OUTPUT_DIR"])
        output_dir.mkdir(parents=True, exist_ok=True)
        output_filename = f"{input_path.stem}_enhanced{input_path.suffix}"
        output_path = output_dir / output_filename

    if output_path.resolve() == input_path.resolve():
        logging.error("Le fichier de sortie ne peut pas être identique au fichier d'entrée.")
        exit(1)

    # --- Application de la configuration dynamique ---
    current_config = CONFIG.copy()
    if args.no_audio_filters:
        current_config["AUDIO_FILTERS"]["enabled"] = False
        logging.info("Filtres audio sur la voix désactivés via l'argument --no-audio-filters.")
    
    # --- Lancement du traitement ---
    process_video(
        input_file=str(input_path),
        output_file=str(output_path),
        config=current_config,
        music_file=args.music,
        music_volume=args.music_volume,
        pre_encode=args.pre_encode_cfr,
        force_reencode_clips=args.force_cfr_per_clip
    )


# python main.py Screen_Recording_20250923_125213_Chrome.mp4 -o out_synced.mp4 -m music_feelgood.mp3 --pre-encode-cfr




# !python "/content/drive/MyDrive/ProjetVideo/main.py" \
#   "/content/drive/MyDrive/ProjetVideo/Screen_Recording_20250923_125213_Chrome.mp4" \
#   -o "/content/drive/MyDrive/ProjetVideo/out_synced_colab.mp4" \
#   -m "/content/drive/MyDrive/ProjetVideo/music_feelgood.mp3" \
#   --pre-encode-cfr


# python main.py Screen_Recording_20250923_125213_Chrome.mp4 -o out_synced_LOUD.mp4 -m music_feelgood.mp3 --pre-encode-cfr