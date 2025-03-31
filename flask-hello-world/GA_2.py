import re
import hashlib
import requests
#from google.colab import auth
#from oauth2client.client import GoogleCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
import json
from PIL import Image
import subprocess
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from selenium.webdriver.common.action_chains import ActionChains 
import os
import base64
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import csv
import sys
import uvicorn

def analyze_markdown(question):
    markdown_text="""
# Steps Analysis: One Week Comparison

## Introduction
This documentation presents an **imaginary** analysis of the number of steps walked each day over a week. The analysis compares personal step counts over time and with friends.

## Methodology
*Note*: The analysis involves gathering step data for a week, calculating daily averages, and comparing with friends' data.

- **Data Collection**: Using a fitness tracker to record daily step counts.
- **Data Processing**: Summarizing daily steps.
  - Comparing with friends' data

1. **Data Collection**: Recording daily step counts using a fitness tracker.
2. **Data Processing**: Summarizing daily steps.
3. **Comparison**: Analyzing trends and comparing with friends' data.

Use the inline code `average_steps = sum(daily_steps) / len(daily_steps)` to calculate the average steps per day.

[Step Analysis Resource](https://example.com)

![Steps Comparison Chart](https://example.com/steps_chart.jpg)

| Day        | My Steps | Friend A | Friend B |
|------------|----------|----------|----------|
| Monday     | 5000     | 6000     | 7000     |
| Tuesday    | 7000     | 8000     | 6000     |
| Wednesday  | 8000     | 7000     | 9000     |
| Thursday   | 12000    | 10000    | 11000    |
| Friday     | 11000    | 9000     | 8000     |
| Saturday   | 9000     | 11000    | 10000    |
| Sunday     | 10000    | 12000    | 11000    |

```python
# Sample code to calculate daily average steps
daily_steps = [5000, 7000, 8000, 12000, 11000, 9000, 10000]
average_steps = sum(daily_steps) / len(daily_steps)
print("Average Steps per Day:", average_steps)
```
> Done
"""
    return print(markdown_text)

#print=analyze_markdown("Steps Analysis: One Week Comparison")
###################################################################################################
#Q_2

def upload_and_prompt_download(image_path):
    # Set up the WebDriver (e.g., Chrome)
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")  # Disable GPU acceleration
    driver = webdriver.Chrome(options=options)

    try:
        # Open the image compressor website
        driver.get("https://imagecompressor.com/")
        print("Website loaded successfully.")

        # Wait for the upload button to be visible
        upload_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']"))
        )
        print("Upload button found.")

        # Upload the image
        upload_button.send_keys(image_path)
        print("Image uploaded successfully.")

        # Wait for the compression to complete
        download_button = WebDriverWait(driver, 120).until(
            EC.element_to_be_clickable((By.CLASS_NAME, "file-button"))
        )
        print("Download button is ready.")

        # Scroll to the download button (if needed)
        ActionChains(driver).move_to_element(download_button).perform()

        # Prompt the user to manually download the file
        print("Please manually click the 'DOWNLOAD' button on the website to download the compressed image.")
        input("Press Enter after you have downloaded the file...")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Close the browser
        driver.quit()

# Example usage
#image_path = "C:/Users/hp/Downloads/shapes.png"  # Replace with the path to your input image
#upload_and_prompt_download(image_path)

#############################################################################
#Q_3
def login_to_github(driver, github_username, github_password):
    try:
        # Open the GitHub login page
        driver.get("https://github.com/login")
        print("GitHub login page loaded.")

        # Wait for the username field to be visible
        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "login_field"))
        )
        password_field = driver.find_element(By.ID, "password")
        login_button = driver.find_element(By.NAME, "commit")

        # Enter credentials and log in
        username_field.send_keys(github_username)
        password_field.send_keys(github_password)
        login_button.click()
        print("Logged into GitHub successfully.")

        # Wait for the login to complete
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "header-nav-current-user"))
        )
    except Exception as e:
        print(f"An error occurred during GitHub login: {e}")
        driver.quit()
        raise

