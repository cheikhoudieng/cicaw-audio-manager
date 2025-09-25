#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SCRIPT UNIVERSEL D'OPTIMISATION AUDIO (QUALITÉ PROFESSIONNELLE) V3.0

Version avancée utilisant une normalisation en deux passes pour un résultat
techniquement parfait, idéal pour les standards de YouTube, podcasts et streaming.

1.  Analyse l'audio pour mesurer ses caractéristiques (volume, pics).
2.  Applique des filtres de nettoyage et de dynamique sur mesure.
3.  Garantit un volume final constant et puissant sans sur-compression.
"""

import argparse
import logging
import subprocess
import shlex
import json
from pathlib import Path

# --- Dépendances tierces ---
try:
    from pydub import AudioSegment
    from pydub.silence import split_on_silence
except ImportError:
    print("ERREUR: Des bibliothèques requises sont manquantes.")
    print("Veuillez installer les dépendances avec la commande : pip install pydub")
    exit(1)

# ==============================================================================
# 1. CONFIGURATION CENTRALE
# ==============================================================================
CONFIG = {
    # ... (les autres configurations restent les mêmes)
    "SILENCE_THRESH_DB": -40,
    "MIN_SILENCE_LEN_MS": 500,
    "CHUNK_KEEP_SILENCE_MS": 250,
    "OUTPUT_DIR": "audio_enhanced",
    "DUCKING": {"threshold": 0.05, "ratio": 5},

    # --- NOUVEAU : Chaîne de filtres séparée pour le workflow pro ---
    "PRO_AUDIO_FILTERS": {
        "enabled": True,
        # Filtres de "nettoyage" appliqués avant l'analyse de volume
        "cleanup_filters": "highpass=f=90,deesser=i=0.5:m=0.5:f=0.5,afftdn=nr=12:nf=-25",
        
        # Filtres de "dynamique" appliqués après l'analyse
        "dynamics_filters": "equalizer=f=300:width_type=q:w=2:g=-3,equalizer=f=3000:width_type=q:w=2:g=3,acompressor=threshold=0.08:ratio=9:attack=20:release=250",
        
        # Cibles de normalisation pour YouTube/Streaming
        "loudness_targets": {
            "integrated_lufs": -16.0,
            "true_peak": -1.5,
            "lufs_range": 7.0
        },
        "audio_codec": "libmp3lame",
        "audio_bitrate": "192k"
    }
}

# ==============================================================================
# 2. CONFIGURATION DU LOGGING (inchangée)
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# ==============================================================================
# 3. FONCTIONS
# ==============================================================================

def run_command(command: list, capture=False):
    """Exécute une commande shell. Capture la sortie si demandé."""
    try:
        logging.debug(f"Exécution : {shlex.join(command)}")
        if capture:
            return subprocess.run(
                command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
        else:
            result = subprocess.run(
                command, check=True, capture_output=True, text=True, encoding='utf-8', errors='ignore'
            )
            return result
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur lors de l'exécution de la commande : {shlex.join(command)}")
        logging.error(f"Code de retour : {e.returncode}\nSortie FFmpeg (stderr):\n{e.stderr}")
        return None
    except FileNotFoundError:
        logging.error(f"Commande introuvable : {command[0]}. Assurez-vous que ffmpeg est installé.")
        return None

def enhance_audio_professional(input_wav: Path, output_path: Path, config: dict) -> bool:
    """Améliore l'audio en utilisant une analyse loudnorm en deux passes."""
    af_config = config["PRO_AUDIO_FILTERS"]
    targets = af_config["loudness_targets"]
    
    # --- PREMIÈRE PASSE : ANALYSE ---
    logging.info("  -> Passe 1/2 : Analyse de l'audio...")
    analysis_filters = f"{af_config['cleanup_filters']},{af_config['dynamics_filters']}"
    cmd_pass1 = [
        "ffmpeg", "-y", "-i", str(input_wav),
        "-af", f"{analysis_filters},loudnorm=I={targets['integrated_lufs']}:TP={targets['true_peak']}:LRA={targets['lufs_range']}:print_format=json",
        "-f", "null", "-"
    ]
    
    result_pass1 = run_command(cmd_pass1, capture=True)
    if not result_pass1:
        logging.error("L'analyse audio (passe 1) a échoué.")
        return False

    # --- CORRECTION DE LA LECTURE JSON ---
    try:
        stderr_text = result_pass1.stderr
        # On cherche le début et la fin exacts du bloc JSON
        json_start_index = stderr_text.find('{')
        json_end_index = stderr_text.rfind('}')
        
        if json_start_index == -1 or json_end_index == -1:
            raise ValueError("Bloc JSON introuvable dans la sortie de FFmpeg.")

        # On isole précisément le JSON, en ignorant tout le reste
        json_output = stderr_text[json_start_index : json_end_index + 1]
        loudness_data = json.loads(json_output)
        
        measured_i = float(loudness_data["input_i"])
        measured_tp = float(loudness_data["input_tp"])
        measured_lra = float(loudness_data["input_lra"])
        measured_thresh = float(loudness_data["input_thresh"])
        target_offset = float(loudness_data["target_offset"])
        
        logging.info(f"  -> Analyse terminée : Volume perçu={measured_i:.1f} LUFS, Pic max={measured_tp:.1f} dB")
    except (ValueError, json.JSONDecodeError) as e:
        logging.error(f"Impossible de lire les résultats de l'analyse loudnorm : {e}")
        logging.debug(f"Sortie complète de FFmpeg (stderr) pour le débogage:\n{stderr_text}")
        return False
    # --- FIN DE LA CORRECTION ---

    # --- DEUXIÈME PASSE : APPLICATION (inchangée) ---
    logging.info("  -> Passe 2/2 : Application des corrections sur mesure...")
    final_loudnorm = f"loudnorm=I={targets['integrated_lufs']}:TP={targets['true_peak']}:LRA={targets['lufs_range']}:measured_I={measured_i}:measured_LRA={measured_lra}:measured_tp={measured_tp}:measured_thresh={measured_thresh}:offset={target_offset}"
    final_filters = f"{analysis_filters},{final_loudnorm}"
    
    cmd_pass2 = [
        "ffmpeg", "-y", "-i", str(input_wav),
        "-af", final_filters,
        "-c:a", af_config["audio_codec"],
        "-b:a", af_config["audio_bitrate"],
        str(output_path)
    ]
    
    return run_command(cmd_pass2) is not None

