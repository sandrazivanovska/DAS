FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5010

CMD ["python", "scraping_app.py"]
