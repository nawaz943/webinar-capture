import os
import sys
import time
import subprocess
import cv2
import struct
import math
import numpy as np
import mss
import threading
import wave
import pyaudio
import pygetwindow as gw

# Suppress the Hugging Face symlink warning on Windows
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# Fix for CUDA DLLs on Windows (Required for faster-whisper/ctranslate2)
# This block is included for consistency, though not strictly needed for recording.
if sys.platform == "win32":
    import site
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
WEBINAR_WINDOW_TITLE = "Cut Your Carbs with Water: Why Hydronics are a Key Nutrient in Electrification and Decarbonization (5288768)" # Part of the title of your Chrome tab
OUTPUT_DIR = "./webinar_output"
SCREENSHOT_THRESHOLD = 5.0  # Percentage of change to trigger a new slide save
SLIDE_WIDTH_PERCENTAGE = 0.5  # Percentage of the window width used by the slide box (on the left)
AUDIO_CHUNK_SIZE = 1024
CHANNELS = 2
RATE = 48000
VIDEO_FPS = 10  # Frames per second for video recording
DEVICE_INDEX = 15  # Set to Stereo Mix (Realtek High Definition Audio) - Windows WASAPI API


os.makedirs(OUTPUT_DIR, exist_ok=True)

class WebinarRecorder:
    def __init__(self):
        self.running = True

    def capture_slides(self):
        """Captures screenshots only when the screen content changes significantly."""
        with mss.MSS() as sct:
            last_frame = None
            slide_count = 0

            print("[*] Slide capture started...")
            while self.running:
                windows = gw.getWindowsWithTitle(WEBINAR_WINDOW_TITLE)
                if not windows:
                    time.sleep(2)
                    continue
                
                win = windows[0]
                print(f"[*] Slide Capture: Found window '{win.title}' at {win.left},{win.top} with size {win.width}x{win.height}")
                
                if win.isMinimized:
                    print("[!] Warning: Webinar window is minimized. Cannot capture slides.")
                    time.sleep(5)
                    continue

                slide_width = int(win.width * SLIDE_WIDTH_PERCENTAGE)
                region = {
                    "top": win.top,
                    "left": win.left,
                    "width": slide_width,
                    "height": win.height
                }

                img = sct.grab(region)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_frame = cv2.GaussianBlur(gray_frame, (21, 21), 0)

                if last_frame is not None:
                    diff = cv2.absdiff(last_frame, gray_frame)
                    thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1]
                    change_percent = (np.count_nonzero(thresh) / thresh.size) * 100

                    if change_percent > SCREENSHOT_THRESHOLD:
                        slide_count += 1
                        path = os.path.join(OUTPUT_DIR, f"slide_{slide_count:03d}.png")
                        cv2.imwrite(path, frame)
                        print(f"[+] New slide detected: {path}")
                
                last_frame = gray_frame
                time.sleep(2)

    def record_video(self, filename):
        """Records the webinar window to a video file."""
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = None
        
        with mss.MSS() as sct:
            print("[*] Video recording started...")
            while self.running:
                start_time = time.time()
                
                windows = gw.getWindowsWithTitle(WEBINAR_WINDOW_TITLE)
                if windows and not windows[0].isMinimized:
                    win = windows[0]
                    print(f"[*] Video Record: Found window '{win.title}' at {win.left},{win.top} with size {win.width}x{win.height}")
                    region = {
                        "top": win.top, "left": win.left, 
                        "width": win.width, "height": win.height
                    }
                    
                    img = sct.grab(region)
                    frame = np.array(img)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    
                    if out is None:
                        h, w = frame.shape[:2]
                        out = cv2.VideoWriter(filename, fourcc, VIDEO_FPS, (w, h))
                    
                    out.write(frame)
                
                elapsed = time.time() - start_time
                time.sleep(max(1./VIDEO_FPS - elapsed, 0))
                
        if out:
            out.release()
            print(f"[!] Video saved to {filename}")

    def record_audio(self, filename):
        """Records system audio to a WAV file."""
        p = pyaudio.PyAudio()
        stream = None
        wf = None
        try:
            device_info = p.get_device_info_by_index(DEVICE_INDEX)
            print(f"[*] Audio Recording: Initializing device '{device_info.get('name')}' (Index {DEVICE_INDEX}) at {RATE}Hz")
            
            stream = p.open(format=pyaudio.paInt16,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            frames_per_buffer=AUDIO_CHUNK_SIZE,
                            input_device_index=DEVICE_INDEX)

            print("[*] Audio recording started...")
            wf = wave.open(filename, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(pyaudio.paInt16))
            wf.setframerate(RATE)

            print("[*] Monitoring volume... (Make sure levels are above 100)")
            status_counter = 0
            while self.running:
                data = stream.read(AUDIO_CHUNK_SIZE, exception_on_overflow=False)
                wf.writeframes(data)

                status_counter += 1
                if status_counter % 45 == 0:
                    shorts = struct.unpack("%dh" % (len(data) // 2), data)
                    sum_squares = sum(s*s for s in shorts)
                    rms = math.sqrt(max(sum_squares / len(shorts), 0))
                    if rms < 50:
                        print(f"[!] Warning: Audio level very low ({rms:.1f}). Is the webinar muted?")
                    else:
                        print(f"[*] Recording volume: {rms:.1f} (OK)")

        except Exception as e:
            print(f"[!] Audio Recording Error: {e}")
            self.running = False
        finally:
            if wf: wf.close()
            if stream:
                stream.stop_stream()
                stream.close()
            p.terminate()

    def run(self):
        audio_file = os.path.join(OUTPUT_DIR, "webinar_audio.wav")
        video_file = os.path.join(OUTPUT_DIR, "webinar_video.mp4")
        
        slide_thread = threading.Thread(target=self.capture_slides)
        audio_thread = threading.Thread(target=self.record_audio, args=(audio_file,))
        video_thread = threading.Thread(target=self.record_video, args=(video_file,))
        
        slide_thread.start()
        audio_thread.start()
        video_thread.start()

        print("\n[!!!] START PLAYING THE WEBINAR NOW [!!!]\n")
        try:
            print("[#] Recording... Press Ctrl+C to stop recording.")
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.running = False
            slide_thread.join()
            audio_thread.join()
            video_thread.join()
            print("[!] Recording stopped. Check output folder for files.")
            
            try:
                final_file = os.path.join(OUTPUT_DIR, "webinar_final.mp4")
                # 1. Merge
                print(f"[*] Calling aud-vid-merge.py to merge {video_file} and {audio_file} into {final_file}")
                subprocess.run([sys.executable, "aud-vid-merge.py", video_file, audio_file, final_file], check=True)
                
                # 2. Transcribe
                print(f"[*] Calling transcriber.py to transcribe {audio_file}")
                subprocess.run([sys.executable, "transcriber.py", audio_file], check=True)
                
                # 3. Summarize
                transcript_file = os.path.join(OUTPUT_DIR, "webinar_audio_transcript.txt")
                print(f"[*] Calling summarizer.py to summarize {transcript_file}")
                subprocess.run([sys.executable, "summarizer.py", transcript_file], check=True)
                
                print("[!] Full post-processing pipeline completed successfully.")
            except subprocess.CalledProcessError as e:
                print(f"[!] Pipeline failed at step: {e.cmd}. Error: {e}")

if __name__ == "__main__":
    recorder = WebinarRecorder()
    recorder.run()