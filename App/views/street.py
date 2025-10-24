from flask import Blueprint, jsonify
from App.controllers.street import get_all_streets_json

street_views = Blueprint('street_views', __name__, template_folder='../templates')

'''
API Routes
'''

@street_views.route('/api/streets', methods=['GET'])
def get_streets_action():
    streets = get_all_streets_json()
    return jsonify({'data': streets}), 200
