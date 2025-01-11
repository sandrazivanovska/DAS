import matplotlib.pyplot as plt
import io
import base64

def generate_bar_chart(positive_count, negative_count, neutral_count):
    labels = ['Positive', 'Neutral', 'Negative']
    values = [positive_count, neutral_count, negative_count]

    plt.figure(figsize=(8, 6))
    plt.bar(labels, values, color=['#5D6D7E', '#A9A9A9', '#2874A6'])
    plt.title("Sentiment Analysis Results")
    plt.ylabel("Number of Articles")
    plt.xlabel("Sentiment")
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url


def generate_filtered_line_chart(data, issuer_code, start_date, end_date):
    filtered_data = data[(data['Company Code'] == issuer_code) &
                         (data['Date'] >= start_date) &
                         (data['Date'] <= end_date)]

    if filtered_data.empty:
        raise ValueError(f"No data found for issuer {issuer_code} in the given date range.")

    sentiment_over_time = filtered_data.groupby(['Date', 'Sentiment']).size().unstack(fill_value=0)

    plt.figure(figsize=(10, 6))
    for sentiment in sentiment_over_time.columns:
        plt.plot(sentiment_over_time.index, sentiment_over_time[sentiment], label=sentiment, marker='o')

    plt.title(f"Sentiment Over Time for {issuer_code}", fontsize=16)
    plt.xlabel("Date", fontsize=12)
    plt.ylabel("Number of Articles", fontsize=12)
    plt.legend(title="Sentiment")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url
