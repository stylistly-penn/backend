import concurrent.futures
import requests
import json
import pandas as pd

# Load the CSV file
df = pd.read_csv("./jcrew.csv")

# Define the regex with a capturing group
regex = r"(\$\d+(?:\.\d+)?)"

# Use str.extract to extract the first match
df["Cost"] = df["Cost"].str.extract(regex)


# Parallelize requests for each row in the dataframe
def create_item(row):
    url = "http://localhost:8000/items/"
    data = {
        "description": row["Item"],
        "price": float(row["Cost"][1:]),
        "brand": "jcrew",
        "item_url": row["Item Url"],
        "RGB": row["RGB"],
    }
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response


# Function to process the dataframe in parallel
def process_dataframe(df):
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the create_item function to each row in the dataframe
        futures = [executor.submit(create_item, row) for index, row in df.iterrows()]
        # Wait for all futures to complete and get the results
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]
    return results


print(process_dataframe(df))