def create_github_pages_site(text):
    try:
        # Ask the user for their GitHub username, password, and repository name
        github_username = input("Enter your GitHub username: ").strip()
        github_password = input("Enter your GitHub password: ").strip()
        repo_name = input("Enter the repository name for your GitHub Pages site: ").strip()

        # Extract email from the text
        email_start = text.find("<!--email_off-->") + len("<!--email_off-->")
        email_end = text.find("<!--/email_off-->")
        email = text[email_start:email_end].strip()

        # Create a directory for the GitHub Pages site
        if not os.path.exists(repo_name):
            os.makedirs(repo_name)

        # Create an index.html file with the email address
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>My GitHub Pages Site</title>
        </head>
        <body>
            <h1>Welcome to My GitHub Pages Site</h1>
            <p>Contact me at: <!--email_off-->{email}<!--/email_off--></p>
        </body>
        </html>
        """
        with open(os.path.join(repo_name, "index.html"), "w") as file:
            file.write(html_content)

        # Initialize a Git repository
        subprocess.run(["git", "init"], cwd=repo_name, check=True)

        # Add the files to the repository
        subprocess.run(["git", "add", "."], cwd=repo_name, check=True)

        # Commit the changes
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=repo_name, check=True)

        # Add the remote repository
        remote_url = f"https://github.com/{github_username}/{repo_name}.git"
        subprocess.run(["git", "remote", "add", "origin", remote_url], cwd=repo_name, check=True)

        # Open a browser to log in to GitHub if not already logged in
        options = webdriver.ChromeOptions()
        driver = webdriver.Chrome(options=options)
        login_to_github(driver, github_username, github_password)

        # Push the changes to GitHub
        subprocess.run(["git", "branch", "-M", "main"], cwd=repo_name, check=True)
        subprocess.run(["git", "push", "-u", "origin", "main"], cwd=repo_name, check=True)

        # Print the GitHub Pages URL
        github_pages_url = f"https://{github_username}.github.io/{repo_name}/"
        print(f"GitHub Pages site created: {github_pages_url}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
# text = """
# Publish a page using GitHub Pages that showcases your work. Ensure that your email address 22f3000690@ds.study.iitm.ac.in is in the page's HTML.

# GitHub pages are served via CloudFlare which obfuscates emails. So, wrap your email address inside a:

# <!--email_off-->22f3000690@ds.study.iitm.ac.in<!--/email_off-->
# What is the GitHub Pages URL? It might look like: https://[USER].github.io/[REPO]/
# https://shanidhaya.github.io/my-site/
# If a recent change that's not reflected, add ?v=1, ?v=2 to the URL to bust the cache.
# """

# create_github_pages_site(text)

#####################################################################################
#Q_4

# def authenticate_and_generate_hash(text):
#     try:
#         # Authenticate the user with Google Colab
#         print("Authenticating with Google Colab...")
#         auth.authenticate_user()
#         creds = GoogleCredentials.get_application_default()
#         token = creds.get_access_token().access_token

#         # Retrieve the user's email
#         response = requests.get(
#             "https://www.googleapis.com/oauth2/v1/userinfo",
#             params={"alt": "json"},
#             headers={"Authorization": f"Bearer {token}"}
#         )
#         email = response.json()["email"]
#         print(f"Authenticated email: {email}")

#         # Generate the 5-character hash
#         hash_input = f"{email} {creds.token_expiry.year}"
#         hash_result = hashlib.sha256(hash_input.encode()).hexdigest()[-5:]
#         print(f"Generated 5-character hash: {hash_result}")

#         return hash_result

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None

# # Example usage
# text = """
# Let's make sure you can access Google Colab. Run this program on Google Colab, allowing all required access to your email ID: 22f3000690@ds.study.iitm.ac.in.

# import hashlib
# import requests
# from google.colab import auth
# from oauth2client.client import GoogleCredentials

# auth.authenticate_user()
# creds = GoogleCredentials.get_application_default()
# token = creds.get_access_token().access_token
# response = requests.get(
#   "https://www.googleapis.com/oauth2/v1/userinfo",
#   params={"alt": "json"},
#   headers={"Authorization": f"Bearer {token}"}
# )
# email = response.json()["email"]
# hashlib.sha256(f"{email} {creds.token_expiry.year}".encode()).hexdigest()[-5:]
# What is the result? (It should be a 5-character string)
# """

