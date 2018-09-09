FROM python:3.6

MAINTAINER Boliang Zhang "zhangb8@rpi.edu"

WORKDIR /usr/src/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install nltk sentence segmentation model
RUN python3 -m nltk.downloader -d /usr/local/nltk_data punkt

COPY data ./data
COPY lorelei_demo ./lorelei_demo

#
# Set environmental variables
#
# Add project path to PYTHONPATH
ENV PYTHONPATH="/:$PYTHONPATH:/usr/src/app/"


################################################################################
#
# layers above should be fixed
#
################################################################################

ENTRYPOINT ["python3"]
CMD ["/usr/src/app/lorelei_demo/run.py"]


################################################################################
#
# notes
#
################################################################################

#
# build docker
#
# docker build -t elisarpi/elisa-ie .
# docker push elisarpi/elisa-ie

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
# 5. Other languages are trained from automatically generated training data
# using Wikipedia markups.

