# -*- coding: utf-8 -*-

from flask import Blueprint, jsonify, render_template, request
from searcher import Searcher, Input

api = Blueprint('api', __name__)
searcher = Searcher()

@api.route('/search', methods=['GET'])
def search():

    searcher_input = Input(request.args)
    products = searcher.search(lat=lat, lng=lng, radius=radius, count=count, tags=tags)
    return jsonify({'products': products})
