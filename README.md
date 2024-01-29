# iPhone Battery Info

API where iPhone Shortcut sends battery info. This API then sends that data to Google Sheets.

## Setup

Install pyenv:

- Windows: [pyenv-win](https://github.com/pyenv-win/pyenv-win)
- WSL: https://gist.github.com/monkut/35c2ef098b871144b49f3f9979032cee

Environment:

1. Create a virtual environment: `python -m venv venv`
2. Activate virtualenv: `.\venv\Scripts\activate` (Windows), `source venv/bin/activate` (Linux)
3. Install packages from requirements.txt: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env` and:

- Set an arbitrary `API_KEY` (which will be used in the `Authorization` header of the http request)
- Populate `SPREADSHEET_ID` with the Google Sheet ID, which can be found in the sheet URL

### Google Sheets API

- Enable `Google Sheets API` in Google Cloud
- Create a new Service Account but don't add any permissions (they're not necessary)
- Give `Editor` access to Google Sheet by sharing it with the email address of the Service Account (e.g. `google-sheets@my-project-random.iam.gserviceaccount.com`)
- Download key for the new Service Account and save as `service-account.json` in the root of this project

## Usage

Start app: `python app.py`

On iPhone, go to `Settings` -> `Privacy & Security` -> `Analytics & Improvements`.

From there, enable `Share iPhone Analytics`. By turning this on, the iPhone will create a `Analytics-YYYY-MM-DD-######.ips.ca.synced` file daily.

Go to `Analytics Data` and find the file that looks like `Analytics-YYYY-MM-DD-######.ips.ca.synced`. Open it, tap the share sheet, then select `Send Battery Info`. This shortcut is a modification of the one posted by @grapplerone here: https://www.reddit.com/r/ios/comments/yf6mu0/comment/iu1zvuw/

The shortcut sends an http put request to this API.

## Run as a service on Raspberry Pi

On Raspberry Pi, create this file at `/etc/systemd/system/iphone-battery-info.service`

```
[Unit]
Description=iPhone Battery Info
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/projects/iphone-battery-info
Environment=FLASK_ENV=production
Environment=FLASK_PORT=8000
ExecStart=/home/pi/projects/iphone-battery-info/venv/bin/python /home/pi/projects/iphone-battery-info/app.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Reload systemd daemon: `sudo systemctl daemon-reload`
Enable our service for autostart: `sudo systemctl enable iphone-battery-info`
List enabled services: `systemctl list-unit-files | grep enabled`
Access logs: `journalctl -u iphone-battery-info`
Make sure to restart Pi after everything is set up
Helpfun commands:

- `systemctl status iphone-battery-info`
- `sudo systemctl stop iphone-battery-info`
- `sudo systemctl start iphone-battery-info`
