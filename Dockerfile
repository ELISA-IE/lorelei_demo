FROM ubuntu:latest

MAINTAINER Boliang Zhang "zhangb8@rpi.edu"

# Update OS
RUN apt-get update -y

# set locale to en_US.UTF-8 (this solves python3 encoding errors)
RUN apt-get install -y locales
RUN sed -i -e 's/# en_US.UTF-8 UTF-8/en_US.UTF-8 UTF-8/' /etc/locale.gen && \
    locale-gen
ENV LANG en_US.UTF-8
ENV LANGUAGE en_US:en
ENV LC_ALL en_US.UTF-8

# Install Python3
RUN apt-get install -y software-properties-common python-software-properties
RUN add-apt-repository ppa:fkrull/deadsnakes
RUN apt-get update -y
RUN apt-get install python3.6 -y
RUN apt-get install -y python3-pip python3.6-dev \
  && pip3 install --upgrade pip \
  && ln -s -f /usr/bin/python3.6 /usr/bin/python3
  
# Set the default directory for our environment
ENV HOME /
WORKDIR /

# Install app requirements
# we install all dependencies needed for our app. This is done before adding our application files to the 
# container because Docker will skip this step if requirements.txt has not changed upon subsequent builds. 
# Every Docker command builds a layer that is cached and if a single layer is changed, Docker will invalidate 
# this cache. This ordering will prevent our dependencies from being reinstalled upon changes to our 
# application code.
# Install app requirements
RUN pip3 install scipy numpy theano flask Flask-Cors jieba nltk

# Install nltk sentence segmentation model
RUN python3 -m nltk.downloader -d ./nltk_data punkt

#
# Set environmental variables
#
# Add project path to PYTHONPATH
ENV PYTHONPATH=$PYTHONPATH:/lorelei_demo
ENV PATH=$PATH:/lorelei_demo

#
# Create app directory
#
# add data first, this prevent re-adding data when source code changes.
RUN mkdir /lorelei_demo
ADD data /lorelei_demo/data
# add source code to image
ADD lorelei_demo /lorelei_demo/lorelei_demo

ENTRYPOINT ["python3"]
CMD ["lorelei_demo/lorelei_demo/run.py"]
