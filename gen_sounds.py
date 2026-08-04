import wave
import math
import struct
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SOUNDS_DIR = os.path.join(BASE_DIR, 'sounds')
os.makedirs(SOUNDS_DIR, exist_ok=True)

def generate_tone(filename, freqs, duration_ms, sample_rate=44100):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        num_frames = int(sample_rate * (duration_ms / 1000.0))
        phase = 0.0
        for i in range(num_frames):
            if isinstance(freqs, tuple):
                f_start, f_end = freqs
                freq = f_start + (f_end - f_start) * (i / num_frames)
            else:
                freq = freqs
                
            phase += 2 * math.pi * freq / sample_rate
            val = math.sin(phase)
            env = 1.0
            if i < 400: env = i / 400
            if i > num_frames - 400: env = (num_frames - i) / 400
            
            val = int(val * env * 32767)
            data = struct.pack('<h', val)
            f.writeframesraw(data)

def generate_double_beep(filename, freq, duration_ms=80, gap_ms=40, sample_rate=44100):
    with wave.open(filename, 'w') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        
        def write_tone(fq, dur):
            num_frames = int(sample_rate * (dur / 1000.0))
            for i in range(num_frames):
                t = i / sample_rate
                val = math.sin(2 * math.pi * fq * t)
                env = 1.0
                if i < 400: env = i / 400
                if i > num_frames - 400: env = (num_frames - i) / 400
                val = int(val * env * 32767)
                f.writeframesraw(struct.pack('<h', val))
                
        def write_silence(dur):
            num_frames = int(sample_rate * (dur / 1000.0))
            for i in range(num_frames):
                f.writeframesraw(struct.pack('<h', 0))
                
        write_tone(freq, duration_ms)
        write_silence(gap_ms)
        write_tone(freq, duration_ms)

# Generate sounds
generate_tone(os.path.join(SOUNDS_DIR, 'start.wav'), (440, 880), 200)
generate_tone(os.path.join(SOUNDS_DIR, 'stop.wav'), (880, 440), 200)
generate_double_beep(os.path.join(SOUNDS_DIR, 'pause.wav'), 400)
generate_double_beep(os.path.join(SOUNDS_DIR, 'unpause.wav'), 800)

print("Sounds generated!")
