FROM ubuntu:20.04

# install and build dependencies
RUN \
apt update \
  && \
apt install --yes \
  python3 \
  python3-pip \
  python-all-dev \
  libexiv2-dev \
  g++ \
  libboost-python-dev \
  exiv2 \
  && \
pip3 install py3exiv2

# "install" the app
COPY screenshot-memories.py /app/screenshot-memories.py

# copy some testdata
# override this step with a bind mount to convert data on the host
COPY testdata/ /data/

# convert the data
CMD python3 /app/screenshot-memories.py /data/*