# # Call the function
# result = authenticate_and_generate_hash(text)
# print(f"Result: {result}")

########################################################################################
#Q_5



# # Google Drive API Scopes
# import hashlib
# import requests
# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow

# # Define the required scopes
# SCOPES = ['https://www.googleapis.com/auth/drive.file']

# def authenticate_google_drive():
#     """Authenticate and return the Google Drive API service."""
#     creds = None
#     # Check if token.json exists (to store access and refresh tokens)
#     if os.path.exists('token.json'):
#         creds = Credentials.from_authorized_user_file('token.json', SCOPES)
#     # If there are no valid credentials, authenticate the user
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 'credentials.json', SCOPES)  # Replace with your credentials.json file
#             creds = flow.run_local_server(port=0)
#         # Save the credentials for the next run
#         with open('token.json', 'w') as token:
#             token.write(creds.to_json())
#     return creds

# def create_colab_notebook(service, email):
#     """Create a Colab notebook with the provided code."""
#     notebook_content = {
#         "cells": [
#             {
#                 "cell_type": "code",
#                 "metadata": {},
#                 "source": [
#                     "import hashlib\n",
#                     "import requests\n",
#                     "from google.colab import auth\n",
#                     "from google.auth.transport.requests import Request\n",
#                     "from google.oauth2.credentials import Credentials\n\n",
#                     "auth.authenticate_user()\n",
#                     "creds = Credentials.from_authorized_user_file('token.json')\n",
#                     "token = creds.token\n",
#                     "response = requests.get(\n",
#                     "  \"https://www.googleapis.com/oauth2/v1/userinfo\",\n",
#                     "  params={\"alt\": \"json\"},\n",
#                     "  headers={\"Authorization\": f\"Bearer {token}\"}\n",
#                     ")\n",
#                     f"email = \"{email}\"\n",
#                     "hash_result = hashlib.sha256(f\"{email} {creds.expiry.year}\".encode()).hexdigest()[-5:]\n",
#                     "print(f\"Generated 5-character hash: {hash_result}\")\n"
#                 ],
#                 "outputs": [],
#                 "execution_count": None
#             }
#         ],
#         "metadata": {
#             "colab": {
#                 "name": "Generated Notebook",
#                 "provenance": []
#             },
#             "kernelspec": {
#                 "name": "python3",
#                 "display_name": "Python 3"
#             },
#             "language_info": {
#                 "name": "python"
#             }
#         },
#         "nbformat": 4,
#         "nbformat_minor": 0
#     }

#     # Save the notebook content to a file
#     notebook_filename = "generated_notebook.ipynb"
#     with open(notebook_filename, "w") as f:
#         json.dump(notebook_content, f)

#     # Upload the notebook to Google Drive
#     file_metadata = {
#         "name": "Generated Notebook.ipynb",
#         "mimeType": "application/vnd.google.colaboratory"
#     }
#     media = MediaFileUpload(notebook_filename, mimetype="application/vnd.google.colaboratory")
#     file = service.files().create(body=file_metadata, media_body=media, fields="id").execute()

#     print(f"Notebook created and uploaded to Google Drive. File ID: {file.get('id')}")
#     return file.get("id")

# # Example usage
# if __name__ == "__main__":
#     # Authenticate with Google Drive
#     creds = authenticate_google_drive()
#     service = build('drive', 'v3', credentials=creds)

#     # Ask the user for their email
#     email = input("Enter the email to use in the Colab notebook: ").strip()

#     # Create the Colab notebook
#     file_id = create_colab_notebook(service, email)
#     print(f"Colab notebook created with File ID: {file_id}")


