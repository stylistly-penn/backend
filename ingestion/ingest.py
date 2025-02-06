import concurrent.futures
import requests
import json
import pandas as pd

# Load the CSV file
jcrew_df = pd.read_csv("./jcrew.csv")
uniqlo_df = pd.read_csv("./uniqlo.csv")

# Define the regex with a capturing group
regex = r"(\$\d+(?:\.\d+)?)"

# Use str.extract to extract the first match
jcrew_df["Cost"] = jcrew_df["Cost"].str.extract(regex)
uniqlo_df["Cost"] = uniqlo_df["Cost"].str.extract(regex)


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
def create_item(row, token, brand):
    url = "http://localhost:8000/items/"

    # Debug: Check each expected field for NaN and log if present
    fields_to_check = {
        "description": row.get("Item"),
        "Cost": row.get("Cost"),
        "item_url": row.get("Item Url"),
        "product_url": row.get("Product Url"),
        "RGB": row.get("RGB"),
    }
    for field_name, value in fields_to_check.items():
        if pd.isna(value):
            print(f"DEBUG: Field '{field_name}' is NaN for row: {row.to_dict()}")

    # Convert cost to float. If the value is invalid, log and return None.
    try:
        price_value = float(row["Cost"][1:])
    except Exception as e:
        print(f"DEBUG: Could not convert cost '{row['Cost']}' to float. Error: {e}")
        return None

    # For string fields, replace NaN with an empty string
    description = row["Item"] if not pd.isna(row["Item"]) else ""
    item_url = row["Item Url"] if not pd.isna(row["Item Url"]) else ""
    product_url = row["Product Url"] if not pd.isna(row["Product Url"]) else ""
    RGB = row["RGB"] if not pd.isna(row["RGB"]) else ""

    data = {
        "description": description,
        "price": price_value,
        "brand": brand,
        "item_url": item_url,
        "product_url": product_url,
        "RGB": RGB,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",  # Ensure token is included
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    if response.status_code != 201:
        print(
            f"❌ Failed to create item: {response.text}, brand: {brand}, code: {response.status_code}"
        )
    return response


# Step 3: Process the dataframe in parallel with authentication
def process_dataframes(dfs):
    for df, brand in dfs:
        print("🚀 Processing dataframe for brand: ", brand)
        token = get_auth_token()
        if not token:
            print("❌ Stopping script because authentication failed.")
            return []

        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Map the create_item function to each row in the dataframe
            futures = [
                executor.submit(create_item, row, token, brand)
                for index, row in df.iterrows()
            ]
            # Wait for all futures to complete and get the results
            results = [
                future.result() for future in concurrent.futures.as_completed(futures)
            ]
        if all(result and result.status_code == 201 for result in results):
            print("✅ All items processed for brand: ", brand)
        else:
            print("❌ Some items failed to process for brand: ", brand)
        return results


# Run the script
# process_dataframes([[jcrew_df, "J. Crew"]])
process_dataframes([[uniqlo_df, "Uniqlo"]])
