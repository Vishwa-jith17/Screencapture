import pyautogui
import cv2
import numpy as np
import time
import multiprocessing as mp
import pyaudio
import wave
from pynput import mouse, keyboard

# Screen recording
def capture_screen(queue):
    while True:
        screenshot = pyautogui.screenshot()
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not queue.full():
            queue.put(frame)
        time.sleep(1/10)  # Capture at 10 frames per second

# Audio recording
def capture_audio(queue):
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
    while True:
        data = stream.read(1024)
        if not queue.full():
            queue.put(data)

# Mouse movements and keystrokes
def capture_mouse_keystrokes(mouse_queue, keyboard_queue):
    def on_click(x, y, button, pressed):
        mouse_queue.put((x, y, button, pressed))
    
    def on_press(key):
        keyboard_queue.put(('press', key))
    
    def on_release(key):
        keyboard_queue.put(('release', key))
    
    with mouse.Listener(on_click=on_click) as mouse_listener, keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
        mouse_listener.join()
        keyboard_listener.join()

def main():
    # Setup
    screen_queue = mp.Queue(maxsize=10)
    audio_queue = mp.Queue(maxsize=10)
    mouse_queue = mp.Queue(maxsize=10)
    keyboard_queue = mp.Queue(maxsize=10)

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    video_writer = cv2.VideoWriter('screen.mp4', fourcc, 10.0, pyautogui.size())

    # Audio writer setup
    audio_writer = wave.open('audio.mp3', 'wb')
    audio_writer.setnchannels(1)
    audio_writer.setsampwidth(pyaudio.PyAudio().get_sample_size(pyaudio.paInt16))
    audio_writer.setframerate(44100)

    # Start capture processes
    screen_proc = mp.Process(target=capture_screen, args=(screen_queue,))
    audio_proc = mp.Process(target=capture_audio, args=(audio_queue,))
    mouse_proc = mp.Process(target=capture_mouse_keystrokes, args=(mouse_queue, keyboard_queue))
    
    screen_proc.start()
    audio_proc.start()
    mouse_proc.start()

    try:
        while True:
            if not screen_queue.empty():
                frame = screen_queue.get()
                video_writer.write(frame)
            
            if not audio_queue.empty():
                data = audio_queue.get()
                audio_writer.writeframes(data)
            
            if not mouse_queue.empty():
                mouse_data = mouse_queue.get()
                print("Mouse:", mouse_data)  # Example output
            
            if not keyboard_queue.empty():
                keyboard_data = keyboard_queue.get()
                print("Keyboard:", keyboard_data)  # Example output
    except KeyboardInterrupt:
        pass
    finally:
        screen_proc.terminate()
        audio_proc.terminate()
        mouse_proc.terminate()
        video_writer.release()
        audio_writer.close()

if __name__ == "__main__":
    main()
