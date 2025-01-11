def process_chart_data(data):

    chart_data = {
        "dates": [row["Датум"] for row in data],
        "last_prices": [
            float(row["Цена на последна трансакција"].replace('.', '').replace(',', '.'))
            for row in data
        ],
        "max_prices": [
            float(row["Мак."].replace('.', '').replace(',', '.'))
            for row in data
        ],
        "min_prices": [
            float(row["Мин."].replace('.', '').replace(',', '.'))
            for row in data
        ],
    }
    return chart_data
