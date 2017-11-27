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
    * Demo GUI: [http://0.0.0.0:3300/elisa_ie](http://0.0.0.0:3300/elisa_ie) (only Hausa model is included, for models of the 282 languages, please contact us.)
    * API: [http://0.0.0.0:3300/elisa_ie/api](http://0.0.0.0:3300/elisa_ie/api)
    * Heatmap: [http://0.0.0.0:3300/elisa_ie/heatmap](http://0.0.0.0:3300/elisa_ie/heatmap).

## Name Tagger

The name tagger is a separate program by itself: `lorelei_demo/name_tagger/theano`.

An example of how to do training and inference, as well as the format of the data, are provided at: `lorelei_demo/name_tagger/theano/example`.

## Citation

[1] Boliang Zhang, Xiaoman Pan, Tianlu Wang, Ashish Vaswani, Heng Ji, Kevin Knight, and Daniel Marcu. [Name Tagging for Low-Resource Incident Languages Based on Expectation-Driven Learning](http://nlp.cs.rpi.edu/paper/expectation2016.pdf), Proc. NAACL, 2016

[2] Xiaoman Pan, Boliang Zhang, Jonathan May, Joel Nothman, Kevin Knight and Heng Ji. [Cross-lingual Name Tagging and Linking for 282 Languages](http://nlp.cs.rpi.edu/paper/282elisa2017.pdf), Proc. ACL, 2017

[3] Boliang Zhang, Di Lu, Xiaoman Pan, Ying Lin, Halidanmu Abudukelimu, Heng Ji, Kevin Knight. Embracing Non-Traditional Linguistic Resources for Low-resource Language Name Tagging, Proc. IJCNLP, 2017

## Contact
   * Boliang Zhang zhangb8@rpi.edu
   * Xiaoman Pan panx2@rpi.edu
   * Heng Ji jih@rpi.edu