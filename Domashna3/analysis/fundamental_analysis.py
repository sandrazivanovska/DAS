import csv
import requests
import html
import re
import pdfplumber
from io import BytesIO
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process
from html.parser import HTMLParser
from transformers import pipeline

parser = HTMLParser()

classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

OUTPUT_CSV = "sentiment_analysis_results.csv"

def initialize_csv():
    with open(OUTPUT_CSV, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "Document ID", "Date", "Description", "Content", "Company Code",
            "Company Name", "Sentiment", "Probability"
        ])

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


def process_document(document):
    try:
        content = document.get("content", "")
        document_id = document.get("documentId", "")
        description = document["layout"]["description"]
        content = html.unescape(content)
        content = re.sub(r"<[^>]*>", "", content)
        published_date = document["publishedDate"].split("T")[0]
        issuer_code = document["issuer"]["code"]
        display_name = document["issuer"]["localizedTerms"][0]["displayName"]

        if "this is automaticaly generated document".lower() in content.lower():
            return

        text = ""
        attachments = document.get("attachments", [])
        if attachments:
            attachment_id = attachments[0].get("attachmentId")
            file_name = attachments[0].get("fileName")

            if file_name.lower().endswith(".pdf"):
                attachment_url = f"https://api.seinet.com.mk/public/documents/attachment/{attachment_id}"
                response = requests.get(attachment_url)
                if response.status_code == 200:
                    pdf_file = BytesIO(response.content)
                    with pdfplumber.open(pdf_file) as pdf:
                        for page in pdf.pages:
                            text += page.extract_text()
                content += "\n"
                content += text

        if not content.strip():
            print(f"Empty text for document {document_id}, skipping sentiment analysis.")
            return

        sentiment, probability = classify_sentiment(content)

        try:
            with open(OUTPUT_CSV, mode="a", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow([
                    document_id,
                    published_date,
                    description,
                    content,
                    issuer_code,
                    display_name,
                    sentiment,
                    probability,
                ])
                print(f"Inserted document {document_id} into CSV file.")
        except Exception as e:
            print(f"Error writing document to CSV for {document_id}: {e}")

    except Exception as e:
        print(f"Error processing document {document_id}: {e}")

def process_page(page):
    payload = {
        "issuerId": 0,
        "languageId": 2,
        "channelId": 1,
        "dateFrom": "2024-06-01T00:00:00",
        "dateTo": "2024-12-31T23:59:59",
        "isPushRequest": False,
        "page": page,
    }
    headers = {"Content-Type": "application/json"}
    url = "https://api.seinet.com.mk/public/documents"

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        json_data = response.json()
        documents = json_data.get("data", [])
        with ThreadPoolExecutor(max_workers=4) as executor:
            for document in documents:
                executor.submit(process_document, document)

def fetch_pages_worker(pages_subset):
    for page in pages_subset:
        process_page(page)

def fetch():
    initialize_csv()

    processes = []
    chunk_size = 1030 // 8
    page_chunks = [range(i, min(i + chunk_size, 1030 + 1)) for i in range(1, 1030 + 1, chunk_size)]

    for chunk in page_chunks:
        p = Process(target=fetch_pages_worker, args=(chunk,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()

if __name__ == "__main__":
    fetch()
