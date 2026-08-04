import soundfile as sf
import numpy as np
import time

def main():
    try:
        print("Creating E:\\test.wav...")
        with sf.SoundFile("E:\\test.wav", mode='w', samplerate=44100, channels=2) as f:
            print("PULL THE DRIVE NOW!")
            for _ in range(100):
                f.write(np.zeros((44100, 2), dtype=np.float32))
                f.flush()
                time.sleep(0.1)
    except Exception as e:
        print("Python caught it safely:", repr(e))

if __name__ == "__main__":
    main()
