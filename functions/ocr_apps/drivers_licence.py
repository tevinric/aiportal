import streamlit as st
import requests
import json
import pandas as pd
from datetime import datetime
from PIL import Image
import io

def save_results_to_file(data, filename):
    """Save the extracted information to a structured text file"""
    with open(filename, 'w') as f:
        f.write("Driver's License Information\n")
        f.write("=========================\n\n")
        for key, value in data.items():
            f.write(f"{key}: {value}\n")

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
        "Personal Information": {
            "Name": data.get("Name", ""),
            "ID Number": data.get("ID No .", ""),
            "Sex": data.get("Sex", ""),
            "Date of Birth": data.get("Birth", "")
        },
        "License Information": {
            "License Number": data.get("Licence Number", ""),
            "License Code": data.get("Code", ""),
            "Vehicle Restriction": data.get("Vehicle restriction", "")
        },
        "Validity Details": {
            "Valid Period": data.get("Valid", ""),
            "Issue Date": data.get("Issued", ""),
            "First Issue Date": data.get("First issue", ""),
            "Restrictions": data.get("Restriction", "")
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

def ocr_drivers_license():
    st.title("Driver's License OCR")
    
    # Upload Section
    st.write("### Upload Document")
    uploaded_file = st.file_uploader(
        "Choose a driver's license document",
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
                response = requests.post('https://coe-apis.azurewebsites.net/drivers_license', files=files)
                
                if response.status_code == 200:
                    st.subheader("Extracted Information")
                    data = response.json()
                    
                    # Display results
                    display_results(data)
                    
                    # Download options
                    st.divider()
                    st.subheader("Download Options")
                    
                    # col1, col2 = st.columns(2)
                    
                    # # Text download
                    # timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        
                    #     # Text download - generate content directly in memory
                    # with col1:
                    #     text_content = generate_text_content(data)
                    #     st.download_button(
                    #         label="📄 Download as Text",
                    #         data=text_content,
                    #         file_name=f"vehicle_license_info_{timestamp}.txt",
                    #         mime="text/plain"
                    #     )
                    
                    # # JSON download - generate content directly in memory
                    # with col2:
                    #     json_content = json.dumps(data, indent=4)
                    #     st.download_button(
                    #         label="📊 Download as JSON",
                    #         data=json_content,
                    #         file_name=f"vehicle_license_info_{timestamp}.json",
                    #         mime="application/json"
                    #     )
                
                else:
                    st.error(f"Error processing document: {response.json().get('error', 'Unknown error')}")
            
            except requests.exceptions.RequestException as e:
                st.error(f"Error connecting to API: {str(e)}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {str(e)}")

# if __name__ == "__main__":
#     main()