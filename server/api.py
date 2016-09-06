# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template, request
from searcher import Searcher, Input

api = Blueprint('api', __name__)
searcher = Searcher()

@api.route('/search', methods=['GET'])
def search():

    searcher_input = Input(request.args)
    if searcher_input.input_errors:
        return jsonify({'errors': searcher_input.input_errors}) , 400
    products = searcher.search(searcher_input)
    return jsonify({'products': products})
