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


# Step 1: Log in and Get the JWT Token
def get_auth_token():
    login_url = "http://localhost:8000/auth/login/"
    login_data = {"username": "testuser", "password": "testpassword"}
    headers = {"Content-Type": "application/json"}

    response = requests.post(login_url, data=json.dumps(login_data), headers=headers)

    if response.status_code == 200:
        token = response.cookies.get("access_token")
        if not token:
            print(f"❌ Login failed! No token returned: {response.text}")
            return None
        print(f"✅ Login successful! Token: {token}")
        return token
    else:
        print(f"❌ Login failed! Response: {response.text}")
        return None


# Step 2: Parallelize requests for each row in the dataframe
def create_item(row, token):
    url = "http://localhost:8000/items/"
    data = {
        "description": row["Item"],
        "price": float(row["Cost"][1:]),
        "brand": "jcrew",
        "item_url": row["Item Url"],
        "product_url": row["Product Url"],
        "RGB": row["RGB"],
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",  # Ensure token is included
    }

    print(f"🔎 DEBUG: Sending request to {url} with headers: {headers}")
    response = requests.post(url, data=json.dumps(data), headers=headers)

    print(f"🔎 DEBUG: Response Code: {response.status_code}, Body: {response.text}")
    return response


# Step 3: Process the dataframe in parallel with authentication
def process_dataframe(df):
    token = get_auth_token()
    if not token:
        print("❌ Stopping script because authentication failed.")
        return []

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Map the create_item function to each row in the dataframe
        futures = [
            executor.submit(create_item, row, token) for index, row in df.iterrows()
        ]
        # Wait for all futures to complete and get the results
        results = [
            future.result() for future in concurrent.futures.as_completed(futures)
        ]

    return results


# Run the script
print(process_dataframe(df))
