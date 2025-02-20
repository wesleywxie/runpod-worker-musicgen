FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04
LABEL maintainer="wesley.w.xie@gmail.com"

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 -y

RUN apt update && apt install -y --no-install-recommends \
        bash ca-certificates wget git gcc sudo libgl1 libglib2.0-dev python3-dev google-perftools \
        && rm -rf /var/lib/apt/lists/*

RUN useradd --home /app -M app -K UID_MIN=10000 -K GID_MIN=10000 -s /bin/bash
RUN mkdir /app
RUN chown app:app -R /app
RUN usermod -aG sudo app
RUN echo 'app ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers

USER app
WORKDIR /app/

RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-$(uname -m).sh
RUN bash ./Miniconda3-latest-Linux-$(uname -m).sh -b \
    && rm -rf ./Miniconda3-latest-Linux-$(uname -m).sh

ENV PATH=/app/miniconda3/bin/:$PATH

RUN conda install python="3.10" -y

ADD . /app
WORKDIR /app

RUN sudo chmod +x /app/start.sh
RUN pip install -r requirements.txt
RUN python3 /app/downloader.py

CMD ["/app/start.sh"]