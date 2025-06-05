# functions/tts/tts_app.py
import streamlit as st
import azure.cognitiveservices.speech as speechsdk
import io
from datetime import datetime
import Functions

def text_to_speech(client):
    # Display header
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1: 
        st.write(" ")
    with col2:
        st.write(" ")
    with col3:
        st.image("Telesure-logo.png", width=200)
    with col4:
        st.write(" ")
    with col5:
        st.write(" ")
    
    st.markdown("<h1 style='text-align: center;'>AI Text To Speech</h1>", unsafe_allow_html=True)
    
    with st.expander("How to use"):
        st.write('''
            Use AI to convert text to natural-sounding speech. Follow these steps:
            
            1. Select a Persona (voice style)
            2. Select the output audio format
            3. Enter the text you want to convert to speech
            4. Click "Generate Speech" to process
            5. Once complete, you can:
               - Listen to the generated audio
               - Download the audio file
            
            For longer texts, the processing may take a few moments.
        ''')
    
    # Persona selection (voice configuration)
    persona_options = {
        "US Female (Aria)": "en-US-AriaNeural",
        "US Male (Guy)": "en-US-GuyNeural",
        "UK Female (Sonia)": "en-GB-SoniaNeural",
        "UK Male (Ryan)": "en-GB-RyanNeural",
        "South African Female (Leah)": "en-ZA-LeahNeural",
        "South African Male (Luke)": "en-ZA-LukeNeural",
        "Australian Female (Natasha)": "en-AU-NatashaNeural",
        "Australian Male (William)": "en-AU-WilliamNeural"
    }
    
    # Format selection
    format_options = {
        "MP3 (Standard Quality)": "mp3",
        "MP3 (High Quality)": "mp3_24k",
        "WAV (Standard Quality)": "wav",
        "WAV (High Quality)": "wav_48k",
        "OGG (Standard Quality)": "ogg",
        "OGG (High Quality)": "ogg_24k",
        "WebM (Standard)": "webm",
        "WebM (High Quality)": "webm_24k"
    }
    
    # UI configuration in the sidebar
    st.sidebar.header("Voice Configuration")
    selected_persona = st.sidebar.selectbox(
        "Select Voice Persona",
        list(persona_options.keys()),
        index=4,  # Default to South African Female
        help="Choose the voice style for your audio"
    )
    
    selected_format = st.sidebar.selectbox(
        "Select Output Format",
        list(format_options.keys()),
        index=1,  # Default to MP3 High Quality
        help="Choose the audio file format and quality"
    )
    
    # Voice customization
    st.sidebar.header("Voice Style (Optional)")
    voice_style = st.sidebar.selectbox(
        "Voice Style",
        ["Default", "Cheerful", "Sad", "Excited", "Friendly", "Terrified", "Angry", "Gentle"],
        index=0,
        help="Apply emotional styling to the voice"
    )
    
    speech_rate = st.sidebar.slider(
        "Speech Rate", 
        min_value=0.5, 
        max_value=2.0, 
        value=1.0, 
        step=0.1,
        help="Adjust how fast the speech is generated (1.0 is normal speed)"
    )
    
    # Main content - Text input
    st.subheader("Enter Text to Convert")
    text_input = st.text_area(
        "Type or paste text here",
        height=200,
        placeholder="Enter the text you want to convert to speech...",
        help="Maximum length: approximately 5000 characters for best results"
    )
    
    # Generate speech button
    if st.button("Generate Speech", type="primary", disabled=not text_input):
        # Check if text is provided
        if not text_input.strip():
            st.warning("Please enter some text to convert to speech.")
            return
        
        # Display processing message
        with st.spinner("Generating speech..."):
            # Create timestamp for filename (used only for downloads)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            try:
                # Get selected voice and format
                voice_name = persona_options[selected_persona]
                audio_format = format_options[selected_format]
                
                # Call the speech synthesis function
                result, audio_bytes, audio_extension = synthesize_speech_in_memory(
                    text_input, 
                    audio_format, 
                    voice_name,
                    voice_style if voice_style != "Default" else None,
                    speech_rate
                )
                
                if result:
                    # Success message
                    st.success("🎉 Speech generated successfully!")
                    
                    # Display audio player
                    st.subheader("Listen to Generated Speech")
                    
                    # Determine MIME type based on format
                    if "mp3" in audio_format:
                        mime_type = "audio/mpeg"  # More widely supported than audio/mp3
                    elif "wav" in audio_format:
                        mime_type = "audio/wav"
                    elif "ogg" in audio_format:
                        mime_type = "audio/ogg"
                    elif "webm" in audio_format:
                        mime_type = "audio/webm"
                    else:
                        mime_type = "audio/mpeg"  # Default fallback
                    
                    # Display audio player
                    st.audio(audio_bytes, format=mime_type)
                    
                    # Create download button
                    download_filename = f"speech_audio_{timestamp}.{audio_extension}"
                    
                    st.download_button(
                        label=f"Download {audio_extension.upper()} File",
                        data=audio_bytes,
                        file_name=download_filename,
                        mime=mime_type
                    )
                    
                    # Display file info
                    file_size_kb = len(audio_bytes) / 1024
                    st.info(f"File Size: {file_size_kb:.2f} KB | Format: {audio_extension.upper()} | Voice: {selected_persona}")
                else:
                    st.error("Failed to generate speech. Please try again with different text or settings.")
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.info("Please try again with shorter text or different settings.")

