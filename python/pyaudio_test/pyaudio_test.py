import pyaudio
import wave
import threading
import time
import os
import sys
from pynput import keyboard

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.recording = False
        self.paused = False
        self.stream = None
        self.frames = []
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 44100
        self.output_file = "output.wav"
        self.listener = None

    def list_audio_devices(self):
        print("\nAvailable Audio Input Devices:")
        print("-" * 50)
        for i in range(self.p.get_device_count()):
            dev_info = self.p.get_device_info_by_index(i)
            if dev_info.get('maxInputChannels') > 0:
                print(f"Device {i}: {dev_info.get('name')}")
        print("-" * 50)

    def select_device(self):
        while True:
            try:
                device_id = int(input("\nEnter the device number to use: "))
                dev_info = self.p.get_device_info_by_index(device_id)
                if dev_info.get('maxInputChannels') > 0:
                    return device_id
                else:
                    print("Invalid device. Please select an input device.")
            except (ValueError, IndexError):
                print("Invalid input. Please enter a valid device number.")

    def callback(self, in_data, frame_count, time_info, status):
        if self.recording and not self.paused:
            self.frames.append(in_data)
        time.sleep(0.001)  # Small sleep to prevent timeout
        return (in_data, pyaudio.paContinue)

    def save_recording(self):
        if not self.frames:
            print("No audio data to save")
            return
            
        with wave.open(self.output_file, 'wb') as wf:
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.p.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(self.frames))
        
        print(f"\nRecording saved to {self.output_file}")
        print(f"Duration: {len(self.frames) * self.CHUNK / self.RATE:.2f} seconds")

    def on_press(self, key):
        try:
            if key == keyboard.Key.space:
                self.toggle_pause()
            elif key == keyboard.KeyCode.from_char('q'):
                self.stop_recording()
                return False  # Stop listener
        except AttributeError:
            pass
        return True

    def start_keyboard_listener(self):
        self.listener = keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def stop_keyboard_listener(self):
        if self.listener:
            self.listener.stop()
            self.listener = None

    def start_recording(self, device_id):
        self.stream = self.p.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            input_device_index=device_id,
            frames_per_buffer=self.CHUNK,
            stream_callback=self.callback
        )
        
        self.recording = True
        self.stream.start_stream()
        print("\nRecording started. Press SPACE to pause/resume, Q to stop and save.")
        self.start_keyboard_listener()

    def toggle_pause(self):
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        print(f"Recording {status}")

    def stop_recording(self):
        self.stop_keyboard_listener()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
            # Save the complete recording
            self.save_recording()
            self.frames = []  # Clear frames after saving
            self.recording = False

    def cleanup(self):
        self.stop_keyboard_listener()
        self.p.terminate()

def main():
    recorder = AudioRecorder()
    
    try:
        recorder.list_audio_devices()
        device_id = recorder.select_device()
        
        recorder.start_recording(device_id)
        
        # Keep the main thread alive
        while recorder.recording:
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()
