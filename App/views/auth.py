from flask import Blueprint, render_template, jsonify, request, flash, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user, unset_jwt_cookies, set_access_cookies


from.index import index_views

from App.controllers.auth import login
from App.controllers.user import register_user

auth_views = Blueprint('auth_views', __name__, template_folder='../templates')


'''
Page/Action Routes
'''

@auth_views.route('/identify', methods=['GET'])
@jwt_required()
def identify_page():
    return render_template('message.html', title="Identify", message=f"You are logged in as {current_user.id} - {current_user.username}")


@auth_views.route('/login', methods=['POST'])
def login_action():
    data = request.form
    token = login(data['username'], data['password'])
    response = redirect(request.referrer)
    if not token:
        flash('Bad username or password given'), 401
    else:
        flash('Login Successful')
        set_access_cookies(response, token)
    return response

@auth_views.route('/logout', methods=['GET'])
def logout_action():
    response = redirect(request.referrer)
    flash("Logged Out!")
    unset_jwt_cookies(response)
    return response

'''
API Routes
'''

@auth_views.route('/api/login', methods=['POST'])
def user_login_api():
  data = request.json
  token = login(data['username'], data['password'])
  if not token:
    return jsonify(message='bad username or password given'), 401
  response = jsonify(access_token=token)
  set_access_cookies(response, token)
  return response

@auth_views.route('/api/identify', methods=['GET'])
@jwt_required()
def identify_user():
    return jsonify({'data': current_user.get_json()})

@auth_views.route('/api/register', methods=['POST'])
def user_register_api():
    data = request.json

    # Validate required fields
    required_fields = ['username', 'password', 'firstName', 'lastName', 'role']
    missing_fields = [field for field in required_fields if field not in data]

    if missing_fields:
        return jsonify(message=f"Missing required fields: {', '.join(missing_fields)}"), 400

    # Get street (optional, required only for residents)
    street = data.get('street', '')

    # Register the user
    user = register_user(
        username=data['username'],
        password=data['password'],
        firstname=data['firstName'],
        lastname=data['lastName'],
        role=data['role'],
        street=street
    )

    if not user:
        return jsonify(message="Registration failed. User may already exist or invalid data provided."), 400

    # Return success with user data
    return jsonify(
        message="User registered successfully",
        data=user.get_json()
    ), 201

@auth_views.route('/api/logout', methods=['GET'])
def logout_api():
    response = jsonify(message="Logged Out!")
    unset_jwt_cookies(response)
    return response
