"""
Railway Flask API for ThisIsMe Integration - Multiple APIs
Supports: DataPro and Trace APIs
Save this as: app.py
"""

from flask import Flask, request, jsonify
import requests
import urllib3
import time
import os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

# Certificate paths
CERT_PATH = "www.fxcloudv2.co.za.pem"
KEY_PATH = "fxcloud.key"

# API Key for security
API_KEY = os.environ.get('API_KEY', 'change-this-to-a-secure-password-123')

def verify_api_key():
    """Check if the API key is valid"""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return False
    token = auth_header.replace('Bearer ', '').strip()
    return token == API_KEY

# ============================================================================
# DATAPRO API FUNCTIONS
# ============================================================================

def submit_datapro_verification(identity_number, reference=None):
    """Submit ID to ThisIsMe DataPro API"""
    url = "https://uat-api.thisisme.com/v4/alwayson-datapro"
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

def get_datapro_results(request_id, max_attempts=10):
    """Retrieve DataPro verification results"""
    url = f"https://uat-api.thisisme.com/v4/alwayson-datapro/{request_id}"
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

# ============================================================================
# TRACE API FUNCTIONS
# ============================================================================

def submit_trace_request(identity_number, reference=None):
    """Submit ID to ThisIsMe Trace API"""
    url = "https://uat-api.thisisme.com/v4/trace"
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

def get_trace_results(request_id, max_attempts=10):
    """Retrieve Trace results"""
    url = f"https://uat-api.thisisme.com/v4/trace/{request_id}"
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

def extract_trace_data(trace_data):
    """Extract specific fields from Trace API response"""
    extracted = {
        "address": None,
        "employer": None,
        "cell_number": None
    }
    
    # Get response data
    response_list = trace_data.get("response", [])
    if not response_list or len(response_list) == 0:
        return extracted
    
    response_data = response_list[0]
    
    # Extract first address
    addresses = response_data.get("addresses", [])
    if addresses and len(addresses) > 0:
        first_address = addresses[0]
        extracted["address"] = {
            "line1": first_address.get("adrs_line1"),
            "line2": first_address.get("adrs_line2"),
            "line3": first_address.get("adrs_line3"),
            "line4": first_address.get("adrs_line4"),
            "type": first_address.get("adrs_type"),
            "postal_code": first_address.get("postal_code"),
            "created_date": first_address.get("created_date"),
            "last_updated": first_address.get("last_updated")
        }
    
    # Extract first employer
    employers = response_data.get("employers", [])
    if employers and len(employers) > 0:
        first_employer = employers[0]
        extracted["employer"] = {
            "name": first_employer.get("emp_name"),
            "occupation": first_employer.get("occupation"),
            "branch_code": first_employer.get("branch_code"),
            "created_date": first_employer.get("created_date"),
            "last_updated": first_employer.get("last_updated")
        }
    
    # Extract first CELL telephone
    telephones = response_data.get("telephones", [])
    for phone in telephones:
        if phone.get("telephone_type") == "CELL":
            extracted["cell_number"] = {
                "number": phone.get("telephone"),
                "created_date": phone.get("created_date"),
                "last_updated": phone.get("last_updated")
            }
            break  # Only get the first CELL number
    
    return extracted

# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.route('/')
def home():
    """Health check"""
    return jsonify({
        "status": "online",
        "service": "ThisIsMe API Middleware",
        "version": "2.0",
        "endpoints": {
            "verify": "POST /verify (DataPro only)",
            "trace": "POST /trace (Trace only)",
            "verify_all": "POST /verify-all (DataPro + Trace combined)",
            "check_datapro": "GET /check/datapro/{request_id}",
            "check_trace": "GET /check/trace/{request_id}"
        }
    })

@app.route('/health')
def health():
    """Health check for monitoring"""
    return jsonify({"status": "healthy"}), 200

@app.route('/verify', methods=['POST'])
def verify_id():
    """Verify ID - DataPro only (original endpoint)"""
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized - Invalid or missing API key"
        }), 401
    
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
    
    # Submit DataPro verification
    submit_status, submit_response = submit_datapro_verification(identity_number, reference)
    
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
    
    time.sleep(2)
    
    result_status, results = get_datapro_results(request_id)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/trace', methods=['POST'])
def trace_id():
    """Trace ID - Trace API only"""
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400
    
    identity_number = data.get('identity_number')
    reference = data.get('reference', '')
    
    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400
    
    # Submit Trace request
    submit_status, submit_response = submit_trace_request(identity_number, reference)
    
    if submit_status != 303 and submit_status != 200:
        return jsonify({
            "success": False,
            "error": "Failed to submit trace request",
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
    
    time.sleep(2)
    
    result_status, results = get_trace_results(request_id)
    
    # Extract specific data
    extracted = extract_trace_data(results)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results,
        "extracted": extracted
    })

@app.route('/verify-all', methods=['POST'])
def verify_all():
    """
    Comprehensive verification - Calls both DataPro and Trace APIs
    Returns combined data
    """
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    try:
        data = request.get_json()
    except:
        return jsonify({
            "success": False,
            "error": "Invalid JSON"
        }), 400
    
    identity_number = data.get('identity_number')
    reference = data.get('reference', '')
    
    if not identity_number:
        return jsonify({
            "success": False,
            "error": "identity_number is required"
        }), 400
    
    combined_results = {
        "identity_number": identity_number,
        "datapro": None,
        "trace": None
    }
    
    # 1. Call DataPro API
    submit_status, submit_response = submit_datapro_verification(identity_number, reference)
    
    if submit_status in [200, 303]:
        datapro_request_id = submit_response.get('request_id')
        if datapro_request_id:
            time.sleep(2)
            datapro_status, datapro_results = get_datapro_results(datapro_request_id)
            combined_results["datapro"] = {
                "success": datapro_status in [200, 227],
                "status_code": datapro_status,
                "request_id": datapro_request_id,
                "data": datapro_results
            }
    
    # 2. Call Trace API
    trace_submit_status, trace_submit_response = submit_trace_request(identity_number, reference)
    
    if trace_submit_status in [200, 303]:
        trace_request_id = trace_submit_response.get('request_id')
        if trace_request_id:
            time.sleep(2)
            trace_status, trace_results = get_trace_results(trace_request_id)
            extracted = extract_trace_data(trace_results)
            combined_results["trace"] = {
                "success": trace_status in [200, 227],
                "status_code": trace_status,
                "request_id": trace_request_id,
                "data": trace_results,
                "extracted": extracted
            }
    
    # Determine overall success
    overall_success = (
        combined_results.get("datapro", {}).get("success", False) or
        combined_results.get("trace", {}).get("success", False)
    )
    
    return jsonify({
        "success": overall_success,
        "results": combined_results
    })

@app.route('/check/datapro/<request_id>', methods=['GET'])
def check_datapro_request(request_id):
    """Check status of DataPro request"""
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    result_status, results = get_datapro_results(request_id, max_attempts=1)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results
    })

@app.route('/check/trace/<request_id>', methods=['GET'])
def check_trace_request(request_id):
    """Check status of Trace request"""
    
    if not verify_api_key():
        return jsonify({
            "success": False,
            "error": "Unauthorized"
        }), 401
    
    result_status, results = get_trace_results(request_id, max_attempts=1)
    extracted = extract_trace_data(results)
    
    return jsonify({
        "success": result_status in [200, 227],
        "status_code": result_status,
        "request_id": request_id,
        "data": results,
        "extracted": extracted
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

