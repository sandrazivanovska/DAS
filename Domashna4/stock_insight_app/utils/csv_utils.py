import pandas as pd

def read_documents_from_csv(file_path, issuer_code):
    try:
        data = pd.read_csv(file_path, encoding='latin1')
        data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
        filtered_data = data[data['Company Code'] == issuer_code]
        return filtered_data
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return pd.DataFrame()
