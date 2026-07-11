from flask import Blueprint, request, jsonify

user_bp = Blueprint('user', __name__)

@user_bp.route('/new-user', methods=['POST'])
def new_user():
    data = request.json
    email = data.get("email")

    # Only process new user logic here

    return jsonify({"message": "User added"})