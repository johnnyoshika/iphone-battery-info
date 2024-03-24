import os
from flask import Flask, request, jsonify
from functools import wraps
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import json

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
        battery_cycles = int(data.get("battery_cycles"))
        battery_maximum_capacity = float(data.get("battery_maximum_capacity"))
        battery_nominal_capacity = float(data.get("battery_nominal_capacity"))
        battery_health = float(data.get("battery_health"))
        battery_health_metric = float(data.get("battery_health_metric"))
        daily_min_soc = float(data.get("daily_min_soc"))
        daily_max_soc = float(data.get("daily_max_soc"))
        min_temperature = float(data.get("min_temperature"))
        max_temperature = float(data.get("max_temperature"))
        ave_temperature = float(data.get("ave_temperature"))
        max_charge_current = float(data.get("max_charge_current"))
        max_discharge_current = float(data.get("max_discharge_current"))
        max_over_charge_current = data.get("max_over_charge_current")
        max_over_discharge_current = data.get("max_over_discharge_current")

        _insert_row(
            date_string,
            device_model,
            os_version,
            battery_cycles,
            battery_maximum_capacity,
            battery_nominal_capacity,
            battery_health,
            battery_health_metric,
            daily_min_soc,
            daily_max_soc,
            min_temperature,
            max_temperature,
            ave_temperature,
            max_charge_current,
            max_discharge_current,
            max_over_charge_current,
            max_over_discharge_current,
        )

        return jsonify({"message": "Battery info updated successfully"})
    except (ValueError, TypeError, Exception) as e:
        return jsonify({"error": str(e)}), 400


# Currently not using this. What we thought would be a more reliable way to extract min and max battery level and temperature values,
# it's proving to be inconsistent.
@app.route('/battery_jsonl', methods=['PUT'])
@require_api_key
def battery_jsonl():
    data = request.get_json()

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    try:
        # Parse analytics_filename to get the date part
        analytics_filename = data.get("analytics_filename")
        device_model = data.get("device_model")
        jsonl = data.get("jsonl")

        date_string = _parse_date_from_filename(analytics_filename)

        # The technique we'll use here is to check min max values by looking at different lines in jsonl.
        daily_min_soc, daily_max_soc = _find_min_max_values(
            jsonl, 'BatteryLevel')
        min_temperature, max_temperature = _find_min_max_values(
            jsonl, 'last_value_BatteryTemperature')

        os_version = _find_value(jsonl, "os_version")
        battery_cycles = int(_find_value(jsonl, "last_value_CycleCount"))
        battery_maximum_capacity = float(
            _find_value(jsonl, "last_value_MaximumFCC"))
        battery_nominal_capacity = float(
            _find_value(jsonl, "last_value_NominalChargeCapacity"))
        battery_health = float(_find_value(
            jsonl, "last_value_MaximumCapacityPercent"))
        battery_health_metric = float(
            _find_value(jsonl, "last_value_BatteryHealthMetric"))
        ave_temperature = float(_find_value(
            jsonl, "last_value_AverageTemperature"))
        max_charge_current = float(_find_value(
            jsonl, "last_value_MaximumChargeCurrent"))
        max_discharge_current = float(
            _find_value(jsonl, "last_value_MaximumDischargeCurrent"))
        max_over_charge_current = _find_value(jsonl,
                                              "last_value_MaximumOverChargedCapacity")
        max_over_discharge_current = _find_value(jsonl,
                                                 "last_value_MaximumOverDischargedCapacity")

        _insert_row(
            date_string,
            device_model,
            os_version,
            battery_cycles,
            battery_maximum_capacity,
            battery_nominal_capacity,
            battery_health,
            battery_health_metric,
            daily_min_soc,
            daily_max_soc,
            min_temperature,
            max_temperature,
            ave_temperature,
            max_charge_current,
            max_discharge_current,
            max_over_charge_current,
            max_over_discharge_current,
        )

        return jsonify({"message": "Battery info updated successfully"})
    except (ValueError, TypeError, Exception) as e:
        return jsonify({"error": str(e)}), 400


def _parse_date_from_filename(filename):
    parts = filename.split('-')
    # Assuming the format is always like "Analytics-YYYY-MM-DD-..."
    date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"  # Extracts YYYY-MM-DD
    return date_str


def _find_min_max_values(jsonl, property):
    values = []

    # Split the content by lines and parse each line as JSON
    for line in jsonl.strip().split('\n'):
        # Try to convert string to a dictionary
        try:
            json_content = json.loads(line)
            message = json_content.get('message', None)
            if (not message):
                continue

            value = message.get(property, None)
            if (not value):
                continue

            values.append(value)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing JSON: {e}")

    # Find the min and max values
    min_value = min(values) if values else None
    max_value = max(values) if values else None

    return min_value, max_value


def _find_value(jsonl, property):
    values = []

    # Split the content by lines and parse each line as JSON
    for line in jsonl.strip().split('\n'):
        # Try to convert string to a dictionary
        try:
            json_content = json.loads(line)

            value = json_content.get(property, None)
            if (value):
                values.append(value)
                continue

            message = json_content.get('message', None)
            if (not message):
                continue

            value = message.get(property, None)
            if (value):
                values.append(value)
        except (SyntaxError, ValueError) as e:
            print(f"Error parsing JSON: {e}")

    # Throw exception if all values aren't the same
    if len(set(values)) > 1:
        raise ValueError(f"Multiple values found for {property}")

    return values[0] if values else None


def _insert_row(
        date_string,
        device_model,
        os_version,
        battery_cycles,
        battery_maximum_capacity,
        battery_nominal_capacity,
        battery_health,
        battery_health_metric,
        daily_min_soc,
        daily_max_soc,
        min_temperature,
        max_temperature,
        ave_temperature,
        max_charge_current,
        max_discharge_current,
        max_over_charge_current,
        max_over_discharge_current):

    # Battery rated capacity in mAh (according to ChatGPT)
    battery_rated_capacity = 3349
    precise_battery_health = round(
        (battery_nominal_capacity / battery_rated_capacity) * 100, 2)

    row_data = [
        date_string,
        device_model,
        os_version,
        battery_cycles,
        battery_rated_capacity,
        battery_maximum_capacity,
        battery_nominal_capacity,
        battery_health,
        precise_battery_health,
        battery_health_metric,
        daily_min_soc,
        daily_max_soc,
        min_temperature,
        max_temperature,
        ave_temperature,
        max_charge_current,
        max_discharge_current,
        max_over_charge_current,
        max_over_discharge_current
    ]

    # Check if the date exists in the first column
    range_name = "A:A"
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=range_name).execute()

    values = result.get('values', [])

    found = False
    for index, row in enumerate(values):
        if row and row[0] == date_string:

            # Update existing row
            range_name = f"A{index+1}:T{index+1}"
            body = {
                'values': [row_data]
            }
            service.spreadsheets().values().update(spreadsheetId=spreadsheet_id, range=range_name,
                                                   body=body, valueInputOption="RAW").execute()
            found = True
            break

    if not found:
        range_name = "Sheet1"
        body = {
            'values': [row_data]
        }
        service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_name,
                                               body=body, valueInputOption="RAW").execute()


if __name__ == '__main__':
    app.run(
        port=8000,  # macOS blocks default port 5000 when proxying through ngrok
        debug=True
    )
