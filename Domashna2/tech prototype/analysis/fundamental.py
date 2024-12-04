
def get_fundamental_metrics(stock_data):
    total_turnover = sum(clean_and_convert(row['Вкупен промет во денари']) for row in stock_data)
    average_price = sum(clean_and_convert(row['Просечна цена']) for row in stock_data) / len(stock_data) if stock_data else 0
    max_price = max(clean_and_convert(row['Мак.']) for row in stock_data)
    min_price = min(clean_and_convert(row['Мин.']) for row in stock_data)
    total_quantity = sum(int(row['Количина']) for row in stock_data)

    return {
        "Total Turnover": f"{total_turnover:,.2f} MKD",
        "Average Price": f"{average_price:,.2f} MKD",
        "Max Price": f"{max_price:,.2f} MKD",
        "Min Price": f"{min_price:,.2f} MKD",
        "Total Quantity": f"{total_quantity:,} units"
    }

def clean_and_convert(value):
    if isinstance(value, str):
        value = value.replace('.', '').replace(',', '.')
    return float(value)
