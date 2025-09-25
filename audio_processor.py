#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PROCESSEUR AUDIO UNIVERSEL (FICHIER UNIQUE OU DOSSIER) V4.0

Ce script est un studio de post-production audio complet.
Il prend un fichier audio/vidéo unique OU un dossier contenant plusieurs
fichiers audio, et effectue les opérations suivantes :
1.  Si un dossier est fourni, il colle tous les fichiers audio dans l'ordre alphabétique.
2.  Coupe les silences et les hésitations de l'audio combiné.
3.  Améliore la voix avec une normalisation professionnelle en deux passes pour une qualité
    optimale sur YouTube et les plateformes de streaming.
4.  (Optionnel) Ajoute une musique de fond avec un effet de "ducking" automatique.

USAGE :
# Pour un dossier d'enregistrements (RECOMMANDÉ POUR LES VOIX OFF) :
$ python audio_processor.py ./mon_dossier_de_voix/ -o voix_finale.mp3

# Pour un fichier unique (audio ou vidéo) :
$ python audio_processor.py ma_video.mp4 -o audio_final.mp3 -m musique.mp3
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
    "SILENCE_THRESH_DB": -40,
    "MIN_SILENCE_LEN_MS": 500,
    "CHUNK_KEEP_SILENCE_MS": 250,
    "OUTPUT_DIR": "audio_enhanced",
    "DUCKING": {"threshold": 0.05, "ratio": 5},

    # Chaîne de filtres pour le workflow professionnel en deux passes
    "PRO_AUDIO_FILTERS": {
        "enabled": True,
        "cleanup_filters": "highpass=f=90,deesser=i=0.5:m=0.5:f=0.5,afftdn=nr=12:nf=-25",
        "dynamics_filters": "equalizer=f=300:width_type=q:w=2:g=-3,equalizer=f=3000:width_type=q:w=2:g=3,acompressor=threshold=0.08:ratio=9:attack=20:release=250",
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
# 2. CONFIGURATION DU LOGGING
# ==============================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# ==============================================================================
# 3. FONCTIONS
# ==============================================================================

def run_command(command: list, capture=False):
    """Exécute une commande shell et gère les erreurs."""
    try:
        logging.debug(f"Exécution : {shlex.join(command)}")
        # Utiliser 'capture_output=True' dans tous les cas pour logger les erreurs
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

    # --- LECTURE ROBUSTE DU JSON ---
    try:
        stderr_text = result_pass1.stderr
        json_start_index = stderr_text.find('{')
        json_end_index = stderr_text.rfind('}')
        if json_start_index == -1 or json_end_index == -1:
            raise ValueError("Bloc JSON introuvable dans la sortie de FFmpeg.")
        json_output = stderr_text[json_start_index : json_end_index + 1]
        loudness_data = json.loads(json_output)
        
        measured_i, measured_tp, measured_lra, measured_thresh, target_offset = (
            float(loudness_data[k]) for k in 
            ["input_i", "input_tp", "input_lra", "input_thresh", "target_offset"]
        )
        logging.info(f"  -> Analyse terminée : Volume perçu={measured_i:.1f} LUFS, Pic max={measured_tp:.1f} dB")
    except (ValueError, json.JSONDecodeError) as e:
        logging.error(f"Impossible de lire les résultats de l'analyse loudnorm : {e}")
        logging.debug(f"Sortie complète de FFmpeg (stderr) pour le débogage:\n{stderr_text}")
        return False

    # --- DEUXIÈME PASSE : APPLICATION ---
    logging.info("  -> Passe 2/2 : Application des corrections sur mesure...")
    final_loudnorm = f"loudnorm=I={targets['integrated_lufs']}:TP={targets['true_peak']}:LRA={targets['lufs_range']}:measured_I={measured_i}:measured_LRA={measured_lra}:measured_tp={measured_tp}:measured_thresh={measured_thresh}:offset={target_offset}"
    final_filters = f"{analysis_filters},{final_loudnorm}"
    
    cmd_pass2 = ["ffmpeg", "-y", "-i", str(input_wav), "-af", final_filters, "-c:a", af_config["audio_codec"], "-b:a", af_config["audio_bitrate"], str(output_path)]
    return run_command(cmd_pass2) is not None

def process_audio(input_path_str: str, output_file: str, config: dict, music_file: str | None, music_volume: float):
    """Orchestre le processus complet de traitement de l'audio."""
    input_path = Path(input_path_str)
    final_output_path = Path(output_file)
    
    # --- ÉTAPE 1 : Chargement et assemblage des audios ---
    logging.info("1/3 - Chargement et assemblage des pistes audio...")
    audio_files_to_process = []
    
    if input_path.is_dir():
        logging.info(f"Dossier détecté. Recherche des fichiers audio (.wav, .m4a, .mp3)...")
        for ext in ["*.wav", "*.m4a", "*.mp3"]:
            audio_files_to_process.extend(sorted(input_path.glob(ext)))
        if not audio_files_to_process:
            logging.error(f"Aucun fichier audio trouvé dans le dossier '{input_path}'."); return
        logging.info(f"{len(audio_files_to_process)} fichiers audio trouvés et triés pour l'assemblage.")
    elif input_path.is_file():
        audio_files_to_process.append(input_path)
    else:
        logging.error(f"Le chemin d'entrée '{input_path}' n'est ni un fichier ni un dossier valide."); return

    try:
        combined_audio = AudioSegment.empty()
        for audio_file in audio_files_to_process:
            logging.debug(f"Assemblage de : {audio_file.name}")
            combined_audio += AudioSegment.from_file(audio_file)
        
        logging.info("Assemblage terminé. Suppression des silences...")
        chunks = split_on_silence(
            combined_audio,
            min_silence_len=config["MIN_SILENCE_LEN_MS"],
            silence_thresh=config["SILENCE_THRESH_DB"],
            keep_silence=config["CHUNK_KEEP_SILENCE_MS"]
        )
        if not chunks: logging.warning("Aucun son n'a été détecté après la découpe des silences."); return
        
        audio_without_silence = sum(chunks)
    except Exception as e:
        logging.error(f"Erreur lors de l'assemblage ou de la découpe : {e}"); return

    # --- ÉTAPE 2 : Amélioration de la voix ---
    logging.info("2/3 - Amélioration de la voix (méthode professionnelle)...")
    temp_wav_path = final_output_path.with_suffix('.temp.wav')
    audio_without_silence.export(temp_wav_path, format="wav")
    enhanced_audio_path = (final_output_path.with_suffix('.enhanced_temp.mp3') if music_file else final_output_path)
    if not enhance_audio_professional(temp_wav_path, enhanced_audio_path, config):
        logging.error("L'étape d'amélioration a échoué."); temp_wav_path.unlink(); return
    temp_wav_path.unlink()

    if not music_file:
        logging.info(f"✅ Succès ! Fichier audio traité sauvegardé dans : '{final_output_path.resolve()}'"); return

    # --- ÉTAPE 3 : Mixage musical (si demandé) ---
    logging.info("3/3 - Ajout de la musique de fond...")
    af_config = config["PRO_AUDIO_FILTERS"]
    duck_config = config["DUCKING"]
    filter_complex = (f"[0:a]aformat=sample_rates=48000:channel_layouts=stereo[voice_norm];[1:a]volume={music_volume}dB,aformat=sample_rates=48000:channel_layouts=stereo[bg_norm];[voice_norm]asplit[voice_main][voice_side];[voice_side]volume=15dB[voice_side_amp];[bg_norm][voice_side_amp]sidechaincompress=threshold={duck_config['threshold']}:ratio={duck_config['ratio']}[ducked_bg];[voice_main][ducked_bg]amix=inputs=2[a_out]")
    cmd_mix = ["ffmpeg", "-y", "-i", str(enhanced_audio_path), "-stream_loop", "-1", "-i", str(music_file), "-filter_complex", filter_complex, "-map", "[a_out]", "-c:a", af_config["audio_codec"], "-b:a", af_config["audio_bitrate"], "-shortest", str(final_output_path)]
    if run_command(cmd_mix):
        logging.info(f"✅ Succès ! Fichier final avec musique sauvegardé dans : '{final_output_path.resolve()}'")
    else:
        logging.error("Le mixage musical a échoué.")
    enhanced_audio_path.unlink()

# ==============================================================================
# 4. POINT D'ENTRÉE DU SCRIPT
# ==============================================================================
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Processeur audio pour voix off, podcasts et vidéos.", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("input_path", type=str, help="Fichier audio/vidéo unique OU dossier contenant plusieurs fichiers audio.")
    parser.add_argument("-o", "--output-file", type=str, help="Fichier de sortie audio (.mp3). Si non spécifié, généré automatiquement.")
    parser.add_argument("--no-audio-filters", action="store_true", help="Désactive tous les filtres d'amélioration.")
    
    music_group = parser.add_argument_group("Options pour la musique de fond")
    music_group.add_argument("-m", "--music", type=str, help="Fichier audio de musique de fond à ajouter.")
    music_group.add_argument("--music-volume", type=float, default=-25.0, help="Volume de la musique en dB. Défaut: -25.0.")

    args = parser.parse_args()
    input_p = Path(args.input_path)
    if not input_p.exists():
        logging.error(f"Le chemin d'entrée '{input_p}' est introuvable."); exit(1)

    if args.music and not Path(args.music).is_file():
        logging.error(f"Fichier de musique introuvable : '{args.music}'"); exit(1)

    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        output_dir = Path(CONFIG["OUTPUT_DIR"]); output_dir.mkdir(parents=True, exist_ok=True)
        # Nom de sortie intelligent basé sur le nom du dossier ou du fichier
        output_filename = f"{input_p.name}_processed.mp3"
        output_path = output_dir / output_filename

    current_config = CONFIG.copy()
    if args.no_audio_filters: 
        current_config["PRO_AUDIO_FILTERS"]["enabled"] = False
        logging.info("Filtres audio désactivés.")
    
    process_audio(
        input_path_str=str(input_p), 
        output_file=str(output_path), 
        config=current_config,
        music_file=args.music, 
        music_volume=args.music_volume
    )