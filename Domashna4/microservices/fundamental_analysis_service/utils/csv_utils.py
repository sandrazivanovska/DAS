
import csv
import os
import sys

csv.field_size_limit(14 * 1024 * 1024)

OUTPUT_CSV = "sentiment_analysis_results.csv"

def initialize_csv():

    try:
        if not os.path.exists(OUTPUT_CSV):
            with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Document ID", "Date", "Description", "Content",
                    "Company Code", "Company Name", "Sentiment", "Probability"
                ])
            print(f"CSV file initialized at {OUTPUT_CSV}.")
        else:
            print(f"CSV file already exists at {OUTPUT_CSV}. No initialization needed.")
    except Exception as e:
        print(f"Error initializing CSV file: {e}")


def read_csv_file():
    if not os.path.exists(OUTPUT_CSV):
        raise FileNotFoundError(f"CSV file not found at {OUTPUT_CSV}.")

    with open(OUTPUT_CSV, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        print(f"Number of rows read from CSV: {len(rows)}")
        return rows
