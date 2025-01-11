from transformers import pipeline

classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")

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
