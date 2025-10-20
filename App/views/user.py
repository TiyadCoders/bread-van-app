from flask import Blueprint, render_template, jsonify, request, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user as jwt_current_user

from.index import index_views

from App.controllers.user import (
    create_user,
    get_all_users,
    get_all_users_json,
    get_all_drivers_json,
    get_user_by_id,
    get_driver_by_id
)

user_views = Blueprint('user_views', __name__, template_folder='../templates')

@user_views.route('/users', methods=['GET'])
def get_user_page():
    users = get_all_users()
    return render_template('users.html', users=users)

@user_views.route('/static/users', methods=['GET'])
def static_user_page():
  return send_from_directory('static', 'static-user.html')


'''
API Routes
'''

@user_views.route('/api/users', methods=['GET'])
@jwt_required()
def get_users_action():
    users = get_all_users_json()
    return jsonify({'data': users})

@user_views.route('/api/users/<int:id>', methods=['GET'])
@jwt_required()
def get_user_action(id):
    user = get_user_by_id(id)
    if not user:
        return jsonify(message="User not found"), 404
    return jsonify({'data': user.get_json()})


@user_views.route('/api/users/inbox', methods=['GET'])
@jwt_required()
def get_user_inbox():
    # Get filter from query parameters (e.g., ?filter=requested or ?filter=confirmed or ?filter=all)
    filter_param = request.args.get('filter', None)
    return jsonify({'data': jwt_current_user.get_inbox_data(filter=filter_param)})


@user_views.route('/api/drivers', methods=['GET'])
def get_drivers_action():
    drivers = get_all_drivers_json()
    return jsonify({'data': drivers})

@user_views.route('/api/drivers/<int:id>', methods=['GET'])
def get_driver_action(id):
    driver = get_driver_by_id(id)
    if not driver:
        return jsonify(message="Driver not found"), 404
    return jsonify({'data': driver.get_json()})
