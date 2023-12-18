import firebase_admin
from firebase_admin import credentials, db
import gspread
from fuzzywuzzy import process
import pandas as pd

# Initialize Firebase
cred = credentials.Certificate("FireKey.json")
app = firebase_admin.initialize_app(cred, {"databaseURL": "https://blockbuster-battle-default-rtdb.firebaseio.com"})

# Initialize Google Sheets
gc = gspread.service_account(filename="BBKey.json")
blockbuster_test_sheet = gc.open("BlockbusterTest").sheet1  # Assuming your sheet name is "BlockbusterTest"
leaderboard_sheet = gc.open("BlockbusterLeaderboard").sheet1  # Assuming your sheet name is "BlockbusterLeaderboard"

# Get data from Firebase RTDB
ref = db.reference("/")  # Assuming the data is directly under the root path
data = ref.get()

# Initialize an empty list to store user scores
user_scores_data = []

# Iterate through each user in the database
for user_id, variables in data.items():
    # Check if the user has any variables containing "premovie"
    if isinstance(variables, dict) and any(f"premovie{i}" in variables for i in range(1, 6)):
        # Extract the "name" variable for the user
        user_name = variables.get("name", "")

        # Initialize a variable to store the total score for the user
        score = 0

        # Iterate through each premovie variable for the user
        for i in range(1, 6):  # Assuming premovie variables are named premovie1 to premovie5
            variable_name = f"premovie{i}"
            variable_value = variables.get(variable_name, "")

            # Skip empty or non-string variables
            if not variable_value or not isinstance(variable_value, str):
                continue

            # Find the closest match in the Google Sheet (assuming "Release" column is column 1)
            result = process.extractOne(variable_value, blockbuster_test_sheet.col_values(1), score_cutoff=70)

            # Check if a match is found
            if result and result[1] > 70:
                movie_title, _ = result
                # Find the corresponding gross value in the "BlockbusterTest" sheet
                try:
                    # Find the row index of the matched movie title
                    row_index = blockbuster_test_sheet.col_values(1).index(movie_title) + 1
                    # Get the gross value from the "Gross" column (assuming "Gross" column is column 2)
                    gross_value = blockbuster_test_sheet.cell(row_index, 2).value
                except (ValueError, gspread.exceptions.CellNotFound) as e:
                    print(f"Error: Movie not found in BlockbusterTest: {movie_title}")
                    continue

                # Remove commas and dollar signs and convert to an integer
                gross_value = int(gross_value.replace(",", "").replace("$", ""))

                # Add the gross value to the total score
                score += (gross_value * i)

        print(f"User: {user_name}, Total Score: {score}")

        # Append the user and their total score to the list
        user_scores_data.append({"User": user_name, "Score": score})

# Create a DataFrame from the list
user_scores_data = sorted(user_scores_data, key=lambda x: x["Score"], reverse=True)

# Upload the user scores data to Firebase Realtime Database
leaderboard_ref = db.reference("/leaderboard")
leaderboard_ref.set(user_scores_data)

# Update the "BlockbusterLeaderboard" sheet with the new scores
leaderboard_sheet.clear()  # Clear the existing data in the sheet
header = list(user_scores_data[0].keys())  # Convert dict_keys to list
data = [[d.get(key, "") for key in header] for d in user_scores_data]  # Extract data

# Format the scores with dollar signs and commas without decimal places
formatted_data = [[name, "${:,.0f}".format(score) if isinstance(score, (int, float)) else score] for name, score in data]

leaderboard_sheet.append_row(header)  # Write the header to the sheet
leaderboard_sheet.append_rows(formatted_data)  # Write the formatted data to the sheet

# Cleanup
firebase_admin.delete_app(app)
