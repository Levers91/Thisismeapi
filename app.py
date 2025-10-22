"""
Railway Flask API for ThisIsMe Integration
Save this as: app.py
"""

from flask import Flask, request, jsonify
import requests
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Certificate paths (will be in same directory)
CERT_PATH = "www.fxcloudv2.co.za.pem"
KEY_PATH = "fxcloud.key"

# API Key for security - CHANGE THIS!
API_KEY = os.environ.get('API_KEY', 'dreamteam91frag')

def verify_api_key():
    """Check if the API key is valid"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    
    # Support both "Bearer token" and just "token"
    token = auth_header.replace('Bearer ', '').strip()
    return token == API_KEY

def submit_id_verification(identity_number, reference=None):
    """Submit ID to ThisIsMe API"""
    url = "https://uat-api.thisisme.com/dhadatapro"
    headers = {'content-type': 'application/json'}
    
    payload = {
        "identity_number": identity_number,
        "disable_report": "true"
    }
    
    if reference:
        payload["reference"] = reference
    
    try:
        response = requests.post(
            url,
            json=payload,
            verify=False,
            headers=headers,
            cert=(CERT_PATH, KEY_PATH),
            timeout=30
        )
        return response.status_code, response.json()
    except Exception as e:
        return 500, {"error": str(e), "type": type(e).__name__}

def get_verification_results(request_id, max_attempts=10):
    """Retrieve verification results"""
    url = f"https://uat-api.thisisme.com/dhadatapro/{request_id}"
    headers = {'content-type': 'application/json'}
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(
                url,
                verify=False,
                headers=headers,
                cert=(CERT_PATH, KEY_PATH),
                timeout=30
            )
            
            result = response.json()
            status_code = response.status_code
            
            if status_code in [200, 227]:
                return status_code, result
            elif status_code == 303:
                if attempt < max_attempts - 1:
                    time.sleep(3)
                    continue
                else:
                    return status_code, result
            else:
                return status_code, result
                
        except Exception as e:
            if attempt < max_attempts - 1:
                time.sleep(3)
                continue
            else:
                return 500, {"error": str(e), "type": type(e).__name__}
    
    return 408, {"status": "TIMEOUT", "message": "Request timed out"}

@app.route('/')
def home():
    """Health check"""
    return jsonify({
        "status": "online",
        "service": "ThisIsMe API Middleware",
        "version": "1.0",
        "endpoints": {
            "verify": "POST /verify",
            "check": "GET /check/{request_id}"
        }
    })

@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({"status": "healthy"}), 200

@app.route('/verify', methods=['POST'])
def verify_id():
    """
    Verify an ID number
    
    Headers: 
        Authorization: Bearer your-api-key
    
    Body: {
        "identity_number": "9905285124088",
        "reference": "optional"
    }
    """
    
    # Check API key
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized - Invalid or missing API key"
        }), 401
    
    # Get request data
    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400
    
    if not data:
        return jsonify({
            "success": False,
            "error": "No data provided"
        }), 400
    
    identity_number = data.get('identity_number')
    reference = data.get('reference', '')
    
    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400
    
    # Submit ID verification
    submit_status, submit_response = submit_id_verification(identity_number, reference)
    
    if submit_status != 303 and submit_status != 200:
        return jsonify({
            "success": False,
            "error": "Failed to submit verification",
            "status_code": submit_status,
            "response": submit_response
        }), submit_status
    
    request_id = submit_response.get('request_id')
    
    if not request_id:
        return jsonify({
            "success": False,
            "error": "No request_id received",
            "response": submit_response
        }), 500
    
    # Wait before checking
    time.sleep(2)
    
    # Get results
    result_status, results = get_verification_results(request_id)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/check/<request_id>', methods=['GET'])
def check_request(request_id):
    """Check status of existing request"""
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    result_status, results = get_verification_results(request_id, max_attempts=1)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))

    app.run(host='0.0.0.0', port=port, debug=False)
