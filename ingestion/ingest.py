import requests
import json
import pandas as pd
import math
import glob
import os
from urllib.parse import urlparse


def clean_jcrew_url(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"


pd.set_option("display.max_colwidth", None)

# Load the CSV files
folder_path = "./jcrew"

# Get all CSV file paths inside the folder
csv_files = glob.glob(os.path.join(folder_path, "*.csv"))
print(csv_files)
# Read all CSV files and concatenate them into one DataFrame
jcrew_df = pd.concat((pd.read_csv(file) for file in csv_files), ignore_index=True)

jcrew_df["Product Url"] = jcrew_df["Product Url"].apply(clean_jcrew_url)
jcrew_df["Product Id"] = jcrew_df["Product Url"].str.split("/").str[-1]
print(jcrew_df["Product Url"])

uniqlo_df = pd.read_csv("./uniqlo.csv")
uniqlo_df["Product Id"] = uniqlo_df["Product Url"].str.split("/").str[-2]

# Use a regex to extract cost values
regex = r"(\$\d+(?:\.\d+)?)"
jcrew_df["Cost"] = jcrew_df["Cost"].str.extract(regex)
uniqlo_df["Cost"] = uniqlo_df["Cost"].str.extract(regex)


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
        print(f"Login successful! Token: {token}")
        return token
    else:
        print(f"❌ Login failed! Response: {response.text}")
        return None


def get_colors():
    url = "http://localhost:8000/colors/"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        # The API likely returns a paginated response with 'results' key
        # Return just the results array
        if isinstance(data, dict) and "results" in data:
            return data["results"]
        return data
    else:
        print(f"❌ Failed to fetch colors: {response.text}")
        return []


def parse_rgb(rgb_str):
    """Parses a string like '[59 68 52]' into a tuple of integers."""
    rgb_str = rgb_str.strip("[]")
    parts = rgb_str.split()
    return tuple(map(int, parts))


def euclidean_distance(rgb1, rgb2):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(rgb1, rgb2)))


def create_item(row, token, brand, colors):
    url = "http://localhost:8000/items/"

    # Debug: Check for missing fields
    fields_to_check = {
        "description": row.get("Item"),
        "Cost": row.get("Cost"),
        "product_id": row.get("Product Id"),
        "item_url": row.get("Item Url"),
        "product_url": row.get("Product Url"),
        "RGB": row.get("RGB"),
    }
    for field_name, value in fields_to_check.items():
        if pd.isna(value):
            print(f"DEBUG: Field '{field_name}' is NaN for row: {row.to_dict()}")

    try:
        price_value = float(row["Cost"].replace("$", ""))
    except Exception as e:
        print(f"DEBUG: Could not convert cost '{row['Cost']}' to float. Error: {e}")
        return None

    description = row["Item"] if not pd.isna(row["Item"]) else ""
    item_url = row["Item Url"] if not pd.isna(row["Item Url"]) else ""
    product_url = row["Product Url"] if not pd.isna(row["Product Url"]) else ""
    product_id = row["Product Id"] if not pd.isna(row["Product Id"]) else ""
    rgb_str = row["RGB"] if not pd.isna(row["RGB"]) else ""

    # Parse the item's RGB value for calculation
    try:
        item_rgb = parse_rgb(rgb_str)
    except Exception as e:
        print(f"DEBUG: Error parsing RGB '{rgb_str}': {e}")
        return None

    # Debug print to see what we're getting from the API
    print(f"DEBUG: First color from API: {colors[0] if colors else 'No colors'}")

    best_color = None
    best_distance = float("inf")
    for color in colors:
        try:
            # Make sure we're accessing the correct field from the color object
            color_code = color.get("code")
            if not color_code:
                print(f"DEBUG: No code field in color object: {color}")
                continue

            color_rgb = parse_rgb(color_code)
            distance = euclidean_distance(item_rgb, color_rgb)
            if distance < best_distance:
                best_distance = distance
                best_color = color
        except Exception as e:
            print(f"DEBUG: Error processing color {color}: {e}")

    if best_color is None:
        print("DEBUG: No suitable color found.")
        return None

    data = {
        "description": description,
        "price": price_value,
        "brand": brand,
        "item_url": item_url,
        "product_url": product_url,
        "product_id": product_id,
        "color_id": best_color["id"],
        "euclidean_distance": best_distance,
        "real_rgb": rgb_str,  # The original RGB from the CSV
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    response = requests.post(url, data=json.dumps(data), headers=headers)
    return response


def process_dataframes(dfs):
    # Fetch colors once at the start
    colors = get_colors()
    if not colors:
        print("❌ Stopping script because no colors were fetched.")
        return []

    for df, brand in dfs:
        print("🚀 Processing dataframe for brand:", brand)
        token = get_auth_token()
        if not token:
            print("❌ Stopping script because authentication failed.")
            return []

        # Group the dataframe by "Product Url"
        grouped = df.groupby("Product Url")
        all_results = []
        for product_url, group in grouped:
            print(f"Ingesting Item: {product_url}")
            # Get unique RGB values for this product
            unique_rgbs = group["RGB"].unique()
            for rgb in unique_rgbs:
                # Choose one representative row for this RGB value
                row = group[group["RGB"] == rgb].iloc[0]
                # Pass the colors to create_item
                response = create_item(row, token, brand, colors)
                if response:
                    result_text = f"status {response.status_code}"
                else:
                    result_text = "FAILED"
                print(f"\tRGB: {rgb} - result: {result_text}")
                all_results.append(response)
        return all_results


# Run the script (choose one or both dataframes)
process_dataframes([[jcrew_df, "J. Crew"]])
process_dataframes([[uniqlo_df, "Uniqlo"]])
