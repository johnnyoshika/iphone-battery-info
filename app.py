import os
from flask import Flask, request, jsonify
from functools import wraps
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()


# Define the path to your service account JSON file
service_account_file = "service-account.json"
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
creds = None
if os.path.exists(service_account_file):
    creds = service_account.Credentials.from_service_account_file(
        service_account_file, scopes=scopes
    )

service = build("sheets", "v4", credentials=creds)
spreadsheet_id = os.getenv("SPREADSHEET_ID")

app = Flask(__name__)


api_key = os.getenv('API_KEY')


def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Authorization header is missing.'}), 401

        parts = auth_header.split()

        if len(parts) == 2 and parts[0] == 'Bearer' and parts[1] == api_key:
            return f(*args, **kwargs)
        else:
            return jsonify({'error': 'Invalid API key.'}), 401

    return decorated_function


@app.route('/battery_info', methods=['PUT'])
@require_api_key
def battery_info():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    try:
        # Parse analytics_filename to get the date part
        analytics_filename = data.get("analytics_filename")
        date_string = _parse_date_from_filename(analytics_filename)

        device_model = data.get("device_model")
        os_version = data.get("os_version")
        cycle_count = int(data.get("cycle_count"))
        maximum_capacity_percent = float(data.get("maximum_capacity_percent"))
        maximum_fcc = float(data.get("maximum_fcc"))
        apple_raw_max_capacity = float(data.get("apple_raw_max_capacity"))
        nominal_charge_capacity = float(data.get("nominal_charge_capacity"))

        capacity = _get_capacity(os_version, apple_raw_max_capacity, nominal_charge_capacity)

        _insert_row(
            _get_sheet(os_version),
            [
                date_string,
                _get_device_model(os_version, device_model),
                os_version,
                cycle_count,
                capacity["rated_capacity"],
                maximum_fcc,
                apple_raw_max_capacity,
                nominal_charge_capacity,
                maximum_capacity_percent,
                capacity["precise_battery_health"]
            ]
        )

        return jsonify({"message": "Battery info updated successfully"})
    except (ValueError, TypeError, Exception) as e:
        return jsonify({"error": str(e)}), 400

@app.route('/mac_battery_info', methods=['PUT'])
@require_api_key
def mac_battery_info():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    try:
        date_string = data.get("date")
        cycle_count = int(data.get("cycle_count"))
        design_capacity = float(data.get("design_capacity"))
        apple_raw_max_capacity = float(data.get("apple_raw_max_capacity"))
        nominal_charge_capacity = float(data.get("nominal_charge_capacity"))
        max_capacity = float(data.get("max_capacity"))

        precise_battery_health = round(
            (apple_raw_max_capacity / design_capacity) * 100, 2)

        _insert_row(
            "MacBook Pro",
            [
                date_string,
                cycle_count,
                design_capacity,
                apple_raw_max_capacity,
                nominal_charge_capacity,
                max_capacity,
                precise_battery_health
            ]
        )

        return jsonify({"message": "Mac battery info updated successfully"})

    except (ValueError, TypeError, Exception) as e:
        return jsonify({"error": str(e)}), 400


def _parse_date_from_filename(filename):
    parts = filename.split('-')
    # Assuming the format is always like "Analytics-YYYY-MM-DD-..."
    date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"  # Extracts YYYY-MM-DD
    return date_str

def _is_watch(os_version):
    if "Watch OS" in os_version:
        return True
    elif "iPhone OS" in os_version:
        return False
    else:
        raise ValueError(f"Unsupported OS version: {os_version}")

def _get_sheet(os_version):
    return "Watch" if _is_watch(os_version) else "Phone"

def _get_device_model(os_version, device_model):
    # device_model passed to API will be the device used to send api request, which will always be iPhone,
    # so fix it for watch here
    return "Apple Watch 7" if _is_watch(os_version) else device_model

def _get_capacity(os_version, apple_raw_max_capacity, nominal_charge_capacity):
    if _is_watch(os_version):
        rated_capacity = 284

    else:
        rated_capacity = 3349

    # We'll use nominal_charge_capacity b/c it's more stable and matches the value reported in max_capacity,
    # whereas apple_raw_max_capacity is all over the place
    precise_battery_health = round(
        (nominal_charge_capacity / rated_capacity) * 100, 2)

    return {
        "rated_capacity": rated_capacity,
        "precise_battery_health": precise_battery_health
    }

def _insert_row(sheet, values):
    # Check if the date exists in the first column
    range_name = f"{sheet}!A:A"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()

    result_values = result.get('values', [])

    found = False
    for index, row in enumerate(result_values):
        date_string = values[0]
        if row and row[0] == date_string:

            # Update existing row
            range_name = f"{sheet}!A{index+1}:J{index+1}"
            body = {
                'values': [values]
            }
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name,
                                                   body=body, valueInputOption="RAW").execute()
            found = True
            break

    if not found:
        range_name = sheet
        body = {
            'values': [values]
        }
        service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_name,
                                               body=body, valueInputOption="RAW").execute()


if __name__ == '__main__':
    app.run(
        port=8000,  # macOS blocks default port 5000 when proxying through ngrok
        debug=True
    )
