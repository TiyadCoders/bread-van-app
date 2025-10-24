from flask import Blueprint, render_template, jsonify, request, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user as jwt_current_user

from .index import index_views

from App.controllers.user import (
    get_user_by_id,
    get_all_users,
    get_user_by_type
)


resident_views = Blueprint('resident_views', __name__, template_folder='../templates')

@resident_views.route('/residents', methods=['GET'])
def get_resident_page():
    users = get_all_users()
    residents = [u for u in users if getattr(u, 'type', None) == 'resident'] if users else []
    return render_template('residents.html', residents=residents)

@resident_views.route('/static/residents', methods=['GET'])
def static_resident_page():
        # point to existing static file
        return send_from_directory('static', 'static-users.html')

'''
API Routes
'''

@resident_views.route('/api/residents', methods=['GET'])
@jwt_required()
def get_residents_action():
    users = get_all_users()
    residents = [u for u in users if getattr(u, 'type', None) == 'resident'] if users else []
    residents_json = [resident.get_json() for resident in residents]
    return jsonify({'data': residents_json})

@resident_views.route('/api/residents/<int:id>', methods=['GET'])
@jwt_required()
def get_resident_action(id):
    resident = get_user_by_id(id)
    if not resident:
        return jsonify(message="Resident not found"), 404
    return jsonify({'data': resident.get_json()})

@resident_views.route('/api/residents/<int:id>/request', methods=['POST'])
@jwt_required()
def resident_request_action(id):
    resident = get_user_by_id(id)
    if not resident:
        return jsonify(message="Resident not found"), 404

    success = resident.request_stop()

    if not success:
        return jsonify(message="Request already exists for this street"), 400

    return jsonify(message="Request sent successfully"), 200
