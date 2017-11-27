# ELISA Information Extraction Demo
---------------------------

ELISA information extraction demo has three components:
1. a GUI for name tagging and linking for 282 languages.
2. APIs for name tagging, linking, transliteration and localization.
3. a Heatmap that can monitor various topics of incidents happening in the world.

## Install

1. Clone the project.

2. Make sure any version of python3 is installed.

3. Use pip3 to install python modules listed in `lorelei_demo/requirements.txt` 

4. Download the nltk sentence segmentation model: `python3 -m nltk.downloader punkt -d data/nltk_data`.

5. Start the demo: `python3 lorelei_demo/run.py`.

6. Testing:
    * Demo GUI: [http://0.0.0.0:3300/elisa_ie](http://0.0.0.0:3300/elisa_ie) (only English model is included, for models of the 282 languages, please contact us.)
    * API: [http://0.0.0.0:3300/elisa_ie/api](http://0.0.0.0:3300/elisa_ie/api)
    * Heatmap: [http://0.0.0.0:3300/elisa_ie/heatmap](http://0.0.0.0:3300/elisa_ie/heatmap).

## Name Tagger

The name tagger is a separate program by itself: `lorelei_demo/name_tagger/theano`.

An example of how to do training and inference, as well as the format of the data, are provided at: `lorelei_demo/name_tagger/theano/example`.

## Citation


## Contact
   * Boliang Zhang zhangb8@rpi.edu
   * Xiaoman Pan panx2@rpi.edu
   * Heng Ji jih@rpi.edu