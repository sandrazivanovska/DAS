# Користи минимална Python слика како база
FROM python:3.9-slim

# Постави работен директориум
WORKDIR /app

# Копирај ги зависностите во контејнерот
COPY requirements.txt requirements.txt

# Инсталирај ги зависностите
RUN pip install --no-cache-dir -r requirements.txt

# Копирај ги сите останати датотеки од проектот во контејнерот
COPY . .

# Отвори порт 5000 за микросервисот
EXPOSE 5000

# Дефинирај командата за стартување на апликацијата
CMD ["python", "app.py"]
