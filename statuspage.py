#!/usr/bin/env python3

import sys, time, os, stat
import requests, json
from datetime import datetime, timezone
import unicornhathd

# Accept one argument from the command line
if len(sys.argv) != 2:
    print('Usage: sudo ./statuspage.py "<domain 1> <domain 2>"')
    print('  Example: sudo ./statuspage.py "www.githubstatus.com www.37status.com"')
    sys.exit(1)
else:
    URL_LIST = sys.argv[1].split()

# VARIABLES
SLEEP_TIMEOUT = 60 # seconds (1 minute)
FILE_PREFIX = '/tmp/hat-status-'

# CONSTANTS
MAX_COMPONENTS = 13
MAX_DAYS = 14
MAX_AGE_SUMMARY = 24 * 60 * 60  # seconds (24 hours)
MAX_AGE_STATUS = 5 * 60         # seconds (5 minutes)

def get_status(file, api_endpoint):
    print("Fetching blended status")
    res = requests.get(api_endpoint + file)
    data = json.loads(res.text)

    return data['status']['indicator']

def get_data(file, api_endpoint, domain):
    res = requests.get(api_endpoint + file)
    data = json.loads(res.text)

    # write the data to output file
    with open(FILE_PREFIX + domain + '-' + file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    return data

def fetch_data(file, api_endpoint, domain):
    temp_file = FILE_PREFIX + domain + '-' + file

    # check if the data file exists and if it's expired
    if os.path.isfile(temp_file):
        age = time.time() - os.stat(temp_file)[stat.ST_MTIME]

        if age > MAX_AGE_SUMMARY:
            data = get_data(file, api_endpoint, domain)
        else:
            with open(temp_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
    else:
        age = 0
        data = get_data(file, api_endpoint, domain)

    return {'data': data, 'age': round(age)}

def set_status(r, g, b):
    for x in range(16):
        unicornhathd.set_pixel(x, 15, r, g, b)
        unicornhathd.set_pixel(x, 14, r, g, b)
        unicornhathd.set_pixel(x, 13, 51, 153, 255) # blue divider line

# set the blended status LEDs (top 3 rows)
def set_blended_status(summary, api_endpoint):
    print(f"Blended status age: {summary['age']} seconds")
    if summary['age'] > MAX_AGE_STATUS:
        status = get_status('status.json', api_endpoint)
    else:
        status = summary['data']['status']['indicator']

    if status == 'critical':
        set_status(255, 0, 0)   # red
    elif status == 'major':
        set_status(255, 79, 0)  # orange
    elif status == 'minor':
        set_status(255, 255, 0) # yellow
    elif status == 'none':
        set_status(0, 255, 0)   # green
    else:
        set_status(0, 0, 255)   # blue

# set the current (daily) status LEDs (right 2 columns)
def set_current_status(summary):
    i = 0

    for y in summary['data']['components']:
        if i < MAX_COMPONENTS:
            unicornhathd.set_pixel(14, i, 51, 153, 255)     # blue divider line

            if y['status'] == 'major_outage':
                unicornhathd.set_pixel(15, i, 255, 0, 0)    # red
            elif y['status'] == 'partial_outage':
                unicornhathd.set_pixel(15, i, 255, 79, 0)   # orange
            elif y['status'] == 'degraded_performance':
                unicornhathd.set_pixel(15, i, 255, 255, 0)  # yellow
            elif y['status'] == 'operational':
                unicornhathd.set_pixel(15, i, 0, 255, 0)    # green
            else:
                unicornhathd.set_pixel(15, i, 0, 0, 255)    # blue

            for x in range(MAX_DAYS):
                unicornhathd.set_pixel(x, i, 0, 255, 0)     # set the daily status LED

        i += 1

# set the historical (daily) status LEDs (left 14 columns)
def set_historical_status(incidents):
    sorted_incidents = sorted(incidents['data']['incidents'], key=lambda d: d['updated_at'], reverse=True)
    current_date = datetime.now(timezone.utc)

    for x in sorted_incidents:
        incident_date = x['updated_at']
        if incident_date.endswith('Z'):
            incident_date = incident_date[:-1] + '+00:00'

        new_date = datetime.fromisoformat(incident_date)
        delta = (current_date - new_date).days + 1 # index should start at 1
        if delta < 14 and len(x['components']) > 0:
            status = x['impact']
            for y in x['components']:
                if y['position'] < 14:
                    x_position = y['position'] - 1 # index should start at 0
                    y_position = 14 - delta
                    unicornhathd.set_pixel(y_position, x_position, 255, 0, 0) # set the impacted status LED
                    print(f"Incident on {new_date} : {delta} days have passed since {current_date}")


def display(domain):
    print("StatusPage: " + domain)

    api_endpoint = 'https://' + domain + '/api/v2/'

    unicornhathd.brightness(0.2)
    unicornhathd.clear()
    unicornhathd.rotation(180)

    summary = fetch_data('summary.json', api_endpoint, domain)
    set_blended_status(summary, api_endpoint)
    set_current_status(summary)

    incidents = fetch_data('incidents.json', api_endpoint, domain)
    set_historical_status(incidents)

    unicornhathd.show()
    print("")

while True:
    for domain in URL_LIST:
        display(domain)
        time.sleep(SLEEP_TIMEOUT) # sleep for N seconds
