import os
import subprocess
import sys

# FFMPEG_PATH needs to be defined here as well, or passed as an argument.
# For now, let's assume it's in PATH or defined as a constant.
FFMPEG_PATH = "ffmpeg"  # Assuming ffmpeg is in system PATH or defined here

def merge_audio_video(video_path, audio_path, output_path):
    """Merges the recorded video and audio files using ffmpeg."""
    print("[*] Merging audio and video to create final file...")
    
    if not os.path.exists(video_path) or os.path.getsize(video_path) == 0:
        print(f"[!] Error: Video file is missing or empty: {video_path}")
        return False
    if not os.path.exists(audio_path) or os.path.getsize(audio_path) == 0:
        print(f"[!] Error: Audio file is missing or empty: {audio_path}")
        return False

    cmd = [
        FFMPEG_PATH, '-y',
        '-i', video_path,
        '-i', audio_path,
        '-c:v', 'copy',
        '-c:a', 'aac',
        '-map', '0:v:0',
        '-map', '1:a:0',
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[!] Final video with sound saved to: {output_path}")
            return True
        else:
            print(f"[!] FFmpeg failed (code {result.returncode}). Error output:\n{result.stderr}")
            return False
    except FileNotFoundError:
        print(f"[!] Error: FFmpeg not found. Ensure '{FFMPEG_PATH}' is installed and in your PATH.")
        print("[!] Download FFmpeg from https://ffmpeg.org/ if it is not installed.")
        return False
    except Exception as e:
        print(f"[!] An unexpected error occurred during merging: {e}")
        return False

if __name__ == "__main__":
    # If no arguments are provided, try to use the default paths from video-maker.py
    if len(sys.argv) == 1:
        output_dir = "./webinar_output"
        video_file = os.path.join(output_dir, "webinar_video.mp4")
        audio_file = os.path.join(output_dir, "webinar_audio.wav")
        output_file = os.path.join(output_dir, "webinar_final.mp4")
        
        print(f"[*] No arguments provided. Using defaults:")
        print(f"    Video: {video_file}\n    Audio: {audio_file}\n    Output: {output_file}")
    elif len(sys.argv) == 4:
        video_file = sys.argv[1]
        audio_file = sys.argv[2]
        output_file = sys.argv[3]
    else:
        print("Usage: python aud-vid-merge.py <video_file_path> <audio_file_path> <output_file_path>")
        print("Or run without arguments to use default './webinar_output' files.")
        sys.exit(1)
    
    merge_audio_video(video_file, audio_file, output_file)