def synthesize_speech_in_memory(text, audio_format="mp3", voice_name=None, style=None, rate=1.0):
    """
    Synthesize speech and keep the audio data in memory using AudioDataStream
    
    Args:
        text (str): Text to synthesize
        audio_format (str): Audio format - 'wav', 'mp3', 'ogg', etc.
        voice_name (str): Voice name to use
        style (str): Voice style (emotional styling)
        rate (float): Speech rate (0.5-2.0)
        
    Returns:
        tuple: (success_bool, audio_bytes, file_extension)
    """
    
    # Configuration
    speech_key = Functions.stt_api_key  # Use the speech-to-text key for TTS as well
    service_region = "southafricanorth"  # Azure region
    
    # Create speech config
    speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
    
    # Set voice if specified
    if voice_name:
        speech_config.speech_synthesis_voice_name = voice_name
    else:
        speech_config.speech_synthesis_voice_name = "en-ZA-LeahNeural"  # Default voice
    
    # Audio format configurations
    format_configs = {
        'wav': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
            'extension': 'wav'
        },
        'wav_8k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff8Khz16BitMonoPcm,
            'extension': 'wav'
        },
        'wav_16k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm,
            'extension': 'wav'
        },
        'wav_48k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
            'extension': 'wav'
        },
        'mp3': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,
            'extension': 'mp3'
        },
        'mp3_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,
            'extension': 'mp3'
        },
        'mp3_16k_64k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz64KBitRateMonoMp3,
            'extension': 'mp3'
        },
        'mp3_16k_32k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
            'extension': 'mp3'
        },
        'ogg': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Ogg16Khz16BitMonoOpus,
            'extension': 'ogg'
        },
        'ogg_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Ogg24Khz16BitMonoOpus,
            'extension': 'ogg'
        },
        'webm': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Webm16Khz16BitMonoOpus,
            'extension': 'webm'
        },
        'webm_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Webm24Khz16BitMonoOpus,
            'extension': 'webm'
        },
        'raw': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Raw16Khz16BitMonoPcm,
            'extension': 'raw'
        },
        'raw_24k': {
            'format': speechsdk.SpeechSynthesisOutputFormat.Raw24Khz16BitMonoPcm,
            'extension': 'raw'
        }
    }
    
    # Get format configuration
    if audio_format not in format_configs:
        print(f"Unsupported format: {audio_format}")
        print(f"Available formats: {list(format_configs.keys())}")
        return False, None, None
    
    format_config = format_configs[audio_format]
    
    # Set audio output format
    speech_config.set_speech_synthesis_output_format(format_config['format'])
    
    # Create synthesizer without audio config (will use stream output)
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
    
    # Prepare SSML with style and rate if specified
    if style or rate != 1.0:
        ssml_text = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="{speech_config.speech_synthesis_voice_name}">
                <prosody rate="{rate}">
                    {f'<mstts:express-as style="{style}">' if style else ''}
                    {text}
                    {f'</mstts:express-as>' if style else ''}
                </prosody>
            </voice>
        </speak>
        """
        result = speech_synthesizer.speak_ssml_async(ssml_text).get()
    else:
        # Synthesize speech using plain text
        result = speech_synthesizer.speak_text_async(text).get()
    
    # Check result
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        try:
            # Create an audio data stream from the result
            audio_data_stream = speechsdk.AudioDataStream(result)
            
            # Create a memory buffer to hold the audio data
            audio_buffer = io.BytesIO()
            
            # IMPROVED: Using a simpler, more robust chunking approach
            # We'll use the same approach for all formats
            buffer_size = 4096  # 4KB buffer is enough
            
            # Make sure we're at the beginning of the stream
            audio_data_stream.seek_to_beginning()
            
            # Read audio data in chunks
            total_bytes_read = 0
            while True:
                # Create a new chunk buffer for each read
                chunk = bytearray(buffer_size)
                bytes_read = audio_data_stream.read_data(chunk)
                
                if bytes_read == 0:
                    break  # End of stream
                
                # Write only the valid portion of the chunk
                audio_buffer.write(chunk[:bytes_read])
                total_bytes_read += bytes_read
            
            # If we read any data
            if total_bytes_read > 0:
                # Reset buffer position to beginning
                audio_buffer.seek(0)
                audio_bytes = audio_buffer.getvalue()
                
                # Return success, audio bytes, and file extension
                return True, audio_bytes, format_config['extension']
            else:
                print("No audio data was read from the stream")
                return False, None, None
                
        except Exception as e:
            print(f"Error processing audio data: {e}")
            return False, None, None
            
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {cancellation_details.error_details}")
        return False, None, None
    
    return False, None, None
