FROM python:3.11

WORKDIR /app

COPY . .

# Remove the unrequired folders from the image
# RUN rm -rf /app/input_documents

# Update the package list and install necessary packages  
RUN apt-get update && \  
    apt-get install -y \  
    curl \  
    apt-transport-https \  
    gnupg2 \  
    build-essential \  
    && rm -rf /var/lib/apt/lists/*  

# Add the Microsoft repository key  
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -  
  
# Add the Microsoft repository  
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list  
  
# Update the package list again  
RUN apt-get update  
  
# Install the msodbcsql17 driver and dependencies  
RUN ACCEPT_EULA=Y apt-get install -y msodbcsql17  
  
# Install optional: UnixODBC development headers  
RUN apt-get install -y unixodbc-dev  
  
# Clean up  
RUN apt-get clean && \  
    rm -rf /var/lib/apt/lists/*  

# List the directory of the application
RUN ls -la /app

# Remove hard-coded port settings
ENV STREAMLIT_SERVER_HEADLESS=true

EXPOSE 8501

# Pip command without proxy setting
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "streamlit", "run", "app.py"]