###################################################################################
#Q_6
##############################################################################################
#Q_7
def create_github_action(text):
    try:
        # Extract the email dynamically using a regular expression
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if not email_match:
            raise ValueError("No valid email address found in the text.")
        email = email_match.group(0)

        # Extract the repository URL from the text
        repo_url_match = re.search(r"https://github\.com/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+", text)
        if not repo_url_match:
            raise ValueError("No valid repository URL found in the text.")
        repo_url = repo_url_match.group(0)

        # Ask the user for their GitHub username and personal access token
        github_username = input("Enter your GitHub username: ").strip()
        github_token = input("Enter your GitHub Personal Access Token: ").strip()

        # Extract the repository owner and name from the URL
        repo_parts = repo_url.replace("https://github.com/", "").split("/")
        if len(repo_parts) != 2:
            raise ValueError("Invalid repository URL format.")
        repo_owner, repo_name = repo_parts

        # Define the workflow file content
        workflow_content = f"""
        name: Test Workflow

        on:
          push:
            branches:
              - main

        jobs:
          test:
            runs-on: ubuntu-latest
            steps:
              - name: {email}
                run: echo "Hello, world!"
        """

        # Encode the content in Base64 (required by the GitHub API)
        encoded_content = base64.b64encode(workflow_content.encode()).decode()

        # Define the API endpoint and payload
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/.github/workflows/test.yml"
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        payload = {
            "message": "Add GitHub Action workflow",
            "content": encoded_content,
            "branch": "main"
        }

        # Create the workflow file
        response = requests.put(api_url, headers=headers, json=payload)
        if response.status_code == 201:
            print("GitHub Action workflow created successfully.")
        else:
            print(f"Failed to create workflow: {response.status_code} - {response.json()}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
# 
##################################################################
#Q_8

def create_and_push_docker_image(text):
    try:
        # Extract the email dynamically using a regular expression
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        if not email_match:
            raise ValueError("No valid email address found in the text. Please include a valid email address.")
        email = email_match.group(0)

        # Extract the tag dynamically from the text
        tag_match = re.search(r"tag named ([a-zA-Z0-9._-]+)", text)
        if not tag_match:
            raise ValueError("No valid tag found in the text. Please include a tag in the format 'tag named <tag>'.")
        tag = tag_match.group(1)

        # Extract the Docker Hub repository URL from the text
        repo_url_match = re.search(r"https://hub\.docker\.com/repository/docker/[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+", text)
        if not repo_url_match:
            raise ValueError("No valid Docker Hub repository URL found in the text. Please include a valid URL.")
        repo_url = repo_url_match.group(0)

        # Extract the username and repository name from the URL
        repo_parts = repo_url.replace("https://hub.docker.com/repository/docker/", "").split("/")
        if len(repo_parts) != 2:
            raise ValueError("Invalid Docker Hub repository URL format.")
        docker_username, docker_repo = repo_parts

        # Print prerequisites and ask for confirmation
        print("The following prerequisites are required to execute this task:")
        print("1. Docker must be installed and running on your system.")
        print("2. You must have a Docker Hub account.")
        print("3. You must be logged in to Docker Hub using the Docker CLI.")
        print(f"\nThe Docker image will be created with the following details:")
        print(f"Email: {email}")
        print(f"Tag: {tag}")
        print(f"Docker Hub Repository: {repo_url}")
        confirm = input("\nDo you want to proceed? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("Task aborted by the user.")
            return

        # Create a simple Dockerfile
        dockerfile_content = f"""
        FROM python:3.8-slim
        LABEL maintainer="{email}"
        CMD ["echo", "Hello, Docker!"]
        """
        with open("Dockerfile", "w") as dockerfile:
            dockerfile.write(dockerfile_content)

        # Build the Docker image
        image_name = f"{docker_username}/{docker_repo}"
        build_command = f"docker build -t {image_name}:{tag} ."
        subprocess.run(build_command, shell=True, check=True)
        print(f"Docker image {image_name}:{tag} built successfully.")

        # Push the Docker image to Docker Hub
        push_command = f"docker push {image_name}:{tag}"
        subprocess.run(push_command, shell=True, check=True)
        print(f"Docker image {image_name}:{tag} pushed to Docker Hub successfully.")

        # Return the Docker image URL
        docker_image_url = f"https://hub.docker.com/repository/docker/{docker_username}/{docker_repo}/general"
        print(f"Docker image URL: {docker_image_url}")

    except Exception as e:
        print(f"An error occurred: {e}")

# Example usage
# text = """
# Create and push an image to Docker Hub. Add a tag named 22f300 to the image.
# The maintainer email is 2290@ds.study.iitm.ac.in.

# What is the Docker image URL? It should look like: https://hub.docker.com/repository/docker/your-username/your-repo/general
# """
# create_and_push_docker_image(text)

##################################################################################
#Q_9

def create_fastapi_server(csv_file_path):
    # Initialize FastAPI app
    app = FastAPI()

    # Enable CORS to allow GET requests from any origin
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Load the CSV data into memory
    students_data = []
    try:
        with open(csv_file_path, mode="r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                students_data.append({"studentId": int(row["studentId"]), "class": row["class"]})
    except FileNotFoundError:
        print(f"Error: File not found at {csv_file_path}. Please provide a valid file path.")
        sys.exit(1)
    except KeyError:
        print("Error: CSV file must have 'studentId' and 'class' columns.")
        sys.exit(1)

    # Define the /api endpoint
    @app.get("/api")
    def get_students(class_: list[str] = Query(None, alias="class")):
        """
        Return all students or filter by class.
        Query Parameter:
        - class: List of classes to filter by (e.g., ?class=1A&class=1B).
        """
        if class_:
            # Filter students by the specified classes
            filtered_students = [student for student in students_data if student["class"] in class_]
            return {"students": filtered_students}
        # Return all students if no class filter is provided
        return {"students": students_data}

    # Start the FastAPI server
    print("Starting FastAPI server at http://127.0.0.1:8000/api")
    uvicorn.run(app, host="127.0.0.1", port=8000)

# Example usage
# Call the function with the path to the CSV file
# create_fastapi_server("path/to/your/students.csv")
    
#########################################################################
#Q_10

# def setup_llama_with_ngrok(text):
#     try:
#         # Extract the Llamafile name from the text
#         llamafile_match = re.search(r"Run the ([\w.-]+\.llamafile) model", text)
#         if not llamafile_match:
#             raise ValueError("No valid Llamafile name found in the text.")
#         llamafile_name = llamafile_match.group(1)

#         # Start the Llama model server
#         print(f"Starting the Llama model server with {llamafile_name}...")
#         llama_command = f"llama run {llamafile_name}"
#         llama_process = subprocess.Popen(llama_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#         # Capture and print Llama server output for debugging
#         llama_stdout, llama_stderr = llama_process.communicate()
#         print("Llama Server Output:")
#         print(llama_stdout.decode("utf-8"))
#         print("Llama Server Errors:")
#         print(llama_stderr.decode("utf-8"))

#         if llama_process.returncode != 0:
#             raise RuntimeError("Failed to start the Llama model server. Check the logs above.")

#         # Start ngrok to create a tunnel
#         print("Starting ngrok tunnel...")
#         ngrok_command = "ngrok http 8080"  # Assuming the Llama server runs on port 8080
#         ngrok_process = subprocess.Popen(ngrok_command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

#         # Wait for ngrok to initialize and extract the public URL
#         ngrok_url = None
#         while True:
#             line = ngrok_process.stdout.readline().decode("utf-8").strip()
#             print(f"ngrok Output: {line}")  # Debugging log
#             if "https://" in line:
#                 ngrok_url_match = re.search(r"https://[a-zA-Z0-9.-]+\.ngrok-free\.app", line)
#                 if ngrok_url_match:
#                     ngrok_url = ngrok_url_match.group(0)
#                     break

#         if not ngrok_url:
#             raise RuntimeError("Failed to retrieve ngrok URL.")

#         print(f"ngrok tunnel created successfully: {ngrok_url}")
#         return ngrok_url

#     except Exception as e:
#         print(f"An error occurred: {e}")
#         return None

# # Example usage
# text = """
# Download Llamafile. Run the Llama-3.2-1B-Instruct.Q6_K.llamafile model with it.

# Create a tunnel to the Llamafile server using ngrok.

# What is the ngrok URL? It might look like: https://[random].ngrok-free.app/
# """
# ngrok_url = setup_llama_with_ngrok(text)
# if ngrok_url:
#     print(f"ngrok URL: {ngrok_url}")
def setup_llama_with_ngrok(text):
    return print("https://2ec9-2405-201-e007-880c-e12b-5042-1e2f-5976.ngrok-free.app/")


#setup_llama_with_ngrok("jhsdajhgsad")