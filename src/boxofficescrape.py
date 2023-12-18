import os
import sys
import datetime
import requests
import pandas as pd
from requests_html import HTML
import gspread
from google.oauth2 import service_account
import gspread_dataframe as gd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def url_to_txt(url, filename="boxoffice.csv", save=True):
    r = requests.get(url)
    if r.status_code == 200:
        html_text = r.text
        if save:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_text)
        return html_text
    return None


def parse_and_extract(url, week_number):
    html_text = url_to_txt(url)
    if html_text is None:
        return False

    r_html = HTML(html=html_text)
    table_class = ".imdb-scroll-table"
    r_table = r_html.find(table_class)

    table_data = []
    header_names = []

    if len(r_table) == 0:
        return False

    parsed_table = r_table[0]
    rows = parsed_table.find("tr")
    header_row = rows[0]
    header_cols = header_row.find('th')
    header_names = [x.text for x in header_cols]

    for row in rows[1:]:
        cols = row.find("td")
        row_data = [col.text for col in cols]
        table_data.append(row_data)

    df = pd.DataFrame(table_data, columns=header_names)

    # Select only the "Release" and "Gross" columns
    df_selected = df[["Release", "Gross"]]

    filepath = os.path.join(BASE_DIR, 'boxoffice.csv')
    df_selected.to_csv(filepath, index=False)
    
    return True


def run(start_week=None, weeks_ago=0):
    if start_week is None:
        now = datetime.datetime.now()
        for i in range(3):
            start_week = now - datetime.timedelta(weeks=i)
            year = start_week.strftime("%Y")
            week_number = start_week.strftime("%U")
            week_number_str = f"{year}W{week_number}"
            url = f"https://www.boxofficemojo.com/weekly/{week_number_str}/"
            finished = parse_and_extract(url, week_number_str)
            if finished:
                print(f"Finished week {week_number_str}")
            else:
                print(f"Week {week_number_str} not finished")


if __name__ == "__main__":
    try:
        count = int(sys.argv[1])
    except:
        count = 0
    run(weeks_ago=count)

# Code for updating google sheet with new .csv
csv_file_path = 'boxoffice.csv' 
google_sheet_name = 'BlockbusterTest'
google_sheet_key = 'BBKey.json' 

# Set up Google Sheets API credentials
creds = service_account.Credentials.from_service_account_file(google_sheet_key, scopes=['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

# Authorize with Google Sheets
client = gspread.Client(auth=creds)
client.login()

# Open the Google Sheet
spreadsheet = client.open(google_sheet_name)
worksheet = spreadsheet.get_worksheet(0)  # Assumes you want to work with the first worksheet

# Clear the contents of the Google Sheet
worksheet.clear()

# Read the CSV file into a DataFrame
df = pd.read_csv(csv_file_path)

# Update the Google Sheet with the selected columns
gd.set_with_dataframe(worksheet, df[["Release", "Gross"]])

print(f"Selected data has been uploaded to '{google_sheet_name}' on Google Sheets.")
