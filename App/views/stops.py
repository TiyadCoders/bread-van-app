from flask import Blueprint, render_template, jsonify, request, send_from_directory, flash, redirect, url_for
from flask_jwt_extended import jwt_required, current_user as jwt_current_user

from .index import index_views

from App.controllers.stop import (
    get_stop_by_id,
    get_all_stops,
    create_stop,
    complete_stop,
    delete_stop
)
from App.controllers.user import (
    get_driver_by_id
    )
from App.controllers.street import (
    get_street_by_string,
    create_street
)


stop_views = Blueprint('stop_views', __name__, template_folder='../templates')

@stop_views.route('/stops', methods=['GET'])
def get_stop_page():
    stops = get_all_stops()
    return render_template('stops.html', stops=stops)

@stop_views.route('/static/stops', methods=['GET'])
def static_stop_page():
    # static-stops.html not present in App/static; reuse existing static-user.html
    return send_from_directory('static', 'static-user.html')

@stop_views.route('/api/stops', methods=['GET'])
def get_stops_action():
    stops = get_all_stops()
    stops_json = [stop.get_json() for stop in stops] if stops else []
    return jsonify({'data': stops_json})

@stop_views.route('/api/stops/<int:id>', methods=['PATCH'])
def complete_stop_action(id):
    complete_stop(id)
    stop = get_stop_by_id(id)
    if not stop.has_arrived:
        return jsonify(message="Stop wasnt marked as arrived"), 400
    
    return jsonify(message="Stop successfully marked as arrived"), 200

@stop_views.route('/api/stops/<int:id>', methods=['DELETE'])
def delete_stop_action(id):
    delete_stop(id)
    return jsonify(message="Stop has been deleted successfully"), 200

@stop_views.route('/api/stops', methods=['POST'])
@jwt_required()
def create_stop_action():
    data = request.get_json()
    street_name = data.get('streetName')
    scheduled_date = data.get('scheduledDate')

    if not street_name or not scheduled_date:
        return jsonify(message="Missing data"), 400

    # ✅ Use the currently logged-in driver
    driver = jwt_current_user
    if not driver or driver.type != 'driver':
        return jsonify(message="Only drivers can create stops"), 403

    street_obj = get_street_by_string(street_name)
    if not street_obj:
        street_obj = create_street(street_name)
        if not street_obj:
            return jsonify(message="Failed to create street"), 400

    stop = create_stop(driver=driver, street=street_obj, scheduled_date=scheduled_date)
    if not stop:
        return jsonify(message="Failed to create stop"), 400

    return jsonify(message="Stop successfully created"), 201

