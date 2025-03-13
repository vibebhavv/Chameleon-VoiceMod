import os
import numpy as np
import tkinter as tk
import sounddevice as sd
import customtkinter as ctk
from tkinter import filedialog

# Necessary logic file
import RealTime
from ConsoleLog import ConsoleLogging
import PreRec

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Chameleon VoicMod")
        self.geometry(f"{400}x{750}")
        self.resizable(False, False)
        
        # input and output device list
        devices = sd.query_devices()
        input_devices = [f"{i}: {d['name']}" for i, d in enumerate(devices) if d['max_input_channels'] > 0]
        output_devices = [f"{i}: {d['name']}" for i, d in enumerate(devices) if d['max_output_channels'] > 0]

        self.main_frame = ctk.CTkFrame(self, width=400, height=500)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
       
        self.main_frame.grid_columnconfigure(0, weight=1) 
        self.main_frame.grid_columnconfigure(1, weight=1) 
        self.main_frame.grid_columnconfigure(2, weight=1) 

        self.device_list_frame = ctk.CTkFrame(self.main_frame)
        self.device_list_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=10)
        self.device_list_frame.grid_columnconfigure(0, weight=1)

        self.input_devices = ctk.CTkOptionMenu(self.device_list_frame, 
                                             values=input_devices, 
                                             width=380, dynamic_resizing=False)
        self.input_devices.grid(row=1, column=0, pady=(5,5), padx=(5,5), sticky="ew")

        self.output_devices = ctk.CTkOptionMenu(self.device_list_frame, 
                                              values=output_devices, 
                                              width=380, dynamic_resizing=False)
        self.output_devices.grid(row=2, column=0, pady=(5,5), padx=(5,5), sticky="ew")

        self.mode_filter_frame = ctk.CTkFrame(self.main_frame)
        self.mode_filter_frame.grid(row=1, column=0, padx=5, pady=5)

        self.radio_var = tk.IntVar(value=0)
        
        # radio buttons for realtime and prerecorded audio 
        self.real_time = ctk.CTkRadioButton(
            master=self.mode_filter_frame,
            variable=self.radio_var,
            value=0,
            text="Realtime",
            command=self.upload_audio_enable
            )
        self.real_time.grid(row=0, column=0, pady=(10,0), padx=20, sticky="w")

        self.upload_audio = ctk.CTkRadioButton(
            master=self.mode_filter_frame,
            variable=self.radio_var,
            value=2,
            text="Pre-Recorded",
            command=self.upload_audio_enable
        )
        self.upload_audio.grid(row=1, column=0, pady=(10,0), padx=20, sticky="w")

        # low cut and high cut filter
        self.low_cut_var = ctk.BooleanVar(value=True)
        self.low_cut_filter = ctk.CTkSwitch(
            master=self.mode_filter_frame,
            text="Low cut filter",
            variable=self.low_cut_var
            )
        self.low_cut_filter.grid(row=0, column=1, pady=(10,0), padx=20, sticky="e")

        self.high_cut_var = ctk.BooleanVar(value=True)
        self.high_cut_filter = ctk.CTkSwitch(
            master=self.mode_filter_frame,
            text="High cut filter",
            variable=self.high_cut_var
            )
        self.high_cut_filter.grid(row=1, column=1, pady=(10, 0), padx=20, sticky="e")

        # prerecord audio file upload button
        self.upload_audio_button = ctk.CTkButton(
            master=self.mode_filter_frame,
            command=self.upload_audio_file,
            text="Upload Audio File",
            state="disabled",
            )
        self.upload_audio_button.grid(row=2, column=0, columnspan=2, pady=(20, 10), padx=10, sticky="ew")
        
        self.slider_frame = ctk.CTkFrame(self.main_frame)
        self.slider_frame.grid(row=6, column=0, pady=(10,10), padx=(10,10), sticky="ew")

        # volume, pitch, echo, reverb and noise gate slider
        self.volume = ctk.CTkSlider(
            master=self.slider_frame,
            from_=0,
            to=100,
            orientation="horizontal"
        )
        self.volume.grid(row=0, column=1, pady=10, padx=10, sticky="ew")
        self.volume.set(70)  # Default volume
        
        self.volume_label = ctk.CTkLabel(self.slider_frame, text="Volume")
        self.volume_label.grid(row=0, column=0, pady=10, padx=10)

        self.pitch = ctk.CTkSlider(
            master=self.slider_frame,
            from_=-12,
            to=12,
            orientation="horizontal",
        )
        self.pitch.grid(row=1, column=1, pady=10, padx=10, sticky="ew")
        self.pitch.set(0)  # Default pitch (no change)
        
        self.pitch_label = ctk.CTkLabel(self.slider_frame, text="Pitch")
        self.pitch_label.grid(row=1, column=0, pady=10, padx=10)

        self.echo = ctk.CTkSlider(
            master=self.slider_frame,
            from_=0,
            to=100,
            orientation="horizontal"
        )
        self.echo.grid(row=2, column=1, pady=10, padx=10, sticky="ew")
        self.echo.set(0)  # Default echo
        
        self.echo_label = ctk.CTkLabel(self.slider_frame, text="Echo")
        self.echo_label.grid(row=2, column=0, pady=10, padx=10)

        self.reverb = ctk.CTkSlider(
            master=self.slider_frame,
            from_=0,
            to=100,
            orientation="horizontal"
        )
        self.reverb.grid(row=3, column=1, pady=10, padx=10, sticky="ew")
        self.reverb.set(0)  # Default reverb
        
        self.reverb_label = ctk.CTkLabel(self.slider_frame, text="Reverb")
        self.reverb_label.grid(row=3, column=0, pady=10, padx=10)

        self.gate_scale = ctk.CTkSlider(
            master=self.slider_frame,
            from_=0,
            to=100,
            orientation="horizontal"
        )
        self.gate_scale.grid(row=4, column=1, pady=10, padx=10, sticky="ew")
        self.gate_scale.set(20)  # Default noise gate threshold
        
        self.noise_gate_label = ctk.CTkLabel(self.slider_frame, text="Noise Gate\nThreshold")
        self.noise_gate_label.grid(row=4, column=0, pady=10, padx=10)

        # start for realtime and generate button for prerecorded audio file
        self.start_button = ctk.CTkButton(
            master=self.main_frame,
            text="START",
            command=self.start
        )
        self.start_button.grid(row=7, column=0, pady=(10,5), padx=(40,10), sticky="w")
 
        self.generate_button = ctk.CTkButton(
            master=self.main_frame,
            text="GENERATE",
            command=self.generate_media,
            state="disabled"
        )
        self.generate_button.grid(row=7, column=0, pady=(10,5), padx=(10,40), sticky="e")

        self.media_button = ctk.CTkButton(
            master=self.main_frame,
            width=20,
            text="⏯",
            command=self.media_con,
            state="disabled"
        )
        self.media_button.grid(row=8, column=0, pady=10, padx=(10,10), sticky="w")

        # media progress bar and save button to save new modified audio file
        self.media_progress_bar = ctk.CTkProgressBar(
            master=self.main_frame
        )
        self.media_progress_bar.grid(row=8, column=0, columnspan=2, pady=10, padx=(50,70), sticky="ew")
        self.media_progress_bar.set(0)

        self.save_audio = ctk.CTkButton(
            master=self.main_frame,
            width=50,
            text="SAVE",
            command=self.save_file,
            state="disabled"
        )
        self.save_audio.grid(row=8, column=0, pady=10, padx=(10,10), sticky="e")

        self.log_frame = ctk.CTkFrame(self.main_frame)
        self.log_frame.grid(row=9, column=0, sticky="ew")

        self.log_box = ctk.CTkTextbox(
            width=390,
            height=150,
            wrap='word',
            border_width=1,
            bg_color="black",
            border_color="white",
            master=self.log_frame,
            )
        self.log_box.grid(row=0, column=0, pady=5, padx=(3,3))
        self.log_box.configure(state="disabled")
        
        self.logger = ConsoleLogging(self.log_box)
        self.logger.setup_tags()

        self.is_running = False
        self.stream = None
        self.filters = RealTime.init_filter()
        self.filename = None
        self.modified_audio = None
        self.is_playing = False
        self.file_loc = None

    def get_device_id(self, device_string):
        return int(device_string.split(":")[0]) if device_string else None

    def audio_callback(self, indata, outdata, frames, time, status):
        if status:
            self.logger.log_error(f"[ERR] Status: {status}")
            #print(x)
        
        # Debug info
        self.logger.log_info(f"[DEBUG] Input max: {np.max(np.abs(indata))} frames: {frames}")
        #print(y)
        
        if self.is_running:
            try:
                # Get settings
                pitch_shift_value = self.pitch.get()
                volume = self.volume.get() / 100.0
                echo_value = self.echo.get() / 100.0
                reverb_value = self.reverb.get() / 100.0
                gate_threshold = self.gate_scale.get() / 100.0

                # Extract audio data from first channel (mono)
                audio_data = indata[:, 0].copy() if indata.shape[1] > 0 else indata.copy().flatten()

                # Apply noise gate
                audio_data = RealTime.noise_gate(audio_data, gate_threshold)
                
                # Apply filters
                audio_data = RealTime.apply_filter(audio_data, self.filters, 
                                                self.low_cut_var.get(), 
                                                self.high_cut_var.get())

                # Apply pitch shifting
                shifted_data = RealTime.pitch_shift(audio_data, RealTime.RATE, pitch_shift_value)

                # Apply echo if value > 0
                if echo_value > 0:
                    shifted_data = RealTime.add_echo(shifted_data, echo_value)
                
                # Apply reverb if value > 0
                if reverb_value > 0:
                    shifted_data = RealTime.add_reverb(shifted_data, reverb_value)

                # Apply volume
                shifted_data = shifted_data[:frames] * volume

                # Fill all output channels with the processed audio
                for channel in range(outdata.shape[1]):
                    outdata[:, channel] = shifted_data

            except Exception as e:
                self.logger.log_error(f"[ERR] Error in audio processing: {e}")
                outdata.fill(0)
        else:
            outdata.fill(0)

    def start(self):
        try:
            input_device_id = self.get_device_id(self.input_devices.get())
            output_device_id = self.get_device_id(self.output_devices.get())
            
            if self.is_running:
                # Stop the stream (code remains unchanged)
                if self.stream:
                    self.stream.stop()
                    self.stream.close()
                    self.stream = None
                self.is_running = False
                self.start_button.configure(text="START")
                self.logger.log_info("[***] Voice Modulation Stopped")
            else:
                # Start the stream
                self.logger.log_info("[***] Starting Voice Modulation...")
                self.logger.log_info(f"[INFO] Input Device: {self.input_devices.get()}")
                self.logger.log_info(f"[INFO] Output Device: {self.output_devices.get()}")
                
                try:
                    # Get device info to check supported channels
                    devices = sd.query_devices()
                    input_channels = devices[input_device_id]['max_input_channels']
                    output_channels = devices[output_device_id]['max_output_channels']
                    
                    # Use minimum of 1 or available channels (typically we want 1 channel for voice)
                    channels_in = min(1, input_channels)
                    channels_out = min(2, output_channels)  # Prefer stereo output if available
                    
                    self.logger.log_info(f"[INFO] Using {channels_in} input channels and {channels_out} output channels")
                    
                    self.stream = sd.Stream(
                        device=(input_device_id, output_device_id),
                        samplerate=RealTime.RATE,
                        blocksize=RealTime.CHUNK,
                        dtype=np.float32,
                        channels=(channels_in, channels_out),  # Separate channel config for input/output
                        callback=self.audio_callback
                    )
                    self.stream.start()
                    self.is_running = True
                    self.start_button.configure(text="STOP")
                    self.logger.log_info("[INFO] Audio stream started successfully")
                except Exception as e:
                    self.logger.log_error(f"[ERR] Failed to start audio stream: {e}")
        except Exception as err:
            self.logger.log_error(f"[ERR] Error in start function: {err}")

    def upload_audio_enable(self):
        if self.radio_var.get() == 2:
            self.upload_audio_button.configure(state="normal")
            self.generate_button.configure(state="normal")
            # Stop the stream if running
            if self.is_running:
                self.start()  # This will stop the stream since self.is_running is True
            self.logger.log_info("[INFO] Mode: Pre-Record")
        else:
            self.logger.log_info("[INFO] Mode: Realtime")
            self.upload_audio_button.configure(state="disabled")
            self.generate_button.configure(state="disabled")
            self.media_button.configure(state="disabled")
            self.save_audio.configure(state="disabled")

    def media_con(self):
        """Control playback of the modified audio"""
        if self.modified_audio is None or len(self.modified_audio) == 0:
            self.logger.log_warning("[WARN] No modified audio available to play")
            return
            
        if self.is_playing:
            # Stop playback
            try:
                sd.stop()
                self.is_playing = False
                self.media_button.configure(text="⏯")
                self.logger.log_info("[INFO] Playback stopped")
            except Exception as e:
                self.logger.log_error(f"[ERR] Error stopping playback: {e}")
        else:
            # Start playback
            try:
                sd.play(self.modified_audio, RealTime.RATE)
                self.is_playing = True
                self.media_button.configure(text="⏹")
                self.logger.log_info("[INFO] Playing modified audio")
                
                # Update progress bar (basic implementation)
                self.after(100, self.media_progress)
            except Exception as e:
                self.logger.log_error(f"[ERR] Error playing audio: {e}")

    def generate_media(self):
        """Process the uploaded audio file with the selected effects"""
        if not self.filename:
            self.logger.log_warning("[WARN] No audio file selected")
            return
            
        self.logger.log_info("[***] Generating Modified Audio...")
        
        try:
            # Get current settings
            pitch_shift_value = self.pitch.get()
            volume = self.volume.get() / 100.0
            echo_value = self.echo.get() / 100.0
            reverb_value = self.reverb.get() / 100.0
            gate_threshold = self.gate_scale.get() / 100.0
            use_low_cut = self.low_cut_var.get()
            use_high_cut = self.high_cut_var.get()
            
            # Process the audio using PreRec module
            self.modified_audio = PreRec.process_audio(
                self.filename,
                pitch_shift=pitch_shift_value,
                volume=volume,
                echo=echo_value,
                reverb=reverb_value,
                gate_threshold=gate_threshold,
                low_cut=use_low_cut,
                high_cut=use_high_cut
            )
            
            # Enable media controls
            self.media_button.configure(state="normal")
            self.save_audio.configure(state="normal")
            
            self.logger.log_info("[INFO] Audio processing complete")
            
        except Exception as e:
            self.logger.log_error(f"[ERR] Error processing audio: {e}")

    def save_file(self):
        """Save the modified audio to a file"""
        if self.modified_audio is None or len(self.modified_audio) == 0:
            self.logger.log_warning("[WARN] No modified audio to save")
            return
            
        try:
            self.file_loc = filedialog.asksaveasfilename(
                defaultextension=".wav",
                filetypes=[("WAV files", "*.wav")]
            )
            
            if self.file_loc:
                # Use PreRec module to save the audio
                PreRec.save_audio(self.modified_audio, self.file_loc)
                self.logger.log_info(f"[SAVE] Saving File to: {self.file_loc}")
            else:
                self.logger.log_warning("[WARN] Save operation canceled")
                
        except Exception as e:
            self.logger.log_error(f"[ERR] Error saving file: {e}")

    def media_progress(self):
        """Update the media progress bar during playback"""
        if self.is_playing and self.modified_audio is not None:
            try:
                # Get current playback position
                try:
                    current_frame = sd.get_stream().active
                    total_frames = len(self.modified_audio)
                    progress = current_frame / total_frames if total_frames > 0 else 0
                    self.media_progress_bar.set(progress)
                except:
                    # Fallback if we can't get the exact position
                    # This is a simple animation to show something is happening
                    current = self.media_progress_bar.get()
                    if current < 1:
                        self.media_progress_bar.set(current + 0.01)
                    else:
                        self.media_progress_bar.set(0)
                
                # Schedule next update
                if self.is_playing:
                    self.after(100, self.media_progress)
            except Exception as e:
                self.logger.log_error(f"[ERR] Error updating progress: {e}")
                
    def upload_audio_file(self):
        self.filename = filedialog.askopenfilename(
            initialdir=os.getcwd(),
            title="Select Audio file",
            filetypes=(("WAV File", "*.wav"), ("MP3 File", "*.mp3"))
        )
        if self.filename:
            self.logger.log_info(f"[INFO] Selected file: {self.filename}")
            self.generate_button.configure(state="normal")
        else:
            self.logger.log_warning("[WARN] No File Selected")
            self.generate_button.configure(state="disabled")

if __name__ == "__main__":
    app = App()
    app.mainloop()