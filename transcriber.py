import os
import sys
import time
from faster_whisper import WhisperModel

# Suppress the Hugging Face symlink warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Fix for CUDA DLLs on Windows (Required for faster-whisper/ctranslate2)
if sys.platform == "win32":
    import site
    # Search for nvidia-* packages in the site-packages directories
    search_paths = site.getsitepackages()
    if hasattr(site, 'getusersitepackages'):
        search_paths.append(site.getusersitepackages())

    for packages_dir in search_paths:
        for pkg in ["cublas", "cudnn", "cuda_runtime"]:
            for subfolder in ["lib", "bin"]:
                full_path = os.path.join(packages_dir, "nvidia", pkg, subfolder)
                if os.path.exists(full_path):
                    print(f"[*] Found CUDA DLLs at: {full_path}")
                    os.add_dll_directory(full_path)

# --- CONFIGURATION ---
MODEL_SIZE = "large-v3"  # Optimized for RTX A4000
OUTPUT_DIR = "./webinar_output"
# ---------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

class AudioTranscriber:
    def __init__(self):
        print(f"[*] Loading Whisper model '{MODEL_SIZE}' on CUDA...")
        self.model = WhisperModel(MODEL_SIZE, device="cuda", compute_type="float16")

    def transcribe_locally(self, audio_path):
        """Transcribes the recorded audio using local Whisper model."""
        if not os.path.exists(audio_path):
            print(f"[!] Error: Audio file {audio_path} not found. Transcription aborted.")
            return

        print(f"[*] Starting transcription of {audio_path}...")
        segments, info = self.model.transcribe(audio_path, beam_size=5)
        
        # Derive transcript filename from audio_path
        audio_filename_base = os.path.splitext(os.path.basename(audio_path))[0]
        transcript_path = os.path.join(OUTPUT_DIR, f"{audio_filename_base}_transcript.txt")
        with open(transcript_path, "w") as f:
            for segment in segments:
                line = f"[{segment.start:.2f}s -> {segment.end:.2f}s] {segment.text}\n"
                f.write(line)
                print(line.strip())
        
        print(f"[!] Transcription saved to {transcript_path}")

if __name__ == "__main__":
    # If no arguments are provided, try to use the default audio file from video-maker.py
    if len(sys.argv) == 1:
        audio_file_to_transcribe = os.path.join(OUTPUT_DIR, "webinar_audio.wav")
        print(f"[*] No arguments provided. Using default audio file: {audio_file_to_transcribe}")
        if not os.path.exists(audio_file_to_transcribe):
            print(f"[!] Error: Default audio file '{audio_file_to_transcribe}' not found.")
            print("Usage: python transcriber.py <path_to_audio_file>")
            print(f"Example: python transcriber.py {os.path.join(OUTPUT_DIR, 'webinar_audio.wav')}")
            sys.exit(1)
    elif len(sys.argv) == 2:
        audio_file_to_transcribe = sys.argv[1]
    else:
        print("Usage: python transcriber.py <path_to_audio_file>")
        print(f"Example: python transcriber.py {os.path.join(OUTPUT_DIR, 'webinar_audio.wav')}")
        print("Or run without arguments to use default './webinar_output/webinar_audio.wav'.")
        sys.exit(1)

    transcriber = AudioTranscriber()
    transcriber.transcribe_locally(audio_file_to_transcribe)
