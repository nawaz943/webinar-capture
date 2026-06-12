import pyaudio
import struct
import math

def list_audio_devices():
    p = pyaudio.PyAudio()
    device_count = p.get_device_count()

    print(f"Total devices found: {device_count}")
    print("\n--- AUDIO INPUT DIAGNOSTICS ---")
    print("Step 1: Start playing your webinar audio now (unmuted).")
    print("Step 2: We will check every input for a signal (VU Meter).\n")
    
    for i in range(device_count):
        try:
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels') > 0:
                name = info.get('name')
                host_api = p.get_host_api_info_by_index(info.get('hostApi')).get('name')
                default_rate = int(info.get('defaultSampleRate'))
                
                print(f"[Index {i}] {name}")
                print(f"    API: {host_api} | Channels: {info.get('maxInputChannels')} | Rate: {default_rate}Hz")
                
                # Test signal for ~0.4 seconds
                try:
                    stream = p.open(format=pyaudio.paInt16,
                                    channels=1,
                                    rate=default_rate,
                                    input=True,
                                    input_device_index=i,
                                    frames_per_buffer=1024)
                    
                    max_rms = 0
                    for _ in range(20):
                        data = stream.read(1024, exception_on_overflow=False)
                        shorts = struct.unpack("%dh" % (len(data) // 2), data)
                        sum_squares = sum(s*s for s in shorts)
                        rms = math.sqrt(max(sum_squares / len(shorts), 0))
                        if rms > max_rms: max_rms = rms
                    
                    stream.stop_stream()
                    stream.close()
                    
                    status = ">>> SIGNAL DETECTED! <<<" if max_rms > 50 else "SILENCE"
                    print(f"    Result: {status} (Peak Level: {max_rms:.1f})\n")
                    
                except Exception as e:
                    print(f"    Result: UNAVAILABLE ({e})\n")
        except Exception:
            continue
    
    p.terminate()

if __name__ == "__main__":
    list_audio_devices()
