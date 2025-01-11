# Користи официјална Python слика како основа
FROM python:3.9-slim

# Постави работна папка во контејнерот
WORKDIR /app

# Копирај ги сите потребни фајлови и директориуми во контејнерот
COPY . /app

# Инсталирај ги Python зависностите од requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Додај порта која ќе ја користи главната апликација
EXPOSE 8000

# Стартувај ја главната апликација
CMD ["python", "stock_insight_app.py"]
