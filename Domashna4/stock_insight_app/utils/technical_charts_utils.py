import matplotlib.pyplot as plt
import io
import base64

def generate_visualization_chart(trend_data):
    dates = trend_data.get('dates', [])
    sma = trend_data.get('SMA_20', [])
    ema = trend_data.get('EMA_20', [])
    wma = trend_data.get('WMA_50', [])

    plt.figure(figsize=(10, 6))
    plt.plot(dates, sma, label="SMA 20", marker='o')
    plt.plot(dates, ema, label="EMA 20", marker='o')
    plt.plot(dates, wma, label="WMA 50", marker='o')

    plt.title("Technical Indicators Over Time")
    plt.xlabel("Dates")
    plt.ylabel("Values")
    plt.legend()
    plt.grid()

    img = io.BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    chart_url = base64.b64encode(img.getvalue()).decode('utf8')
    plt.close()
    return chart_url
