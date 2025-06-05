import streamlit as st
from openai import AzureOpenAI
import os
from PIL import Image
import requests
from io import BytesIO
import base64
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Predefined style guides
STYLE_GUIDES = {
    "Photorealistic": "Create a photorealistic image with natural lighting, detailed textures, and real-world accuracy",
    "Digital Art": "Create a digital art piece with vibrant colors, clean lines, and modern styling",
    "Oil Painting": "Create an oil painting style image with visible brushstrokes, rich colors, and classical composition",
    "Anime": "Create an anime-style illustration with characteristic styling, clean lines, and expressive features",
    "Watercolor": "Create a watercolor style image with soft edges, transparent colors, and gentle blending",
    "3D Render": "Create a 3D rendered image with perfect lighting, smooth surfaces, and realistic materials",
    "Minimalist": "Create a minimalist design with simple shapes, limited color palette, and clean composition",
    "Fantasy": "Create a fantasy-style illustration with magical elements, dramatic lighting, and otherworldly atmosphere"
}

def enhance_prompt(prompt, style_guide="", additional_instructions=""):
    """
    Enhanced prompt generation with style guidance and custom instructions.
    """
    try:
        system_message = """You are an expert at crafting detailed image generation prompts. 
        Your task is to enhance user prompts to create high-quality, detailed images using DALL-E 3.
        
        Consider these aspects in your enhancement:
        - Composition: Rule of thirds, focal points, perspective
        - Lighting: Direction, intensity, atmosphere
        - Color palette: Complementary colors, mood
        - Texture and materials
        - Depth and dimensionality
        - Atmosphere and mood
        - Scale and proportions
        
        IMPORTANT RULES:
        - NEVER include instructions for text or writing
        - Focus on visual elements and artistic style
        - Maintain the original intent while adding detail
        - Be specific about visual attributes
        - Include lighting and atmosphere details
        """

        # Combine user input with style guide and additional instructions
        full_prompt = f"{prompt}"
        if style_guide:
            full_prompt = f"{full_prompt}. {style_guide}"
        if additional_instructions:
            full_prompt = f"{full_prompt}. {additional_instructions}"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Enhance this prompt for image generation: {full_prompt}"}
        ]

        response = client.chat.completions.create(
            model="gpt4o",
            messages=messages,
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        st.error("An error occurred while enhancing the prompt. Please try again.")
        raise e

def generate_image(prompt):
    """
    Generate image with error handling and quality settings.
    """
    try:
        response = client.images.generate(
            model="Dalle3",
            prompt=prompt,
            size="1024x1024",
            quality="hd",  # Using HD quality for better results
            n=1,
            style="vivid"  # Using vivid style for more striking images
        )
        
        return response.data[0].url
    
    except Exception as e:
        error_message = str(e).lower()
        if any(keyword in error_message for keyword in ['content_policy', 'safety', 'policy', 'violated']):
            st.error("Whoops! That image cannot be generated as it triggers content filters. Please rephrase your prompt and avoid any famous character or copyright references.")
        else:
            st.error("An unexpected error occurred while generating the image. Please try again.")
        raise e

def main():
    st.title("Advanced AI Image Generator")
    
    # Initialize session state
    if 'generation_history' not in st.session_state:
        st.session_state.generation_history = []
    if 'current_prompt' not in st.session_state:
        st.session_state.current_prompt = ""
    if 'image_url' not in st.session_state:
        st.session_state.image_url = None
    if 'feedback_data' not in st.session_state:
        st.session_state.feedback_data = {}

    # Sidebar for style selection and additional controls
    with st.sidebar:
        st.header("Image Style Controls")
        
        # Style selection
        selected_style = st.selectbox(
            "Choose Art Style",
            list(STYLE_GUIDES.keys()),
            help="Select a base style for your image"
        )

        # Advanced controls
        st.subheader("Fine-tune Your Image")
        mood = st.select_slider(
            "Mood",
            options=["Dark", "Neutral", "Bright"],
            value="Neutral"
        )
        
        detail_level = st.select_slider(
            "Detail Level",
            options=["Simple", "Balanced", "Complex"],
            value="Balanced"
        )

        # Composition guidance
        composition = st.selectbox(
            "Composition",
            ["Centered", "Rule of Thirds", "Dynamic", "Symmetrical"]
        )

    # Main content area
    st.subheader("Create Your Image")

    # Input area with guidance
    prompt_placeholder = "Describe what you want to see in the image..."
    prompt_help = "Tip: Be specific about colors, lighting, and important details"
    
    prompt = st.text_area(
        "Enter your prompt:",
        placeholder=prompt_placeholder,
        help=prompt_help,
        height=100
    )

    # Additional instructions
    with st.expander("Additional Instructions (Optional)"):
        additional_instructions = st.text_area(
            "Add specific details about:",
            placeholder="Lighting, colors, textures, perspective, etc.",
            height=100
        )

    # Generate button with style information
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.button("Generate Image", type="primary"):
            try:
                with st.spinner("Creating your image..."):
                    # Combine style guide with mood and composition
                    style_instruction = f"{STYLE_GUIDES[selected_style]}. {mood} mood. {composition} composition. {detail_level} detail level."
                    
                    # Enhance and generate
                    enhanced_prompt = enhance_prompt(prompt, style_instruction, additional_instructions)
                    image_url = generate_image(enhanced_prompt)
                    
                    # Store in session state
                    st.session_state.current_prompt = enhanced_prompt
                    st.session_state.image_url = image_url
                    
                    # Add to history
                    st.session_state.generation_history.append({
                        'prompt': prompt,
                        'enhanced_prompt': enhanced_prompt,
                        'style': selected_style,
                        'settings': {
                            'mood': mood,
                            'detail_level': detail_level,
                            'composition': composition
                        },
                        'image_url': image_url
                    })

            except Exception:
                return

    # Display current image and feedback
    if st.session_state.image_url:
        st.image(st.session_state.image_url)
        
        # Feedback section
        st.subheader("Image Feedback")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            satisfaction = st.select_slider(
                "How satisfied are you with this image?",
                options=["Very Unsatisfied", "Unsatisfied", "Neutral", "Satisfied", "Very Satisfied"],
                value="Neutral"
            )
        
        with col2:
            aspects = st.multiselect(
                "What aspects need improvement?",
                ["Composition", "Colors", "Style", "Details", "Lighting", "Overall Quality"]
            )
        
        with col3:
            feedback_text = st.text_input("Additional feedback (optional)")

        if st.button("Submit Feedback"):
            st.session_state.feedback_data[st.session_state.image_url] = {
                'satisfaction': satisfaction,
                'aspects': aspects,
                'feedback': feedback_text
            }
            st.success("Thank you for your feedback!")

    # History viewer
    if st.session_state.generation_history:
        with st.expander("View Generation History"):
            for i, entry in enumerate(reversed(st.session_state.generation_history)):
                st.write(f"Generation {len(st.session_state.generation_history) - i}")
                st.write(f"Style: {entry['style']}")
                st.write(f"Settings: {entry['settings']}")
                st.write("Original Prompt:", entry['prompt'])
                st.write("Enhanced Prompt:", entry['enhanced_prompt'])
                st.image(entry['image_url'], width=300)
                st.divider()

if __name__ == "__main__":
    main()