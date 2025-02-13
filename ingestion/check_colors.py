import pandas as pd


def main():
    # Read the CSV file
    df = pd.read_csv("uniqlo.csv")

    # Group by "Product Url" and count unique "RGB" values per product
    unique_counts = df.groupby("Product Url")["RGB"].nunique()

    # Create a summary that counts how many products have each unique number of RGBs
    summary = unique_counts.value_counts().sort_index()

    # Print the header and table
    header = f"{'# unique colors':<15} | {'count':<5}"
    print(header)
    print("-" * len(header))
    for unique_color, count in summary.items():
        print(f"{unique_color:<15} | {count:<5}")

    # Identify and print product URLs that have exactly 2 unique RGB values,
    # along with the corresponding two colors.
    two_colors = unique_counts[unique_counts == 2]
    print("\nProducts with exactly 2 unique RGB values:")
    for product_url in two_colors.index:
        colors = df[df["Product Url"] == product_url]["RGB"].unique()
        print(f"{product_url}: {colors}")


if __name__ == "__main__":
    main()
