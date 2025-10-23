"""
Railway Flask API for ThisIsMe Integration
Now supports:
 - /verify   → DHA ID Verification
 - /trace    → Trace API (Address, Employer, Phone)
"""

from flask import Flask, request, jsonify
import requests
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Certificate paths (same as before)
CERT_PATH = "www.fxcloudv2.co.za.pem"
KEY_PATH = "fxcloud.key"

# API Key for security
API_KEY = os.environ.get('API_KEY', 'dreamteam91frag')

def verify_api_key():
    """Check if API key is valid."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    token = auth_header.replace('Bearer ', '').strip()
    return token == API_KEY


# ===============================================================
# ✅ DHA Verification Endpoint
# ===============================================================
@app.route('/verify', methods=['POST'])
def verify_id():
    """Submit ID for DHA verification via ThisIsMe."""
    if not verify_api_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        identity_number = data.get("identity_number")
        reference = data.get("reference", "")

        if not identity_number:
            return jsonify({"success": False, "error": "identity_number is required"}), 400

        url = "https://uat-api.thisisme.com/dhadatapro"
        headers = {"content-type": "application/json"}
        payload = {
            "identity_number": identity_number,
            "disable_report": "true",
            "reference": reference
        }

        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )

        # If accepted, ThisIsMe sometimes returns 303 (check later)
        result_json = {}
        try:
            result_json = response.json()
        except:
            pass

        return jsonify({
            "success": response.status_code in [200, 227, 303],
            "status_code": response.status_code,
            "data": result_json,
            "request_id": result_json.get("request_id") if isinstance(result_json, dict) else None
        }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "type": type(e).__name__}), 500


# ===============================================================
# ✅ TRACE Endpoint
# ===============================================================
@app.route('/trace', methods=['POST'])
def trace_lookup():
    """Perform Trace lookup via ThisIsMe API."""
    if not verify_api_key():
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json()
        identity_number = data.get("identity_number")
        reference = data.get("reference", "")

        if not identity_number:
            return jsonify({"success": False, "error": "identity_number is required"}), 400

        url = "https://uat-api.thisisme.com/v4/trace/"
        headers = {"content-type": "application/json"}
        payload = {
            "identity_number": identity_number,
            "disable_report": "true",
            "reference": reference
        }

        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=45
        )

        result_json = {}
        try:
            result_json = response.json()
        except:
            pass

        return jsonify({
            "success": response.status_code == 200,
            "status_code": response.status_code,
            "data": result_json
        }), response.status_code

    except Exception as e:
        return jsonify({"success": False, "error": str(e), "type": type(e).__name__}), 500


# ===============================================================
# ✅ Health & Root Routes
# ===============================================================
@app.route('/')
def home():
    return jsonify({
        "status": "online",
        "service": "ThisIsMe API Middleware",
        "version": "2.0",
        "endpoints": {
            "verify": "POST /verify",
            "trace": "POST /trace"
        }
    })

@app.route('/health')
def health():
    return "OK", 200


# ===============================================================
# ✅ Start Server
# ===============================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

