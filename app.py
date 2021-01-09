from adapter import *

from flask import Flask
from flask import json
from datetime import datetime
app = Flask(__name__)

@app.route("/")
def index():
    output = {
        "datetime": datetime.utcnow(),
        "methods": {
            "station_list": "/stations/",
            "station_details": "/stations/{station_id}/",
            "departures": "/stations/{station_id}/departures/",
            "line_details": "/stations/{station_id}/lines/{line_id}/"
        }
    }
    return json.dumps(output)


@app.route("/stations/")
@cached()
def stations_list():
    stations = json.dumps(get_stations())
    return stations


@app.route("/stations/<int:station_id>/")
@cached()
def station_details(station_id):
    details = get_station_details(station_id)
    return json.dumps(details)


@app.route("/stations/<int:station_id>/lines/<int:line_id>/")
@cached()
def line_stations(station_id, line_id):
    details = get_line_details(station_id, line_id)
    return json.dumps(details)


@app.route("/stations/<int:station_id>/departures/")
def station_departuress(station_id):
    details = get_departures(station_id)
    return json.dumps(details)

# Add CORS header to every request
@app.after_request
def add_cors(resp):
    resp.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin','*')
    resp.headers['Access-Control-Allow-Credentials'] = 'true'
    resp.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS, GET'
    resp.headers['Access-Control-Allow-Headers'] = request.headers.get('Access-Control-Request-Headers', 'Authorization' )
    if app.debug:
        resp.headers['Access-Control-Max-Age'] = '1'
    return resp


if __name__ == "__main__":
    app.config["DEBUG"] = True
    app.run()
