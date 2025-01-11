import matplotlib.pyplot as plt
import io
import base64

def generate_prediction_chart(predictions):
    dates = ['1 Day', '1 Week', '1 Month']
    values = [round(predictions[i], 2) for i in [0, 6, 29] if i < len(predictions)]

    plt.figure(figsize=(10, 5))
    plt.plot(dates[:len(values)], values, marker='o', color='blue', label='Predicted Prices', zorder=5)
    plt.fill_between(
        dates[:len(values)],
        [v * 0.95 for v in values],
        [v * 1.05 for v in values],
        color='blue',
        alpha=0.2,
        label='Confidence Interval (95%)'
    )
    plt.title('Predictions for Future Periods')
    plt.xlabel('Time Period')
    plt.ylabel('Price (USD)')
    plt.xticks(rotation=45)
    plt.legend()
    plt.grid()

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    chart_url = base64.b64encode(buf.getvalue()).decode('utf8')
    buf.close()
    plt.close()
    return chart_url
