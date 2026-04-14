from flask import Flask, request, jsonify
import os, requests

app = Flask(__name__)
KC = os.getenv("KEYCLOAK_URL", "http://keycloak:8080")
REALM = os.getenv("REALM", "corpcloud")

def verify_token(token):
    r = requests.get(f"{KC}/realms/{REALM}/protocol/openid-connect/userinfo",
                     headers={"Authorization": f"Bearer {token}"})
    return r.json() if r.status_code == 200 else None

@app.route("/api/public")
def public():
    return jsonify({"message": "Endpoint public — accessible sans authentification"})

@app.route("/api/profile")
def profile():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Non autorisé"}), 401
    return jsonify({"message": "Profil utilisateur", "user": user})

@app.route("/api/secrets")
def secrets():
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    user = verify_token(token)
    if not user:
        return jsonify({"error": "Non autorisé"}), 401
    return jsonify({
        "message": "Secrets de l'application",
        "db_password": "prod-db-P@ssw0rd!",
        "api_key": "sk-prod-X
