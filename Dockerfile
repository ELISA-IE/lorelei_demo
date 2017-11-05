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
RUN pip3 install scipy numpy theano flask Flask-Cors jieba nltk requests

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
RUN mkdir /lorelei_demo/data
# add app
ADD data/app /lorelei_demo/data/app
# add gaz
RUN mkdir /lorelei_demo/data/name_tagger
ADD data/name_tagger/gaz /lorelei_demo/data/name_tagger/gaz
# add models
RUN mkdir /lorelei_demo/data/name_tagger/models
ADD data/name_tagger/models/zh /lorelei_demo/data/name_tagger/models/zh
ADD data/name_tagger/models/es /lorelei_demo/data/name_tagger/models/es
ADD data/name_tagger/models/en /lorelei_demo/data/name_tagger/models/en
ADD data/name_tagger/models/ug /lorelei_demo/data/name_tagger/models/ug
ADD data/name_tagger/models/ti /lorelei_demo/data/name_tagger/models/ti
ADD data/name_tagger/models/om /lorelei_demo/data/name_tagger/models/om


################################################################################
#
# layers above should be fixed
#
################################################################################

# add source code to image
ADD lorelei_demo /lorelei_demo/lorelei_demo

ENTRYPOINT ["python3"]
CMD ["lorelei_demo/lorelei_demo/run.py"]


################################################################################
#
# notes
#
################################################################################

#
# build docker
#
# docker build -t zhangb8/lorelei .

#
# NER model overview:
#
# 1. Chinese, English and Spanish:
# trained from multiple resources. they should have relatively good performance
# (as good as last year EDL16 top performers).
# 2. Uyghur:
# trained during LORELEI 2016 evaluation.
# 3. Amharic, Arabic, Farsi, Hausa, Hungarian, Russian, Somali, Turkish, Uzbek,
# Vietnamese, Yoruba:
# trained from LDC's LRLP data.
# 4. Oromo and Tigrinya (to-do):
# train during LORELEI 2017 evaluation.
# 5. Other languages are trained from automatically generated training data by
# using Wikipedia markups.

