from flask import Flask, jsonify, request, make_response, abort
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import jwt
import datetime

app = Flask(__name__)

# Secret key for JWT
app.config['SECRET_KEY'] = 'supersecretkey'

# In-memory database simulation
users = []
items = []

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('x-access-token')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = next(user for user in users if user['username'] == data['username'])
        except:
            return jsonify({'message': 'Token is invalid!'}), 403
        return f(current_user, *args, **kwargs)
    return decorated

# Helper functions
def get_user_by_username(username):
    return next((user for user in users if user['username'] == username), None)

def generate_token(user):
    token = jwt.encode({
        'username': user['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return token

# Routes

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='sha256')
    new_user = {
        'username': data['username'],
        'password': hashed_password
    }
    if get_user_by_username(data['username']):
        return jsonify({'message': 'User already exists!'}), 409
    users.append(new_user)
    return jsonify({'message': 'User registered successfully!'}), 201

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user = get_user_by_username(data['username'])
    if not user or not check_password_hash(user['password'], data['password']):
        return make_response('Could not verify', 401, {'WWW-Authenticate': 'Basic realm="Login required!"'})
    token = generate_token(user)
    return jsonify({'token': token})

@app.route('/api/user', methods=['GET'])
@token_required
def get_all_users(current_user):
    return jsonify({'users': users})

@app.route('/api/user/<username>', methods=['GET'])
@token_required
def get_one_user(current_user, username):
    user = get_user_by_username(username)
    if not user:
        abort(404)
    return jsonify(user)

@app.route('/api/user/<username>', methods=['DELETE'])
@token_required
def delete_user(current_user, username):
    user = get_user_by_username(username)
    if not user:
        abort(404)
    users.remove(user)
    return jsonify({'message': f'User {username} deleted!'})

@app.route('/api/items', methods=['POST'])
@token_required
def create_item(current_user):
    data = request.get_json()
    item = {
        'id': len(items) + 1,
        'name': data['name'],
        'owner': current_user['username']
    }
    items.append(item)
    return jsonify({'message': 'Item created successfully!', 'item': item}), 201

@app.route('/api/items', methods=['GET'])
@token_required
def get_all_items(current_user):
    user_items = [item for item in items if item['owner'] == current_user['username']]
    return jsonify({'items': user_items})

@app.route('/api/items/<int:item_id>', methods=['GET'])
@token_required
def get_one_item(current_user, item_id):
    item = next((item for item in items if item['id'] == item_id and item['owner'] == current_user['username']), None)
    if not item:
        abort(404)
    return jsonify(item)

@app.route('/api/items/<int:item_id>', methods=['PUT'])
@token_required
def update_item(current_user, item_id):
    data = request.get_json()
    item = next((item for item in items if item['id'] == item_id and item['owner'] == current_user['username']), None)
    if not item:
        abort(404)
    item['name'] = data.get('name', item['name'])
    return jsonify({'message': 'Item updated successfully!', 'item': item})

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@token_required
def delete_item(current_user, item_id):
    item = next((item for item in items if item['id'] == item_id and item['owner'] == current_user['username']), None)
    if not item:
        abort(404)
    items.remove(item)
    return jsonify({'message': 'Item deleted successfully!'})

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'message': 'Bad request!'}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'message': 'Resource not found!'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'message': 'Server error occurred!'}), 500

# Main entry point
if __name__ == '__main__':
    app.run(debug=True)