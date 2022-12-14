# Build an image that can do inference in SageMaker
# for serving inferences in a stable way.

# GPU enabled image
FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04

# Install necessary dependencies for MMS and SageMaker Inference Toolkit
RUN apt-get -y update
    # apt-get install -y --no-install-recommends software-properties-common &&\
    # add-apt-repository -y ppa:deadsnakes/ppa
RUN apt-get install -y --no-install-recommends \
            build-essential \
            ca-certificates \
            openjdk-8-jdk-headless \
            curl \
            vim \
            # python3.8 \
            python3-pip \
            python3-setuptools \
    && rm -rf /var/lib/apt/lists/*

# set python3 as default
# RUN ln -s /usr/bin/python3 /usr/bin/python
# RUN ln -s /usr/bin/pip3 /usr/bin/pip

# Here we get all python packages. converting them from the poetry dependency manager
# There's substantial overlap between scipy and numpy that we eliminate by
# linking them together. Likewise, pip leaves the install caches populated which uses
# a significant amount of space. These optimizations save a fair amount of space in the
# image, which reduces start up time.
WORKDIR /opt/program
RUN pip3 install --upgrade pip
RUN pip3 install poetry
COPY pyproject.toml poetry.lock ./
RUN poetry install
# RUN poetry export --without-hashes --output ./requirements.txt
# RUN pip --no-cache-dir install -r requirements.txt

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/program:${PATH}"

# Set up the program in the image
COPY endpoint /opt/program/endpoint/

RUN poetry install

EXPOSE 8080

# starts the server which will handle sagemaker requests.
ENTRYPOINT [ "poetry","run", "python", "/opt/program/endpoint/server.py" ]
CMD ["serve"]