def process_audio(
    input_file: str,
    output_file: str,
    config: dict,
    music_file: str | None,
    music_volume: float
):
    """Orchestre le processus complet de traitement de l'audio."""
    input_path = Path(input_file)
    final_output_path = Path(output_file)
    
    # ... (le début est identique)
    video_extensions = ['.mp4', '.mov', '.mkv', '.avi', '.webm', '.flv']
    if input_path.suffix.lower() in video_extensions:
        logging.info(f"Fichier vidéo détecté ('{input_path.name}'). La piste audio sera extraite et traitée.")
    else:
        logging.info(f"Fichier audio détecté ('{input_path.name}').")

    num_steps = 3 if music_file else 2
    
    logging.info(f"1/{num_steps} - Chargement de l'audio et suppression des silences...")
    try:
        audio = AudioSegment.from_file(input_path)
        chunks = split_on_silence(
            audio,
            min_silence_len=config["MIN_SILENCE_LEN_MS"],
            silence_thresh=config["SILENCE_THRESH_DB"],
            keep_silence=config["CHUNK_KEEP_SILENCE_MS"]
        )
        if not chunks:
            logging.warning("Aucun son détecté.")
            return

        logging.info(f"{len(chunks)} segments sonores conservés.")
        audio_without_silence = sum(chunks)
    except Exception as e:
        logging.error(f"Erreur lors du traitement Pydub : {e}")
        return

    logging.info(f"2/{num_steps} - Amélioration de la voix (méthode professionnelle)...")
    temp_wav_path = final_output_path.with_suffix('.temp.wav')
    audio_without_silence.export(temp_wav_path, format="wav")

    enhanced_audio_path = (final_output_path.with_suffix('.enhanced_temp.mp3') if music_file else final_output_path)
    
    if not enhance_audio_professional(temp_wav_path, enhanced_audio_path, config):
        logging.error("L'étape d'amélioration de la voix a échoué.")
        temp_wav_path.unlink()
        return
        
    temp_wav_path.unlink()

    if not music_file:
        logging.info(f"✅ Succès ! Fichier audio traité sauvegardé dans : '{final_output_path.resolve()}'")
        return

    # ... (le mixage musical reste identique)
    logging.info(f"3/{num_steps} - Ajout de la musique de fond avec effet ducking...")
    af_config = config["PRO_AUDIO_FILTERS"]
    duck_config = config["DUCKING"]
    filter_complex = (f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[voice_norm];"
                      f"[1:a]volume={music_volume}dB,aformat=sample_rates=48000:channel_layouts=stereo[bg_norm];"
                      f"[voice_norm]asplit[voice_main][voice_side];"
                      f"[voice_side]volume=15dB[voice_side_amp];"
                      f"[bg_norm][voice_side_amp]sidechaincompress=threshold={duck_config['threshold']}:ratio={duck_config['ratio']}[ducked_bg];"
                      f"[voice_main][ducked_bg]amix=inputs=2[a_out]")
    cmd_mix = ["ffmpeg", "-y", "-i", str(enhanced_audio_path), "-stream_loop", "-1", "-i", str(music_file),
               "-filter_complex", filter_complex, "-map", "[a_out]", "-c:a", af_config["audio_codec"],
               "-b:a", af_config["audio_bitrate"], "-shortest", str(final_output_path)]

    if run_command(cmd_mix):
        logging.info(f"✅ Succès ! Fichier final avec musique sauvegardé dans : '{final_output_path.resolve()}'")
    else:
        logging.error("Le mixage musical a échoué.")
    enhanced_audio_path.unlink()


