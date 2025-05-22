import pyaudio
import wave
import threading
import time
import os
import sys
import select
import termios
import tty

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
        self.terminal_settings = None

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

    def toggle_pause(self):
        self.paused = not self.paused
        status = "paused" if self.paused else "resumed"
        print(f"Recording {status}")

    def stop_recording(self):
        if self.stream:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            
            # Save the complete recording
            self.save_recording()
            self.frames = []  # Clear frames after saving

    def cleanup(self):
        self.p.terminate()

    def check_keyboard(self):
        if select.select([sys.stdin], [], [], 0)[0]:
            key = sys.stdin.read(1)
            if key == ' ':  # Space
                self.toggle_pause()
            elif key == 'q':  # Q
                self.stop_recording()
                return False
        return True

def main():
    recorder = AudioRecorder()
    
    try:
        recorder.list_audio_devices()
        device_id = recorder.select_device()
        
        recorder.start_recording(device_id)
        
        # Keep the main thread alive and check for keyboard input
        while recorder.recording:
            if not recorder.check_keyboard():
                break
            time.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    finally:
        recorder.cleanup()

if __name__ == "__main__":
    main()
