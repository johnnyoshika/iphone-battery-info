import os
from flask import Flask, request, jsonify
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


@app.route('/battery_info', methods=['PUT'])
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
        # Battery rated capacity in mAh (according to ChatGPT)
        battery_rated_capacity = 3349
        battery_maximum_capacity = float(data.get("battery_maximum_capacity"))
        battery_nominal_capacity = float(data.get("battery_nominal_capacity"))
        battery_health = float(data.get("battery_health"))
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
            precise_battery_health
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
                range_name = f"A{index+1}:I{index+1}"
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

        return jsonify({"message": "Battery info updated successfully"})
    except (ValueError, TypeError, Exception) as e:
        return jsonify({"error": str(e)}), 400


def _parse_date_from_filename(filename):
    parts = filename.split('-')
    # Assuming the format is always like "Analytics-YYYY-MM-DD-..."
    date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"  # Extracts YYYY-MM-DD
    return date_str


if __name__ == '__main__':
    app.run(debug=True)