# ==============================================================================
# 4. POINT D'ENTRÉE DU SCRIPT (inchangé)
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Améliore un enregistrement audio en utilisant des techniques professionnelles.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_file", type=str, help="Fichier AUDIO ou VIDÉO à traiter.")
    parser.add_argument("-o", "--output-file", type=str, help="Fichier de sortie audio (.mp3).")
    parser.add_argument("--no-audio-filters", action="store_true", help="Désactive les filtres d'amélioration.")
    music_group = parser.add_argument_group("Options pour la musique de fond")
    music_group.add_argument("-m", "--music", type=str, help="Fichier de musique de fond.")
    music_group.add_argument("--music-volume", type=float, default=-25.0, help="Volume de la musique en dB. Défaut: -25.0.")

    args = parser.parse_args()
    input_path = Path(args.input_file)
    if not input_path.is_file():
        logging.error(f"Fichier d'entrée introuvable : '{input_path}'"); exit(1)
    if args.music and not Path(args.music).is_file():
        logging.error(f"Fichier de musique introuvable : '{args.music}'"); exit(1)

    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(CONFIG["OUTPUT_DIR"]); output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{input_path.stem}_enhanced_pro.mp3"

    if output_path.resolve() == input_path.resolve():
        logging.error("Le fichier de sortie ne peut être identique au fichier d'entrée."); exit(1)

    current_config = CONFIG.copy()
    if args.no_audio_filters:
        current_config["PRO_AUDIO_FILTERS"]["enabled"] = False
        logging.info("Filtres audio désactivés.")
    
    process_audio(
        input_file=str(input_path), output_file=str(output_path), config=current_config,
        music_file=args.music, music_volume=args.music_volume
    )

# Simplement traiter la voix de la vidéo
# python audio_enhancer.py Screen_Recording_20250923_125213_Chrome.mp4 -o voix_de_la_video.mp3

# Traiter la voix de la vidéo et ajouter de la musique
# python audio_enhancer.py Screen_Recording_20250923_125213_Chrome.mp4 -o voix_de_la_video_musique.mp3 -m musique_feelgood.mp3