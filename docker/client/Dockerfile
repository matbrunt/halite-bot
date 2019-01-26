FROM python:3.6

RUN apt-get update && \
    apt-get install -y unzip

COPY Halite3Tools.zip /usr/src
WORKDIR /usr/src

RUN unzip Halite3Tools.zip && \
    cd hlt_client && \
    pip install -r requirements.txt && \
    python setup.py install

RUN hlt auth -k 8364:a50cfd22e63546a2a6505a2a3b22c49c