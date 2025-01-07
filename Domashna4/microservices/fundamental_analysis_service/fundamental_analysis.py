from flask import Flask, request, jsonify
import csv
import os
from html.parser import HTMLParser
from transformers import pipeline
import sys
import csv
csv.field_size_limit(2**31 - 1)
app = Flask(__name__)
parser = HTMLParser()

OUTPUT_CSV = "sentiment_analysis_results.csv"

classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")


def initialize_csv():

    try:
        if not os.path.exists(OUTPUT_CSV):
            with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    "Document ID", "Date", "Description", "Content",
                    "Company Code", "Company Name", "Sentiment", "Probability"
                ])
            print("CSV file initialized.")
        else:
            print("CSV file already exists. No initialization needed.")
    except Exception as e:
        print(f"Error initializing CSV file: {e}")


def classify_sentiment(content):

    try:
        result = classifier(content[:500])[0]
        label = result["label"]
        score = result["score"]

        positive_keywords = ["profit", "growth", "success", "increase", "gain"]
        negative_keywords = ["loss", "decline", "decrease", "risk", "problem", "fall", "debt"]

        content_lower = content.lower()
        has_positive_keyword = any(word in content_lower for word in positive_keywords)
        has_negative_keyword = any(word in content_lower for word in negative_keywords)

        keyword_bonus = 0.1
        if has_positive_keyword:
            score += keyword_bonus
        if has_negative_keyword:
            score += keyword_bonus

        if label == "LABEL_0":
            sentiment = "Negative" if score > 0.35 or has_negative_keyword else "Neutral"
        elif label == "LABEL_1":
            sentiment = (
                "Neutral"
                if score > 0.75 and not (has_positive_keyword or has_negative_keyword)
                else ("Positive" if has_positive_keyword else "Negative")
            )
        elif label == "LABEL_2":
            sentiment = "Positive" if score > 0.35 or has_positive_keyword else "Neutral"
        else:
            sentiment = "Unknown"

        return sentiment, score
    except Exception as e:
        print(f"Error during sentiment classification: {e}")
        return "Error", 0.0


@app.route("/analyze_document", methods=["POST"])
def analyze_document():

    try:
        print("Received request data:", request.json)

        issuer_code = request.json.get("issuer_code")
        if not issuer_code:
            return jsonify({"status": "error", "message": "Issuer code is required."}), 400

        if not os.path.exists(OUTPUT_CSV):
            return jsonify({"status": "error", "message": "CSV file not found."}), 404

        filtered_documents = []
        with open(OUTPUT_CSV, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                if row["Company Code"] == issuer_code:
                    filtered_documents.append(row)

        if not filtered_documents:
            return jsonify({"status": "error", "message": f"No documents found for issuer {issuer_code}."}), 404

        return jsonify({"status": "success", "data": filtered_documents})

    except Exception as e:
        print(f"Unexpected error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    initialize_csv()
    app.run(host="0.0.0.0", port=5003)
