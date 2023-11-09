import os
import sys
import datetime
import requests
import pandas as pd
from requests_html import HTML

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def url_to_txt(url, filename="weekly.html", save=False):
    r = requests.get(url)
    if r.status_code == 200:
        html_text = r.text
        if save:
            with open(filename, 'w') as f:
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

    path = os.path.join(BASE_DIR, 'data')
    os.makedirs(path, exist_ok=True)
    filepath = os.path.join('data', f'week-{week_number}.csv')
    df.to_csv(filepath, index=False)
    return True


def run(start_week=None, weeks_ago=0):
    if start_week is None:
        now = datetime.datetime.now()
        for i in range(weeks_ago + 1):
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
