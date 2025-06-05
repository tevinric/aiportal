import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import io

def generate_text_content(data):
    """Generate formatted text content in memory"""
    lines = [
        "Vehicle License Disc Information",
        "==============================\n"
    ]
    for key, value in data.items():
        lines.append(f"{key}: {value}")
    return "\n".join(lines)

def display_image_preview(uploaded_file):
    """Display image preview with error handling"""
    try:
        # Read the uploaded file
        image_bytes = uploaded_file.read()
        uploaded_file.seek(0)
        
        # Check if it's a PDF
        if uploaded_file.type == "application/pdf":
            st.warning("PDF preview not available. File will still be processed.")
            return image_bytes
            
        # Open and display image
        image = Image.open(io.BytesIO(image_bytes))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(" ")
        with col2:
            st.image(image, caption="Document Preview", use_container_width=True)
        with col3:
            st.write(" ")
        
        return image_bytes
        
    except Exception as e:
        st.error(f"Error displaying image preview: {str(e)}")
        return None

def display_results(data):
    """Display extracted results in a neat format"""
    # Group related fields
    groups = {
        "Vehicle Information": {
            "Make": data.get("Make", ""),
            "Description": data.get("Description/Beskrywing", ""),
            "VIN": data.get("VIN", ""),
            "Engine Number": data.get("Engine no./Enjinnr.", ""),
            "Vehicle Register Number": data.get("Veh. register no./Vrt.registerer.", "")
        },
        "License Information": {
            "RSA Number": data.get("RSA NO.", ""),
            "License Number": data.get("License no./Lisensienr.", ""),
            "Expiry Date": data.get("Date of expiry/Vervaldatum", ""),
            "Fees": data.get("Fees/Gelde", "")
        },
        "Vehicle Specifications": {
            "GVM": data.get("GVM/PVM", ""),
            "Tare": data.get("Tare/Tarra", ""),
            "Total Persons": data.get("Persons/Personne", ""),
            "Seated": data.get("Seated/Sittende", "")
        }
    }
    
    # Display each group in an expander
    for group_name, fields in groups.items():
        with st.expander(f"📋 {group_name}", expanded=True):
            # Create two columns for each field
            for field_name, value in fields.items():
                col1, col2 = st.columns([1, 2])
                col1.write(f"**{field_name}:**")
                col2.write(value)

def ocr_vehicle_license():
    st.title("Vehicle License Disc OCR")
    
    # Upload Section
    st.write("### Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a vehicle license disc document",
        type=['png', 'jpg', 'jpeg', 'pdf', 'tiff'],
        help="Supported formats: PNG, JPG, JPEG, PDF, TIFF"
    )
    
    if uploaded_file:
        st.divider()
        
        # File details in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("File Name", uploaded_file.name)
        col2.metric("File Type", uploaded_file.type.split('/')[-1].upper())
        col3.metric("File Size", f"{uploaded_file.size / 1024:.1f} KB")
        
        st.divider()
        
        # Process document
        with st.spinner('Processing document...'):
            try:
                # Display preview
                st.subheader("Document Preview")
                image_bytes = display_image_preview(uploaded_file)
                
                st.divider()
                
                # Process with API
                files = {'file': uploaded_file}
                response = requests.post('https://coe-apis.azurewebsites.net/vehicle_license_disc', files=files)
                
                if response.status_code == 200:
                    st.subheader("Extracted Information")
                    data = json.loads(response.text)  # Parse the JSON string response
                    
                    # Display results
                    display_results(data)
                    
                    # Download options
                    st.divider()
                    st.subheader("Download Options")
                    
                    col1, col2 = st.columns(2)
                    
                    # Generate timestamp for filenames
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    
                    # Text download - generate content directly in memory
                    with col1:
                        text_content = generate_text_content(data)
                        st.download_button(
                            label="📄 Download as Text",
                            data=text_content,
                            file_name=f"vehicle_license_info_{timestamp}.txt",
                            mime="text/plain"
                        )
                    
                    # JSON download - generate content directly in memory
                    with col2:
                        json_content = json.dumps(data, indent=4)
                        st.download_button(
                            label="📊 Download as JSON",
                            data=json_content,
                            file_name=f"vehicle_license_info_{timestamp}.json",
                            mime="application/json"
                        )
                
                else:
                    st.error(f"Error processing document: {response.json().get('error', 'Unknown error')}")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to API: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")