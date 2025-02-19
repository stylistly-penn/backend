import pandas as pd

# Load CSV
df = pd.concat([pd.read_csv(f"abercrombie_output_{i}.csv") for i in range(1, 35)], ignore_index=True)

initial_count = len(df)
# Drop duplicates based on 'Item' and 'Item Url', keeping the first occurrence
df = df.drop_duplicates(subset=['Item', 'Item Url'], keep='first')
final_count = len(df)
duplicates_count = initial_count - final_count

# Save the cleaned CSV
df = df.sort_values(by='Item')
df.to_csv("abercrombie_output_cleaned_womens.csv", index=False)

print("Duplicates removed. Cleaned data saved as 'cleaned_file.csv'.")


print(f"Initial entries: {initial_count}")
print(f"Duplicates removed: {duplicates_count}")
print(f"Final entries: {final_count}")


