#!/usr/bin/env python3
#
# statuspage.py - Display Statuspage data on the Unicorn HAT HD
#
# This script assumes the LED matrix is 16x16
#
# MIT License
# Copyright (c) 2024 Alexander Williams, https://a1w.ca

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
HAT_ROTATION = 180
HAT_BRIGHTNESS = 0.2

# CONSTANTS
MAX_COMPONENTS = 13
MAX_DAYS = 14
MAX_AGE_SUMMARY = 24 * 60 * 60  # seconds (24 hours)
MAX_AGE_STATUS = 5 * 60         # seconds (5 minutes)

# STATUS LED COLOURS (RGB)
COLOUR_RED      = [255, 0, 0]
COLOUR_ORANGE   = [255, 79, 0]
COLOUR_YELLOW   = [255, 255, 0]
COLOUR_GREEN    = [0, 255, 0]
COLOUR_BLUE     = [0, 0, 255]

def api_request(url):
    res = requests.get(url)

    return json.loads(res.text)

def cache_data(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_and_cache_data(file, api_endpoint, domain):
    temp_file = FILE_PREFIX + domain + '-' + file

    data = api_request(api_endpoint + file)

    cache_data(temp_file, data)

    return data

def load_cached_data(file):
    with open(file, 'r', encoding='utf-8') as f:
        return json.load(f)

def fetch_summary_incidents(file, api_endpoint, domain):
    temp_file = FILE_PREFIX + domain + '-' + file

    # check if the temporary file exists, and if it's expired
    if os.path.isfile(temp_file):
        age = time.time() - os.stat(temp_file)[stat.ST_MTIME]

        if age > MAX_AGE_SUMMARY:
            data = get_and_cache_data(file, api_endpoint, domain)
        else:
            data = load_cached_data(temp_file)

    else:
        age = 0
        data = get_and_cache_data(file, api_endpoint, domain)

    return {'data': data, 'age': round(age)}

def set_status(r, g, b):
    for x in range(16):
        unicornhathd.set_pixel(x, 15, r, g, b)
        unicornhathd.set_pixel(x, 14, r, g, b)
        unicornhathd.set_pixel(x, 13, 51, 153, 255) # blue divider line

def get_status_colour(status):
    if status == 'critical':
        return COLOUR_RED
    elif status == 'major':
        return COLOUR_ORANGE
    elif status == 'minor':
        return COLOUR_YELLOW
    elif status == 'none':
        return COLOUR_GREEN
    else:
        return COLOUR_BLUE

# set the blended status LEDs (top 3 rows)
def set_blended_status(summary, api_endpoint, domain):
    print(f"Blended status age: {summary['age']} seconds")

    if summary['age'] > MAX_AGE_STATUS:
        data = get_and_cache_data('status.json', api_endpoint, domain)
        status = data['status']['indicator']
    else:
        status = summary['data']['status']['indicator']

    r, g, b = get_status_colour(status)
    set_status(r, g, b)

def get_today_colour(status):
    if status == 'major_outage':
        return COLOUR_RED
    elif status == 'partial_outage':
        return COLOUR_ORANGE
    elif status == 'degraded_performance':
        return COLOUR_YELLOW
    elif status == 'operational':
        return COLOUR_GREEN
    else:
        return COLOUR_BLUE

# set today's (daily) status LEDs (right 2 columns)
def set_today_status(summary):
    for i, y in zip(range(MAX_COMPONENTS), summary['data']['components']):
        unicornhathd.set_pixel(14, i, 51, 153, 255)     # blue divider line

        r, g, b = get_today_colour(y['status'])
        unicornhathd.set_pixel(15, i, r, g, b)

        for x in range(MAX_DAYS):
            unicornhathd.set_pixel(x, i, 0, 255, 0)     # set the historical status LEDs to green

def format_incident_date(incident_date):
    if incident_date.endswith('Z'):
        return datetime.fromisoformat(incident_date[:-1] + '+00:00')
    else:
        return datetime.fromisoformat(incident_date)

# set the historical (daily) status LEDs (left 14 columns)
def set_historical_status(incidents):
    sorted_incidents = sorted(incidents['data']['incidents'], key=lambda d: d['updated_at'], reverse=True)
    current_date = datetime.now(timezone.utc)

    # TODO: cleanup
    for x in sorted_incidents:
        incident_date = format_incident_date(x['updated_at'])
        delta = (current_date - incident_date).days + 1 # index should start at 1

        if delta < MAX_DAYS and len(x['components']) > 0:
            for y in x['components']:
                if y['position'] < MAX_DAYS:
                    x_position = y['position'] - 1 # index should start at 0
                    y_position = MAX_DAYS - delta
                    r, g, b = get_status_colour(x['impact'])
                    unicornhathd.set_pixel(y_position, x_position, r, g, b) # set the impacted status LED
                    print(f"Incident ({x['impact']}) on {incident_date} : {delta} days have passed since {current_date}")


def display(domain):
    print("StatusPage: " + domain)

    api_endpoint = 'https://' + domain + '/api/v2/'

    unicornhathd.brightness(HAT_BRIGHTNESS)
    unicornhathd.clear()
    unicornhathd.rotation(HAT_ROTATION)

    summary = fetch_summary_incidents('summary.json', api_endpoint, domain)
    set_blended_status(summary, api_endpoint, domain)
    set_today_status(summary)

    incidents = fetch_summary_incidents('incidents.json', api_endpoint, domain)
    set_historical_status(incidents)

    unicornhathd.show()
    print("")

while True:
    for domain in URL_LIST:
        display(domain)
        time.sleep(SLEEP_TIMEOUT) # sleep for N seconds
