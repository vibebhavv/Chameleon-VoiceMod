import numpy as np
import scipy.signal as signal
from scipy.io import wavfile
import librosa
import librosa.effects
import soundfile as sf

# Audio parameters
RATE = 44100  # Sample rate
CHUNK = 1024  # Buffer size

def init_filter():
    """Initialize filters for low and high cut"""
    filters = {
        'low_cut': {
            'b': signal.firwin(101, 300, fs=RATE, pass_zero=False),
            'a': 1,
        },
        'high_cut': {
            'b': signal.firwin(101, 3000, fs=RATE),
            'a': 1,
        }
    }
    return filters

def noise_gate(audio_data, threshold):
    """
    Apply a noise gate to the audio to remove background noise
    """
    # Calculate the absolute values
    abs_data = np.abs(audio_data)
    
    # Calculate the RMS (root mean square) level
    rms = np.sqrt(np.mean(abs_data**2))
    
    # Normalize the threshold against the maximum possible amplitude
    normalized_threshold = threshold * np.max(abs_data) if np.max(abs_data) > 0 else threshold
    
    # Create a mask for values below the threshold
    mask = abs_data < normalized_threshold
    
    # Apply the gate
    gated_data = audio_data.copy()
    gated_data[mask] = 0
    
    return gated_data

def apply_filter(audio_data, filters, use_low_cut=True, use_high_cut=True):
    """
    Apply low-cut and high-cut filters to the audio
    """
    filtered_data = audio_data.copy()
    
    # Apply low-cut filter (removes low frequencies)
    if use_low_cut:
        filtered_data = signal.lfilter(
            filters['low_cut']['b'],
            filters['low_cut']['a'],
            filtered_data
        )
    
    # Apply high-cut filter (removes high frequencies)
    if use_high_cut:
        filtered_data = signal.lfilter(
            filters['high_cut']['b'],
            filters['high_cut']['a'],
            filtered_data
        )
    
    return filtered_data

def pitch_shift(audio_data, sample_rate, n_steps):
    """
    Shift the pitch of the audio
    """
    # Using librosa for pitch shifting
    # Convert to float32 if not already
    audio_float = audio_data.astype(np.float32)
    
    # Check if audio is too short for default n_fft
    if len(audio_float) < 2048:
        # Use a smaller n_fft value
        n_fft = 1024
        while n_fft > len(audio_float) and n_fft > 64:
            n_fft = n_fft // 2
        
        # Apply pitch shift with custom n_fft
        shifted = librosa.effects.pitch_shift(
            y=audio_float,
            sr=sample_rate,
            n_steps=n_steps,
            bins_per_octave=12,
            n_fft=n_fft
        )
    else:
        # Apply standard pitch shift
        shifted = librosa.effects.pitch_shift(
            y=audio_float,
            sr=sample_rate,
            n_steps=n_steps,
            bins_per_octave=12
        )
    
    return shifted

def add_echo(audio_data, echo_strength):
    # Calculate delay samples (about 200ms)
    delay_samples = int(RATE * 0.2)
    
    # Calculate decay factor based on echo strength
    decay = 0.5 * echo_strength
    
    # Create a delayed version of the audio
    if len(audio_data) > delay_samples:
        # Create padded arrays
        original = np.pad(audio_data, (0, delay_samples), 'constant')
        delayed = np.pad(audio_data, (delay_samples, 0), 'constant')
        
        # Mix original and delayed signals
        result = original + delayed * decay
        
        # Normalize to prevent clipping
        if np.max(np.abs(result)) > 0:
            result = result / np.max(np.abs(result))
        
        # Return the part that matches the original length
        return result[:len(audio_data)]
    else:
        return audio_data

def add_reverb(audio_data, reverb_amount):
    """
    Add a simple reverb effect to audio data
    """
    # Determine delay in samples (e.g., 100ms at 44.1kHz)
    delay_samples = int(0.1 * 44100)
    
    # Create output array (same length as input)
    output = np.copy(audio_data)
    
    # Create a few delays with decreasing amplitude
    for i in range(1, 5):
        # Calculate delay position and amplitude
        delay_pos = i * delay_samples
        amplitude = reverb_amount * (0.7 ** i)  # Exponential decay
        
        # Add delayed signal to the output, but only where it fits
        if delay_pos < len(audio_data):
            # Add the delayed signal up to where it fits
            max_copy = len(audio_data) - delay_pos
            output[delay_pos:] += audio_data[:max_copy] * amplitude
    
    # Normalize if needed to prevent clipping
    if np.max(np.abs(output)) > 1.0:
        output = output / np.max(np.abs(output))
        
    return output

def apply_volume(audio_data, volume):
    """
    Adjust the volume of the audio
    """
    return audio_data * volume

def process_audio(audio_data, pitch_shift_value=0, volume=1.0, echo=0, reverb=0, 
                  gate_threshold=0.1, low_cut=True, high_cut=True):
    """
    Process audio data with all effects in one go
    """
    # Get filters
    filters = init_filter()
    
    # Apply noise gate
    processed = noise_gate(audio_data, gate_threshold)
    
    # Apply filters
    processed = apply_filter(processed, filters, low_cut, high_cut)
    
    # Apply pitch shift
    if pitch_shift_value != 0:
        processed = pitch_shift(processed, RATE, pitch_shift_value)
    
    # Apply echo
    if echo > 0:
        processed = add_echo(processed, echo)
    
    # Apply reverb
    if reverb > 0:
        processed = add_reverb(processed, reverb)
    
    # Apply volume
    processed = apply_volume(processed, volume)
    
    return processed

def save_processed_audio(input_file, output_file, pitch_shift_value=0, volume=1.0, 
                         echo=0, reverb=0, gate_threshold=0.1, low_cut=True, high_cut=True):
    """
    Process an audio file and save the result
    """
    try:
        # Load audio file
        audio_data, sample_rate = librosa.load(input_file, sr=RATE)
        
        # Process audio
        processed = process_audio(
            audio_data,
            pitch_shift_value,
            volume,
            echo,
            reverb,
            gate_threshold,
            low_cut,
            high_cut
        )
        
        # Save processed audio
        sf.write(output_file, processed, RATE)
        
        return True
    except Exception as e:
        print(f"Error processing file: {e}")
        return False

# Function to test real-time audio processing
def test_processing():
    """Test audio processing functions with a sample WAV file"""
    # Load a test file
    try:
        # You can replace this with any test WAV file
        test_file = "sample-audio.wav"
        audio_data, sample_rate = librosa.load(test_file, sr=RATE)
        
        # Process with some test settings
        processed = process_audio(
            audio_data,
            pitch_shift_value=2,  # Shift up 2 semitones
            volume=0.8,
            echo=0.3,
            reverb=0.2,
            gate_threshold=0.1,
            low_cut=True,
            high_cut=True
        )
        
        # Save the result
        sf.write("sample-audio.wav", processed, RATE)
        
        print("Test processing complete. Output saved to test_processed.wav")
    except Exception as e:
        print(f"Test processing failed: {e}")

if __name__ == "__main__":
    test_processing()