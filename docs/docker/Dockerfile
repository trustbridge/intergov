FROM python:3.8

WORKDIR /app

RUN apt-get update && \
    apt-get -y install graphviz && \
    apt-get -y install enchant && \
    apt-get -y install plantuml

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
