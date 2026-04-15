from flask import Flask, request, jsonify
import base64, json

app = Flask(__name__)

def decode_token(token):
    try:
        payload = token.split('.')[1]
        payload += '=' * (4 - len(payload) % 4)
        return json.loads(base64.b64decode(payload))
    except:
        return None

@app.route("/api/public")
def public():
    return jsonify({"message": "Endpoint public"})

@app.route("/api/profile")
def profile():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = decode_token(token)
    if not user:
        return jsonify({"error": "Non autorise"}), 401
    return jsonify({"user": user})

@app.route("/api/secrets")
def secrets():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = decode_token(token)
    if not user:
        return jsonify({"error": "Non autorise"}), 401
    return jsonify({"db_password": "prod-db-Password123", "svc_account": "svc-account", "svc_secret": "svc-acc-secret-XkP92mQz"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
