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
    
    # Simplified format selection - focusing on browser-compatible formats
    format_options = {
        "MP3 (Recommended)": "mp3",
        "WAV (High Quality)": "wav",
        "MP3 (High Quality)": "mp3_hq",
        "WAV (Standard)": "wav_std"
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
        index=0,  # Default to MP3 (Recommended)
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
                result, audio_bytes, audio_extension, mime_type = synthesize_speech_in_memory(
                    text_input, 
                    audio_format, 
                    voice_name,
                    voice_style if voice_style != "Default" else None,
                    speech_rate
                )
                
                if result and audio_bytes:
                    # Success message
                    st.success("🎉 Speech generated successfully!")
                    
                    # Display audio player
                    st.subheader("Listen to Generated Speech")
                    
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
    Synthesize speech and keep the audio data in memory
    
    Args:
        text (str): Text to synthesize
        audio_format (str): Audio format - 'wav', 'mp3', etc.
        voice_name (str): Voice name to use
        style (str): Voice style (emotional styling)
        rate (float): Speech rate (0.5-2.0)
        
    Returns:
        tuple: (success_bool, audio_bytes, file_extension, mime_type)
    """
    
    try:
        # Configuration
        speech_key = Functions.stt_api_key
        service_region = "southafricanorth"
        
        # Create speech config
        speech_config = speechsdk.SpeechConfig(subscription=speech_key, region=service_region)
        
        # Set voice if specified
        if voice_name:
            speech_config.speech_synthesis_voice_name = voice_name
        else:
            speech_config.speech_synthesis_voice_name = "en-ZA-LeahNeural"
        
        # Audio format configurations - simplified and tested
        format_configs = {
            'mp3': {
                'format': speechsdk.SpeechSynthesisOutputFormat.Audio16Khz128KBitRateMonoMp3,
                'extension': 'mp3',
                'mime_type': 'audio/mpeg'
            },
            'mp3_hq': {
                'format': speechsdk.SpeechSynthesisOutputFormat.Audio24Khz160KBitRateMonoMp3,
                'extension': 'mp3',
                'mime_type': 'audio/mpeg'
            },
            'wav': {
                'format': speechsdk.SpeechSynthesisOutputFormat.Riff48Khz16BitMonoPcm,
                'extension': 'wav',
                'mime_type': 'audio/wav'
            },
            'wav_std': {
                'format': speechsdk.SpeechSynthesisOutputFormat.Riff24Khz16BitMonoPcm,
                'extension': 'wav',
                'mime_type': 'audio/wav'
            }
        }
        
        # Get format configuration
        if audio_format not in format_configs:
            print(f"Unsupported format: {audio_format}")
            return False, None, None, None
        
        format_config = format_configs[audio_format]
        
        # Set audio output format
        speech_config.set_speech_synthesis_output_format(format_config['format'])
        
        # Create synthesizer without audio config (will use result.audio_data)
        speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=None)
        
        # Prepare SSML with style and rate if specified
        if style or rate != 1.0:
            # Clean the text to avoid XML issues
            clean_text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            
            ssml_text = f"""
            <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xml:lang="en-US">
                <voice name="{speech_config.speech_synthesis_voice_name}">
                    <prosody rate="{rate}">
                        {f'<mstts:express-as style="{style}">' if style else ''}
                        {clean_text}
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
            # IMPROVED: Direct access to audio data
            audio_bytes = result.audio_data
            
            if audio_bytes and len(audio_bytes) > 0:
                return True, audio_bytes, format_config['extension'], format_config['mime_type']
            else:
                print("No audio data received")
                return False, None, None, None
                
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print(f"Speech synthesis canceled: {cancellation_details.reason}")
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print(f"Error details: {cancellation_details.error_details}")
            return False, None, None, None
        
        return False, None, None, None
        
    except Exception as e:
        print(f"Exception in synthesize_speech_in_memory: {e}")
        return False, None, None, None
