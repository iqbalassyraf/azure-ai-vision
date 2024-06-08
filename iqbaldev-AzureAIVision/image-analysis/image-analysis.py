# Import necessary libraries and modules
from dotenv import load_dotenv  # To load environment variables from a .env file
import os  # To interact with the operating system
from PIL import Image, ImageDraw  # For image processing and drawing
import sys  # To handle command-line arguments and system-specific parameters
from matplotlib import pyplot as plt  # For plotting and visualizing data
from azure.core.exceptions import HttpResponseError  # To handle HTTP response errors from Azure
import requests  # To make HTTP requests

# Import namespaces for Azure AI Vision
from azure.ai.vision.imageanalysis import ImageAnalysisClient  # To interact with Azure Image Analysis service
from azure.ai.vision.imageanalysis.models import VisualFeatures  # To specify visual features for analysis
from azure.core.credentials import AzureKeyCredential  # For authentication using Azure API key

# Main function that orchestrates the workflow
def main():
    global cv_client  # Declare cv_client as a global variable

    try:
        # Load environment variables from .env file
        load_dotenv()
        ai_endpoint = os.getenv('AI_SERVICE_ENDPOINT')  # Get the AI service endpoint
        ai_key = os.getenv('AI_SERVICE_KEY')  # Get the AI service key

        # Get the image file path
        image_file = 'images/street.jpg'
        if len(sys.argv) > 1:
            image_file = sys.argv[1]  # If a command-line argument is provided, use it as the image file path

        # Read the image file in binary mode
        with open(image_file, "rb") as f:
            image_data = f.read()

        # Authenticate Azure AI Vision client
        cv_client = ImageAnalysisClient(
            endpoint=ai_endpoint,
            credential=AzureKeyCredential(ai_key)
        )
        
        # Analyze the image using the helper function
        AnalyzeImage(image_file, image_data, cv_client)
        
        # Remove the background using the helper function
        BackgroundForeground(ai_endpoint, ai_key, image_file)

    except Exception as ex:
        # Print any exceptions that occur
        print(ex)

# Helper function to analyze the image
def AnalyzeImage(image_filename, image_data, cv_client):
    print('\nAnalyzing image...')

    try:
        # Get analysis results with specified visual features
        result = cv_client.analyze(
            image_data=image_data,
            visual_features=[
                VisualFeatures.CAPTION,
                VisualFeatures.DENSE_CAPTIONS,
                VisualFeatures.TAGS,
                VisualFeatures.OBJECTS,
                VisualFeatures.PEOPLE
            ],
        )

    except HttpResponseError as e:
        # Handle HTTP response errors
        print(f"Status code: {e.status_code}")
        print(f"Reason: {e.reason}")
        print(f"Message: {e.error.message}")

    # Display analysis results for objects in the image
    if result.objects is not None:
        print("\nObjects in image:")

        # Open the image and prepare for drawing
        image = Image.open(image_filename)
        fig = plt.figure(figsize=(image.width/100, image.height/100))
        plt.axis('off')
        draw = ImageDraw.Draw(image)
        color = 'cyan'

        for detected_object in result.objects.list:
            # Print object name and confidence
            print(" {} (confidence: {:.2f}%)".format(detected_object.tags[0].name, detected_object.tags[0].confidence * 100))
            
            # Draw object bounding box
            r = detected_object.bounding_box
            bounding_box = ((r.x, r.y), (r.x + r.width, r.y + r.height)) 
            draw.rectangle(bounding_box, outline=color, width=3)
            plt.annotate(detected_object.tags[0].name, (r.x, r.y), backgroundcolor=color)

        # Save the annotated image
        plt.imshow(image)
        plt.tight_layout(pad=0)
        outputfile = 'objects.jpg'
        fig.savefig(outputfile)
        print('  Results saved in', outputfile)

    # Display analysis results for people in the image
    if result.people is not None:
        print("\nPeople in image:")

        # Open the image and prepare for drawing
        image = Image.open(image_filename)
        fig = plt.figure(figsize=(image.width/100, image.height/100))
        plt.axis('off')
        draw = ImageDraw.Draw(image)
        color = 'cyan'

        for detected_people in result.people.list:
            # Draw bounding box for each person
            r = detected_people.bounding_box
            bounding_box = ((r.x, r.y), (r.x + r.width, r.y + r.height))
            draw.rectangle(bounding_box, outline=color, width=3)

            # Print the confidence of the person detected
            print(" {} (confidence: {:.2f}%)".format(detected_people.bounding_box, detected_people.confidence * 100))
            
        # Save the annotated image
        plt.imshow(image)
        plt.tight_layout(pad=0)
        outputfile = 'people.jpg'
        fig.savefig(outputfile)
        print('  Results saved in', outputfile)

# Helper function to remove background from the image
def BackgroundForeground(endpoint, key, image_file):
    # Define the API version and mode
    api_version = "2023-02-01-preview"
    mode = "backgroundRemoval"  # Mode can be "foregroundMatting" or "backgroundRemoval"
    
    # Print message indicating background removal process
    print('\nRemoving background from image...')
    
    # Construct the API URL
    url = "{}computervision/imageanalysis:segment?api-version={}&mode={}".format(endpoint, api_version, mode)

    # Set headers for the API request
    headers = {
        "Ocp-Apim-Subscription-Key": key, 
        "Content-Type": "application/json"
    }

    # Construct the image URL
    image_url = "https://github.com/MicrosoftLearning/mslearn-ai-vision/blob/main/Labfiles/01-analyze-images/Python/image-analysis/{}?raw=true".format(image_file)  

    # Set the request body
    body = {
        "url": image_url,
    }
        
    # Make the API request to remove the background
    response = requests.post(url, headers=headers, json=body)

    # Save the response content as an image
    image = response.content
    with open("backgroundForeground.png", "wb") as file:
        file.write(image)
    print('  Results saved in backgroundForeground.png \n')

# Ensure the main function runs when the script is executed directly
if __name__ == "__main__":
    main()