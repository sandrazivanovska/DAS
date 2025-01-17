FROM python:3.9

RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    libfreetype6-dev \
    libpng-dev \
    libopenblas-dev \
    liblapack-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev

RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xvzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib/ && \
    ./configure --prefix=/usr && \
    make && \
    make install

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5001

CMD ["python", "technical_analysis_app.py"]
