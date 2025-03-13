import numpy as np
import librosa
import soundfile as sf
import RealTime
import os
from scipy import signal

class AudioProcessingTask:
    """Class to track audio processing progress"""
    def __init__(self):
        self.progress = 0.0
        self.is_canceled = False
        self.is_complete = False
        self.result = None
        self.error = None

    def update_progress(self, value):
        """Update progress value (0-1)"""
        self.progress = value
        
    def cancel(self):
        """Cancel the processing task"""
        self.is_canceled = True
        
    def complete(self, result):
        """Mark task as complete with result"""
        self.result = result
        self.is_complete = True
        self.progress = 1.0
        
    def fail(self, error):
        """Mark task as failed with error"""
        self.error = error
        self.is_complete = True

def process_audio(file_path, pitch_shift=0, volume=1.0, echo=0, reverb=0, 
                  gate_threshold=0.1, low_cut=True, high_cut=True, 
                  callback=None, task=None):
    """
    Process pre-recorded audio file with effects
    """
    try:
        # Create task object if not provided
        if task is None:
            task = AudioProcessingTask()
            
        # Update progress
        task.update_progress(0.1)
        if callback:
            callback("Loading audio file...")
            
        # Load audio file
        audio_data, sample_rate = librosa.load(file_path, sr=RealTime.RATE)
        
        # Update progress
        task.update_progress(0.3)
        if callback:
            callback("Applying effects...")
            
        # Apply noise gate if threshold > 0
        if gate_threshold > 0:
            audio_data = RealTime.noise_gate(audio_data, gate_threshold)
            
        # Apply filters
        filters = RealTime.init_filter()
        audio_data = RealTime.apply_filter(audio_data, filters, low_cut, high_cut)
        
        # Update progress
        task.update_progress(0.5)
        if task.is_canceled:
            return None
            
        # Apply pitch shift if not zero
        if pitch_shift != 0:
            if callback:
                callback("Shifting pitch...")
            audio_data = RealTime.pitch_shift(audio_data, RealTime.RATE, pitch_shift)
            
        # Update progress
        task.update_progress(0.7)
        if task.is_canceled:
            return None
            
        # Apply echo if > 0
        if echo > 0:
            if callback:
                callback("Adding echo...")
            audio_data = RealTime.add_echo(audio_data, echo)
            
        # Apply reverb if > 0
        if reverb > 0:
            if callback:
                callback("Adding reverb...")
            audio_data = RealTime.add_reverb(audio_data, reverb)
            
        # Apply volume
        audio_data = audio_data * volume
        
        # Update progress
        task.update_progress(0.9)
        if callback:
            callback("Finalizing...")
            
        # Normalize to prevent clipping
        if np.max(np.abs(audio_data)) > 0.99:
            audio_data = audio_data / np.max(np.abs(audio_data)) * 0.99
            
        # Mark task as complete
        task.complete(audio_data)
        if callback:
            callback("Processing complete")
            
        return audio_data
        
    except Exception as e:
        if task:
            task.fail(str(e))
        if callback:
            callback(f"Error: {e}")
        raise e

def save_audio(audio_data, file_path, callback=None):
    """
    Save processed audio to a file
    """
    try:
        if callback:
            callback("Saving audio file...")
            
        # Write to file
        sf.write(file_path, audio_data, RealTime.RATE)
        
        if callback:
            callback(f"File saved: {file_path}")
            
        return True
    except Exception as e:
        if callback:
            callback(f"Error saving file: {e}")
        return False

def get_audio_info(file_path):
    """
    Get information about an audio file
    """
    try:
        # Load audio file metadata
        info = sf.info(file_path)
        
        # Get additional info with librosa
        audio_data, sample_rate = librosa.load(file_path, sr=None)
        
        return {
            'duration': info.duration,
            'sample_rate': info.samplerate,
            'channels': info.channels,
            'format': info.format,
            'file_size': os.path.getsize(file_path),
            'max_amplitude': np.max(np.abs(audio_data)),
            'min_amplitude': np.min(np.abs(audio_data)),
            'avg_amplitude': np.mean(np.abs(audio_data))
        }
        
    except Exception as e:
        print(f"Error getting audio info: {e}")
        return None

def get_pitch_detection(file_path):
    """
    Detect the pitch of an audio file
    """
    try:
        # Load audio
        audio_data, sample_rate = librosa.load(file_path, sr=RealTime.RATE)
        
        # Calculate pitch using librosa
        pitches, magnitudes = librosa.piptrack(y=audio_data, sr=sample_rate)
        
        # Find the highest magnitude for each frame
        pitch_values = []
        for i in range(pitches.shape[1]):
            index = magnitudes[:, i].argmax()
            pitch = pitches[index, i]
            if pitch > 0:  # Ignore zero pitch (silence)
                pitch_values.append(pitch)
                
        # Return average pitch or 0 if no pitch detected
        if pitch_values:
            return np.mean(pitch_values)
        else:
            return 0
            
    except Exception as e:
        print(f"Error detecting pitch: {e}")
        return 0

def batch_process(file_list, output_dir, pitch_shift=0, volume=1.0, echo=0, reverb=0, 
                  gate_threshold=0.1, low_cut=True, high_cut=True, callback=None):
    """
    Process multiple audio files with the same settings
    """
    successful_files = []
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    total_files = len(file_list)
    for i, file_path in enumerate(file_list):
        file_name = os.path.basename(file_path)
        output_file = os.path.join(output_dir, f"processed_{file_name}")
        
        if callback:
            callback(f"Processing file {i+1}/{total_files}: {file_name}")
            
        try:
            # Process the file
            audio_data = process_audio(
                file_path,
                pitch_shift=pitch_shift,
                volume=volume,
                echo=echo,
                reverb=reverb,
                gate_threshold=gate_threshold,
                low_cut=low_cut,
                high_cut=high_cut
            )
            
            # Save the processed file
            sf.write(output_file, audio_data, RealTime.RATE)
            
            successful_files.append(output_file)
            
            if callback:
                callback(f"Successfully processed: {file_name}")
                
        except Exception as e:
            if callback:
                callback(f"Error processing {file_name}: {e}")
    
    return successful_files

if __name__ == "__main__":
    # Example usage
    def print_progress(message):
        print(message)
        
    # Test processing a single file
    try:
        test_file = "sample-audio.wav"
        processed = process_audio(
            test_file,
            pitch_shift=2,
            volume=0.8,
            echo=0.3,
            reverb=0.2,
            callback=print_progress
        )
        
        # Save the processed audio
        save_audio(processed, "sample-audio.wav", print_progress)
        
        # Get audio info
        info = get_audio_info(test_file)
        print("Audio Info:", info)
        
    except Exception as e:
        print(f"Test failed: {e}")