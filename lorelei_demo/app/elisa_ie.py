__author__ = 'boliangzhang'

import os
import json
from flask import request, render_template, Blueprint
import operator
from lorelei_demo.app.api import run_plain_text, get_status
from collections import OrderedDict


bp_elisa_ie = Blueprint('elisa_ie', __name__)


@bp_elisa_ie.route("/elisa_ie", methods=["GET", "POST"])
def demo_page_initialization():
    """
    elisa_ie main page
    """
    if request.method == "POST":
        # return login page
        return render_template("login.html")

    elif request.method == "GET":
        # verify dev code
        # dev_code = request.form['dev_code']
        # if dev_code != 'e420ie2':
        #     raise ValueError('dev code incorrect', status_code=406)

        # ======== get supported languages ======== #
        status = get_status()
        status = sorted(status.items(), key=operator.itemgetter(1, 0))
        online_languages = OrderedDict()

        for lang_code, (lang_name, _status, lang_group, direction) in status:
            if _status == 'online':
                online_languages[lang_code] = [lang_name, _status, lang_group,
                                               direction]

        return render_template('elisa_ie.html',
                               online_languages=online_languages)


@bp_elisa_ie.route('/elisa_ie/run', methods=["POST"])
def run():
    res = dict()
    selected_il = request.form.get('seleted_il')

    demo_input = request.form.get("demo_input")
    # print demo_input,'input'
    eval_tab, visualization_html = run_plain_text(selected_il, demo_input,
                                                  to_visualize=True)

    res['visualization_html'] = visualization_html

    return json.dumps(res)