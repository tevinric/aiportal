# Step 1 - Create the docker image
```docker build -t <image_name> .```

# Step 2- Run the docker image on a port that was exposed - Good when deploying a streamlit app
``` docker run -p 8501:8501 <image_name>```

First 8501 is the container port to run the app on
Second 8501 is the app port exposed for the container

The docker image will now be available locally thourgh Docker Desktop or Rancher Desktop. This is the local image

## Follow the steps below to push the local image to an Azure Container Registry

# Step 3 - Create an azure container registry in Azure

When creating please take note of the container registry name and the server. 

Please enable admin for the ACR

# Step 4 - Get the name of all images locally 

Check all the local images and locate the one you wish to push to ACR

```docker images```

# Pushing a Docker Image to Azure Container Registry (ACR)

## Prerequisites
- Azure CLI installed and logged in
- Docker installed and running
- An existing Azure Container Registry
- A Docker image you want to push

## Steps

1. Log in to Azure (if not already logged in):
   ```
   az login
   ```

2. Log in to your Azure Container Registry:
   ```
   az acr login --name <your-acr-name>
   ```
   Replace `<your-acr-name>` with your ACR name.

3. Tag your local image with the ACR login server name:
   ```
   docker tag <local-image-name>:<tag> <acr-login-server>/<image-name>:<tag>
   ```
   - `<local-image-name>`: The name of your local image
   - `<tag>`: The tag of your local image (e.g., latest)
   - `<acr-login-server>`: Your ACR login server name (e.g., myregistry.azurecr.io)
   - `<image-name>`: The name you want to use for the image in ACR

4. Push the tagged image to ACR:
   ```
   docker push <acr-login-server>/<image-name>:<tag>
   ```

5. Verify the push by listing the repositories in your ACR:
   ```
   az acr repository list --name <your-acr-name> --output table
   ```

6. To see the tags for a specific repository:
   ```
   az acr repository show-tags --name <your-acr-name> --repository <image-name> --output table
   ```

## Example

Assuming you have:
- ACR name: myregistry
- Local image: myapp:v1
- Desired image name in ACR: myapplication

The commands would look like this:

```bash
az acr login --name myregistry
docker tag myapp:v1 myregistry.azurecr.io/myapplication:v1
docker push myregistry.azurecr.io/myapplication:v1
az acr repository list --name myregistry --output table
az acr repository show-tags --name myregistry --repository myapplication --output table
```



## Removing docker build cache

```docker buildx prune```