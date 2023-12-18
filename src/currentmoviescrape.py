import os
import datetime
import pandas as pd
import gspread
from google.oauth2 import service_account
import requests
from bs4 import BeautifulSoup
import re

def get_movie_information(url):
    response = requests.get(url)
    
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        movie_cards = soup.find_all('li', class_='poster-card')
        
        movie_data = []

        for movie_card in movie_cards:
            title_elem = movie_card.find('span', class_='heading-style-1')
            release_date_elem = movie_card.find('span', class_='sr-only')

            if title_elem and release_date_elem:
                # Remove the year from the title and extra space
                title = re.sub(r'\s*\(\d{4}\)$', '', title_elem.text.strip())
                release_text = release_date_elem.text

                if 'Released' in release_text:
                    # Extract the release date
                    release_date = release_text.split('Released ')[1]
                else:
                    release_date = "Release date not found"

                movie_data.append([title, release_date])

        return movie_data

    else:
        print("Failed to retrieve the web page. Status code:", response.status_code)
        return None

def write_to_google_sheets(movie_data, google_sheet_key):
    creds = service_account.Credentials.from_service_account_file('BBKey.json', scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
    client = gspread.Client(auth=creds)
    client.login()
    spreadsheet = client.open_by_key(google_sheet_key)

    # Try to get the existing 'All Movies' worksheet
    try:
        worksheet = spreadsheet.worksheet('All Movies')
    except gspread.exceptions.WorksheetNotFound:
        # If it doesn't exist, create a new one
        worksheet = spreadsheet.add_worksheet('All Movies', 1, 2)

    worksheet.clear()

    # Remove movies that are more than 6 weeks old
    today = datetime.datetime.now()
    movie_data = [movie for movie in movie_data if movie[1] == "Release date not found" or movie[1].endswith("days") or (parse_release_date(movie[1]) and (today - parse_release_date(movie[1])).days <= 42)]

    # Write data to the sheet
    header = ['Title', 'Release Date']
    worksheet.update('A1:B', values=[header] + movie_data)
    print("Data for all movies has been uploaded to Google Sheets.")

def parse_release_date(release_date):
    try:
        # Remove suffixes (st, nd, rd, th)
        release_date = re.sub(r'(?<=\d)(st|nd|rd|th)', '', release_date)
        # Parse and format the date
        return datetime.datetime.strptime(release_date, "%a, %B %d").replace(year=datetime.datetime.now().year)
    except ValueError:
        return None

if __name__ == "__main__":
    url = "https://www.fandango.com/movies-in-theaters"
    google_sheet_key = '1JVvjE_cdoof9qEW7tFdaw7J1S7MExIjOAdr5JFNLOIM'

    movie_data = get_movie_information(url)

    if movie_data:
        print("Movie Data:")
        print(movie_data)

        write_to_google_sheets(movie_data, google_sheet_key)
