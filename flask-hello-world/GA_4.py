import requests
from bs4 import BeautifulSoup
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import markdown
import uvicorn
from urllib.parse import urlencode
import pandas as pd
from datetime import datetime
from geopy.geocoders import Nominatim
import feedparser
import tabula
import subprocess
import os
from pathlib import Path
from pdfminer.high_level import extract_text
import markdownify

# Q_2
def fetch_movies_from_text(input_text):
    """
    Fetches movie data from IMDb based on the rating range extracted from the input text.

    Args:
        input_text (str): The input text containing the rating range and task description.

    Returns:
        str: JSON string containing the movie data.
    """
    # Extract the rating range from the input text using regex
    rating_match = re.search(r"rating between (\d+) and (\d+)", input_text)
    if not rating_match:
        print("Rating range not found in the input text.")
        return json.dumps([])

    min_rating = float(rating_match.group(1))
    max_rating = float(rating_match.group(2))

    # IMDb search URL with title_type=feature
    source_url = f"https://www.imdb.com/search/title/?title_type=feature&user_rating={min_rating},{max_rating}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    response = requests.get(source_url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch page: {response.status_code}")
        return json.dumps([])

    soup = BeautifulSoup(response.text, "html.parser")
    movies = []

    # Select up to 25 movie items
    movie_items = soup.select('.ipc-metadata-list-summary-item')[:25]

    for item in movie_items:
        title_element = item.select_one('.ipc-title__text')
        year_element = item.select_one('.sc-f30335b4-7.jhjEEd.dli-title-metadata-item')
        rating_element = item.select_one('.ipc-rating-star--rating')

        if title_element and year_element:
            # Extract ID
            link_tag = item.select_one('a[href*="/title/tt"]')
            match = re.search(r'tt\d+', link_tag['href']) if link_tag else None
            imdb_id = match.group(0) if match else None

            # Extract and clean fields
            title = title_element.get_text(strip=True)
            year = year_element.get_text().replace('\xa0', ' ')  # Preserve NBSP
            rating = rating_element.get_text(strip=True) if rating_element else None

            try:
                rating_float = float(rating)
                if min_rating <= rating_float <= max_rating:
                    movies.append({
                        "id": imdb_id,
                        "title": title,
                        "year": year,
                        "rating": rating
                    })
            except (ValueError, TypeError):
                continue

    return json.dumps(movies, indent=2, ensure_ascii=False)

########################################################################################

# Q_3

app = FastAPI()

# Allow CORS from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_wikipedia_url(country: str) -> str:
    """
    Given a country name, returns the Wikipedia URL for the country.
    """
    return f"https://en.wikipedia.org/wiki/{country}"

def extract_headings_from_html(html: str) -> list:
    """
    Extract all headings (H1 to H6) from the given HTML and return a list.
    """
    soup = BeautifulSoup(html, "html.parser")
    headings = []

    # Loop through all the heading tags (H1 to H6)
    for level in range(1, 7):
        for tag in soup.find_all(f'h{level}'):
            headings.append((level, tag.get_text(strip=True)))

    return headings

def generate_markdown_outline(headings: list) -> str:
    """
    Converts the extracted headings into a markdown-formatted outline.
    """
    markdown_outline = "## Contents\n\n"
    for level, heading in headings:
        markdown_outline += "#" * level + f" {heading}\n\n"
    return markdown_outline

@app.get("/api/outline")
async def get_country_outline(country: str):
    """
    API endpoint that returns the markdown outline of the given country Wikipedia page.
    """
    if not country:
        raise HTTPException(status_code=400, detail="Country parameter is required")

    # Fetch Wikipedia page
    url = get_wikipedia_url(country)
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=404, detail=f"Error fetching Wikipedia page: {e}")

    # Extract headings and generate markdown outline
    headings = extract_headings_from_html(response.text)
    if not headings:
        raise HTTPException(status_code=404, detail="No headings found in the Wikipedia page")

    markdown_outline = generate_markdown_outline(headings)
    return JSONResponse(content={"outline": markdown_outline})

#################################################################################################

