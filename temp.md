'''
  Azure Speech SDK - Text to Speech with Audio File Download
  For more samples please visit https://github.com/Azure-Samples/cognitive-services-speech-sdk
'''

import azure.cognitiveservices.speech as speechsdk
import os

def synthesize_speech_to_file(text, output_file, audio_format="wav", voice_name=None):
    """
    Synthesize speech and save to file in specified format
    
    Args:
        text (str): Text to synthesize
        output_file (str): Output file path (without extension)
        audio_format (str): Audio format - 'wav', 'mp3', 'ogg', 'silk', 'raw'
        voice_name (str): Voice name to use
    """
    
    # Configuration
    speech_key = os.environ.get("tts_key")  # Replace with your subscription key
    service_region = "southafricanorth"
    
    # Create speech config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    
    # Set voice if specified
    if voice_name:
        speech_config.speech_synthesis_voice_name = voice_name
    else:
        speech_config.speech_synthesis_voice_name = "en-US-AriaNeural"  # Default voice
    
    # Audio format configurations (using correct Azure Speech SDK format names)
    format_configs = {
        'wav': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
            'extension': '.wav'
        },
        'wav_8k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff8Khz16BitMonoPcm,
            'extension': '.wav'
        },
        'wav_16k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
            'extension': '.wav'
        },
        'wav_48k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
            'extension': '.wav'
        },
        'mp3': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,  # Fixed: KBit not Kbit
            'extension': '.mp3'
        },
        'mp3_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,  # Fixed: KBit not Kbit
            'extension': '.mp3'
        },
        'mp3_16k_64k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3,   # Fixed: KBit not Kbit
            'extension': '.mp3'
        },
        'mp3_16k_32k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,   # Fixed: KBit not Kbit
            'extension': '.mp3'
        },
        'ogg': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
            'extension': '.ogg'
        },
        'ogg_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Ogg24Khz16BitMonoOpus,
            'extension': '.ogg'
        },
        'webm': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Webm16Khz16BitMonoOpus,
            'extension': '.webm'
        },
        'webm_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Webm24Khz16BitMonoOpus,
            'extension': '.webm'
        },
        'raw': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm,
            'extension': '.raw'
        },
        'raw_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm,
            'extension': '.raw'
        }
    }
    
    # Get format configuration
    if audio_format not in format_configs:
        print(f"Unsupported format: {audio_format}")
        print(f"Available formats: {list(format_configs.keys())}")
        return False
    
    format_config = format_configs[audio_format]
    
    # Set audio output format
    speech_config.set_speech_synthesis_output_format(format_config['format'])
    
    # Create output file path with appropriate extension
    output_path = output_file + format_config['extension']
    
    # Create audio output config for file
    audio_config = speechsdk.audio.AudioOutputConfig(filename=output_path)
    
    # Create synthesizer
    speech_synthesizer = speechsdk.SpeechSynthesizer(
        speech_config=speech_config, 
        audio_config=audio_config
    )
    
    print(f"Synthesizing text: '{text}'")
    print(f"Output file: {output_path}")
    print(f"Format: {audio_format}")
    print(f"Voice: {speech_config.speech_synthesis_voice_name}")
    
    # Synthesize speech
    result = speech_synthesizer.speak_text_async(text).get()
    
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print(f"✅ Speech synthesized successfully!")
        print(f"📁 Audio saved to: {output_path}")
        print(f"📊 File size: {os.path.getsize(output_path)} bytes")
        return True
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"❌ Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"🔴 Error details: {cancellation_details.error_details}")
        return False
    
    return False

def list_available_formats():
    """
    List all available audio formats
    """
    formats = {
        'WAV Formats': ['wav', 'wav_8k', 'wav_16k', 'wav_48k'],
        'MP3 Formats': ['mp3', 'mp3_24k', 'mp3_16k_64k', 'mp3_16k_32k'],
        'OGG Formats': ['ogg', 'ogg_24k'],
        'WebM Formats': ['webm', 'webm_24k'],
        'Raw Formats': ['raw', 'raw_24k']
    }
    
    print("📋 Available Audio Formats:")
    print("=" * 40)
    for category, fmt_list in formats.items():
        print(f"\n🎵 {category}:")
        for fmt in fmt_list:
            print(f"   - {fmt}")
    print("\n" + "=" * 40)

def synthesize_multiple_formats(text, base_filename, formats=None, voice_name=None):
    """
    Synthesize speech in multiple formats
    
    Args:
        text (str): Text to synthesize
        base_filename (str): Base filename (without extension)
        formats (list): List of formats to generate
        voice_name (str): Voice name to use
    """
    if formats is None:
        formats = ['wav', 'mp3', 'ogg']
    
    print(f"🎙️  Generating audio in {len(formats)} formats...")
    print("-" * 50)
    
    success_count = 0
    for fmt in formats:
        print(f"\n🔄 Processing format: {fmt}")
        if synthesize_speech_to_file(text, base_filename, fmt, voice_name):
            success_count += 1
        print("-" * 30)
    
    print(f"\n✨ Summary: {success_count}/{len(formats)} files generated successfully!")

# Example usage
if __name__ == "__main__":
    # List available formats first
    list_available_formats()
    
    # Text to synthesize
    sample_text = "Hello! This is a demonstration of Azure Speech Services with file download capabilities."
    
    # Example 1: Single format
    print("\n=== Single Format Example ===")
    synthesize_speech_to_file(
        text=sample_text,
        output_file="output_speech",
        audio_format="mp3_24k",
        voice_name="en-ZA-LeahNeural" #"en-ZA-LeahNeural", "en-ZA-LukeNeural" 
    )
    
    print("\n" + "="*60 + "\n")
    
   
    print("\n🎉 All audio files have been generated!")
    print("📁 Check your current directory for the output files.")
