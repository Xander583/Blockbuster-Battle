import firebase_admin
from firebase_admin import credentials, db
import gspread
from fuzzywuzzy import process
import warnings

# Ignore the python-Levenshtein warning
warnings.filterwarnings("ignore", category=UserWarning, module="fuzzywuzzy")

# Initialize Firebase
cred = credentials.Certificate("FireKey.json")
app = firebase_admin.initialize_app(cred, {"databaseURL": "https://blockbuster-battle-default-rtdb.firebaseio.com"})

# Initialize Google Sheets
gc = gspread.service_account(filename="BBKey.json")
sheet = gc.open("BlockbusterTest").sheet1  # Assuming your sheet name is "BlockbusterTest"

# Get data from Firebase RTDB
ref = db.reference("/")  # Assuming the data is directly under the root path
data = ref.get()

# Iterate through each user in the database
for user_id, variables in data.items():
    if isinstance(variables, dict):
        movie_variables = {k: v for k, v in variables.items() if "upmovie" in k.lower()}
        
        # Iterate through each movie variable for the user
        for variable_name, variable_value in movie_variables.items():
            # Find the closest match in the Google Sheet (assuming "release" column is column 1)
            result = process.extractOne(variable_value, sheet.col_values(1), score_cutoff=70)
            
            # Check if a match is found
            if result and result[1] > 70:
                movie_title, confidence = result
                # If the match is above the threshold, update the variable
                ref.child(user_id).update({variable_name: movie_title})
                print(f"Updated variable for user {user_id}, variable {variable_name}: {variable_value} -> {movie_title}")
            else:
                print(f"No close match found for user {user_id}, variable {variable_name}: {variable_value}")
    else:
        print(f"Skipping user {user_id} because the data structure is not as expected.")

# Cleanup
firebase_admin.delete_app(app)