# Q_4

def fetch_weather_forecast(input_text: str) -> str:
    """
    Fetches the weather forecast description for a given city based on the input text.

    Args:
        input_text (str): The input text containing the city name.

    Returns:
        str: JSON string containing the weather forecast description for the city.
    """
    # Extract the city name from the input text using regex
    city_match = re.search(r"weather forecast description for (\w+)", input_text, re.IGNORECASE)
    if not city_match:
        return json.dumps({"error": "City name not found in the input text."}, indent=4)

    required_city = city_match.group(1)

    # Construct the location API URL
    location_url = 'https://locator-service.api.bbci.co.uk/locations?' + urlencode({
        'api_key': 'AGbFAKx58hyjQScCXIYrxuEwJh2W2cmv',
        's': required_city,
        'stack': 'aws',
        'locale': 'en',
        'filter': 'international',
        'place-types': 'settlement,airport,district',
        'order': 'importance',
        'a': 'true',
        'format': 'json'
    })

    try:
        # Fetch location data
        location_result = requests.get(location_url).json()
        if not location_result['response']['results']['results']:
            return json.dumps({"error": f"No location found for city: {required_city}"}, indent=4)

        # Extract the location ID for the city
        location_id = location_result['response']['results']['results'][0]['id']

        # Construct the weather URL
        weather_url = f'https://www.bbc.com/weather/{location_id}'

        # Fetch weather data
        response = requests.get(weather_url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract daily weather summary
        daily_summary = soup.find('div', attrs={'class': 'wr-day-summary'})
        if not daily_summary:
            return json.dumps({"error": f"No weather data found for city: {required_city}"}, indent=4)

        # Split the daily summary into a list of descriptions
        daily_summary_list = re.findall('[a-zA-Z][^A-Z]*', daily_summary.text)

        # Generate a list of dates corresponding to the weather descriptions
        datelist = pd.date_range(datetime.today(), periods=len(daily_summary_list)).tolist()
        datelist = [date.date().strftime('%Y-%m-%d') for date in datelist]

        # Map dates to descriptions
        weather_data = {date: desc for date, desc in zip(datelist, daily_summary_list)}

        # Convert to JSON
        weather_json = json.dumps(weather_data, indent=4)
        return weather_json

    except Exception as e:
        return json.dumps({"error": f"An error occurred: {str(e)}"}, indent=4)

#################################################################################################

# Q_5

def fetch_min_latitude(input_text: str) -> str:
    """
    Fetches the minimum latitude of the bounding box for a given city and country using the Nominatim API.

    Args:
        input_text (str): The input text containing the city and country.

    Returns:
        str: JSON string containing the minimum latitude or an error message.
    """
    # Extract the city and country from the input text using regex
    match = re.search(r"minimum latitude of the bounding box of the city (\w+) in the country (\w+)", input_text, re.IGNORECASE)
    if not match:
        return json.dumps({"error": "City and country not found in the input text."}, indent=4)

    city = match.group(1)
    country = match.group(2)

    # Activate the Nominatim geocoder
    locator = Nominatim(user_agent="myGeocoder")

    try:
        # Geocode the city and country
        location = locator.geocode(f"{city}, {country}")

        # Check if the location was found
        if location:
            # Retrieve the bounding box
            bounding_box = location.raw.get('boundingbox', [])

            # Check if the bounding box is available
            if len(bounding_box) > 1:
                # Extract the minimum latitude from the bounding box (the first value in the list)
                min_latitude = bounding_box[0]
                return json.dumps({"city": city, "country": country, "min_latitude": min_latitude}, indent=4)
            else:
                return json.dumps({"error": "Bounding box information not available."}, indent=4)
        else:
            return json.dumps({"error": f"Location not found for city: {city}, country: {country}"}, indent=4)

    except Exception as e:
        return json.dumps({"error": f"An error occurred: {str(e)}"}, indent=4)

#################################################################################################

# Q_6

def fetch_latest_hn_post(input_text: str) -> str:
    """
    Fetches the link to the latest Hacker News post based on the query and minimum points extracted from the input text.

    Args:
        input_text (str): The input text containing the query and minimum points.

    Returns:
        str: JSON string containing the link to the latest post or an error message.
    """
    # Extract the query and points from the input text using regex
    match = re.search(r"latest Hacker News post mentioning (\w+) having at least (\d+) points", input_text, re.IGNORECASE)
    if not match:
        return json.dumps({"error": "Query and points not found in the input text."}, indent=4)

    query = match.group(1)
    points = match.group(2)

    # Construct the feed URL
    feed_url = f"https://hnrss.org/newest?q={query}&points={points}"
    feed = feedparser.parse(feed_url)

    # Extract the link of the latest post
    if feed.entries:
        latest_post_link = feed.entries[0].link
    else:
        latest_post_link = "No posts found."

    # Return the result as JSON
    return json.dumps({"query": query, "points": points, "latest_post_link": latest_post_link}, indent=4)

##################################################################################################################

# Q_7

import datetime

def fetch_newest_github_user(input_text: str) -> str:
    """
    Fetches the newest GitHub user profile based on location and follower count extracted from the input text.

    Args:
        input_text (str): The input text containing the city and follower count.

    Returns:
        str: JSON string containing the newest user's profile creation date and details or an error message.
    """
    # Extract the city and follower count from the input text using regex
    match = re.search(r"users located in the city (\w+) with over (\d+) followers", input_text, re.IGNORECASE)
    if not match:
        return json.dumps({"error": "City and follower count not found in the input text."}, indent=4)

    city = match.group(1)
    followers = match.group(2)

    # Ask the user for their GitHub personal access token
    github_token = input("Enter your GitHub personal access token: ").strip()
    headers = {'Authorization': f'token {github_token}'}

    # Get the current local date and time
    current_local_datetime = datetime.datetime.now()

    # Subtract 5 minutes to set the cutoff time
    cutoff_datetime = current_local_datetime - datetime.timedelta(minutes=5)

    # Function to search for users based on location and followers, sorted by join date
    def search_users():
        url = f"https://api.github.com/search/users?q=location:{city}+followers:>{followers}&sort=joined&order=desc"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json().get('items', [])
        else:
            return {"error": f"Error: {response.status_code} - {response.json().get('message')}"}

    # Get users in the specified city with more than the specified followers, sorted by join date (newest first)
    users = search_users()

    if isinstance(users, dict) and "error" in users:
        return json.dumps(users, indent=4)

    # Process the first valid user who is not ultra-new
    for user in users:
        user_url = user['url']  # Get the profile API URL
        user_response = requests.get(user_url, headers=headers)

        if user_response.status_code == 200:
            user_data = user_response.json()
            created_at = user_data['created_at']  # ISO 8601 format
            created_at_date = datetime.datetime.fromisoformat(created_at[:-1])  # Convert to datetime

            # Check if the user is NOT ultra-new (joined more than 5 minutes ago)
            if created_at_date < cutoff_datetime:
                return json.dumps({
                    "city": city,
                    "followers": followers,
                    "newest_user": {
                        "login": user_data['login'],
                        "profile_url": user_data['html_url'],
                        "created_at": created_at
                    }
                }, indent=4)
        else:
            return json.dumps({"error": f"Error fetching user details: {user_response.status_code}"}, indent=4)

    # If no valid users found
    return json.dumps({"error": "No valid users found."}, indent=4)


def calculate_total_marks(input_text: str, pdf_path: str) -> str:
    """
    Calculates the total Maths marks of students who scored 19 or more marks in Physics
    in groups 57-82 (inclusive) from a PDF file containing student marks.

    Args:
        input_text (str): The input text containing the task description.
        pdf_path (str): The path to the PDF file containing the student marks table.

    Returns:
        str: A JSON string containing the total Maths marks or an error message.
    """
    # Extract the criteria from the input text using regex
    match = re.search(r"scored (\d+) or more marks in Physics in groups (\d+)-(\d+)", input_text, re.IGNORECASE)
    if not match:
        return json.dumps({"error": "Criteria not found in the input text."}, indent=4)

    physics_min_marks = int(match.group(1))
    group_min = int(match.group(2))
    group_max = int(match.group(3))

    try:
        # Extract tables from the PDF
        tables = tabula.read_pdf(pdf_path, pages="all", multiple_tables=True)

        # Initialize an empty list to store all DataFrames
        all_dfs = []

        # Iterate through each table and add a "Group" column based on the page number
        for i, table in enumerate(tables):
            # Add a "Group" column to the table
            table["Group"] = i + 1  # Group 1 for Page 1, Group 2 for Page 2, etc.
            # Append the table to the list
            all_dfs.append(table)

        # Combine all DataFrames into a single DataFrame
        df = pd.concat(all_dfs, ignore_index=True)

        # Rename columns for easier access (if necessary)
        df.columns = ["Maths", "Physics", "English", "Economics", "Biology", "Group"]

        # Convert marks to numerical data types
        df["Maths"] = pd.to_numeric(df["Maths"], errors="coerce")
        df["Physics"] = pd.to_numeric(df["Physics"], errors="coerce")
        df["English"] = pd.to_numeric(df["English"], errors="coerce")
        df["Economics"] = pd.to_numeric(df["Economics"], errors="coerce")
        df["Biology"] = pd.to_numeric(df["Biology"], errors="coerce")
        df["Group"] = pd.to_numeric(df["Group"], errors="coerce")

        # Drop rows with missing values (if any)
        df.dropna(inplace=True)

        # Filter the DataFrame based on the criteria
        filtered_df = df[(df["Physics"] >= physics_min_marks) & (df["Group"].between(group_min, group_max))]

        # Calculate the total Maths marks
        total_maths_marks = filtered_df["Maths"].sum()

        # Return the result as JSON
        return json.dumps({"total_maths_marks": total_maths_marks}, indent=4)

    except Exception as e:
        return json.dumps({"error": f"An error occurred: {str(e)}"}, indent=4)

#################################################################################################

# Q_10

def convert_pdf_to_markdown(input_text: str, pdf_path: str) -> str:
    """
    Converts a PDF file to Markdown format, formats it using Prettier, and returns the formatted Markdown content.

    Args:
        input_text (str): The input text containing the task description.
        pdf_path (str): The path to the PDF file to be converted.

    Returns:
        str: The formatted Markdown content or an error message.
    """
    try:
        # Step 1: Extract text from the PDF
        extracted_text = extract_text(pdf_path)
        if not extracted_text.strip():
            return "Error: No content extracted from the PDF."

        # Step 2: Convert the extracted text to Markdown
        markdown_content = markdownify.markdownify(extracted_text, heading_style="ATX")

        # Step 3: Save the Markdown content to a temporary file
        temp_markdown_path = "temp_markdown.md"
        with open(temp_markdown_path, "w", encoding="utf-8") as md_file:
            md_file.write(markdown_content)

        # Step 4: Format the Markdown file using Prettier
        try:
            subprocess.run(
                ["npx", "prettier", "--write", temp_markdown_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            return f"Error: Prettier formatting failed. {e.stderr.decode('utf-8')}"

        # Step 5: Read the formatted Markdown content
        with open(temp_markdown_path, "r", encoding="utf-8") as md_file:
            formatted_markdown = md_file.read()

        # Step 6: Clean up the temporary file
        os.remove(temp_markdown_path)

        return formatted_markdown

    except Exception as e:
        return f"An error occurred: {str(e)}"

# Example usage
if __name__ == "__main__":
    # Input text
    input_text = """
    Convert the PDF to Markdown: Extract the content from the PDF file. Accurately convert the extracted content into Markdown format, preserving the structure and formatting as much as possible.
    Format the Markdown: Use Prettier version 3.4.2 to format the converted Markdown file.
    Submit the Formatted Markdown: Provide the final, formatted Markdown file as your submission.
    """

    # Path to the PDF file
    pdf_path = "sample_document.pdf"  # Replace with the actual path to your PDF file

    # Convert the PDF to Markdown
    result = convert_pdf_to_markdown(input_text, pdf_path)
    print(result)