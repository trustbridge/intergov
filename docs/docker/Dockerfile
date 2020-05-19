FROM python:3.8

WORKDIR /app

RUN apt-get update && \
    apt-get -y install graphviz && \
    apt-get -y install enchant && \
    apt-get -y install plantuml

# copy requirements into the image
<<<<<<< HEAD
RUN mkdir -p docs
COPY docs/requirements.txt docs/
COPY requirements/ requirements/
# and install them
RUN pip install --no-cache-dir -r docs/requirements.txt
=======
RUN mkdir -p docs/docker
COPY docs/docker/requirements.txt docs/docker/
COPY requirements/ requirements/
# and install them
RUN pip install --no-cache-dir -r docs/docker/requirements.txt
>>>>>>> master
