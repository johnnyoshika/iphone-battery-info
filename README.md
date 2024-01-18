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
4. Copy `.env.example` to `.env` and populate `SPREADSHEET_ID` with the Google Sheet ID, which can be found in the sheet URL

### Google Sheets API

- Enable `Google Sheets API` in Google Cloud
- Create a new Service Account but don't add any permissions (they're not necessary)
- Give `Editor` access to Google Sheet by sharing it with the email address of the Service Account (e.g. `google-sheets@my-project-random.iam.gserviceaccount.com`)
- Download key for the new Service Account and save as `service-account.json` in the root of this project

## Usage

On iPhone, go to `Settings` -> `Privacy & Security` -> `Analytics & Improvements`.

From there, enable `Share iPhone Analytics`. By turning this on, the iPhone will create a `Analytics-YYYY-MM-DD-######.ips.ca.synced` file daily.

Go to `Analytics Data` and find the file that looks like `Analytics-YYYY-MM-DD-######.ips.ca.synced`. Open it, tap the share sheet, then select `Send Battery Info`. This shortcut is a modification of the one posted by @grapplerone here: https://www.reddit.com/r/ios/comments/yf6mu0/comment/iu1zvuw/

The shortcut sends an http put request to this API.

## Sniff HTTP Requests

### Windows

Use [2. Old Solution (Not recommended)](https://docs.proxyman.io/debug-devices/python#2.-old-solution-not-recommended).

1. Download cert from Proxyman: Certificate -> Export -> Root Certificate as PEM...
2. Save that file to certs folder
3. Inside venv: `python proxyman.py add`
4. Paste relative path to cert file

To disable proxyman proxy:

1. Inside venv: `python proxyman.py remove`

### Mac

Use [1. New Automatic Solution (v4.7.0 or later)](https://docs.proxyman.io/debug-devices/python#1.-new-automatic-solution-v4.7.0-or-later).

When new Terminal launches, open vscode from there:

```
cd projects/iphone-battery-info
code .
```
