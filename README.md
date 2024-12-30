# Statuspage Unicorn HAT HD

A small Python script for fetching _site_, _component_, and _incident_ status from the [Atlassian Statuspage v2 API](https://www.atlassian.com/software/statuspage), and displaying them on a [Unicorn HAT HD](https://github.com/pimoroni/unicorn-hat-hd), as shown below:

| Site | Status |
| ---- | ---- |
| **www.githubstatus.com** | ![hat-status-github2](https://github.com/user-attachments/assets/8fae211a-d8e2-4efa-b971-3de1e6053d47) |
| **37status.com** | ![hat-status-37signals2](https://github.com/user-attachments/assets/de048c57-a6eb-4366-ba3a-d92729072e7d) |
| **status.openai.com** | ![hat-status-openai2](https://github.com/user-attachments/assets/79ccf899-ba25-4e5d-b97d-9c9f4d98eaaf) |

  1. [How to read the matrix](#how-to-read-the-matrix)
  2. [Requirements](#requirements)
  3. [Getting started](#getting-started)
  4. [How it works](#how-it-works)
  5. [Contributing](#contributing)
  6. [License](#license)

## How to read the matrix

Here we'll use an example from [githubstatus.com](https://www.githubstatus.com):

![matrix dots](https://github.com/user-attachments/assets/2e87b9a8-4560-48be-8716-c4ecff5afe8c)

First, most importantly: **The blue lines are dividers**

### Above the blue line

The 2x16 dots (32 dots) above the _horizontal blue line_ represent the **blended status**, as [explained here](https://www.githubstatus.com/api#status). Those dots will always appear either red, orange, yellow, or green at the same time. This makes it very clear when a global outage or incident is currently in effect.

### Right of the blue line

Next, the 11 dots to the right of the _vertical blue line_ represent **today's status impact** of each individual component, as [explained here](https://www.githubstatus.com/api#incidents). Each component is given one row of dots starting from the bottom. Each dot can appear either red, orange, yellow, or green independently.

A maximum of 13 components can be displayed at once, so the program will only display the first 13 components returned by the _Statuspage_ v2 API.

### Left of the blue line

Finally, the dots to the left of the _vertical blue line_ represent the **historical status impact** of each individual component. The dot immediately to the left of the _vertical blue line_ is the status from 1 day ago. The second dot to the left of the _vertical blue line_ is the status from 2 days ago, etc.

A maximum of 14 days worth of historical status can be displayed at once.

### Below the blue line

The black dots/spaces below the _horizontal blue line_ represent _no component_ and therefore have no status dots and no dividing line (i.e: no blue dot).

### Interpreting githubstatus.com

From the example above, we can conclude the following:

- All systems are currently operational (blended status)
- All 11 components are operational today
- Components 2, 4, 5, 6 had a major outage 11 days ago
- Component 5 had a major outage 12 days ago

## Requirements

* A [Unicorn Hat HD](https://shop.pimoroni.com/products/unicorn-hat-hd)
* RPi with a network connection
* Raspios flashed and accessible
* Python 3.9+

This was tested and developed on an RPi 2 B+ and WiPi wireless network adapter.

> **Note:** The Unicorn HAT HD might be out of stock at Pimoroni, but it should available at Adafruit, Digi-Key, and others.

## Getting started

Once the hardware is set up, you'll need to install some software.

**DISCLAIMER: I can't be held responsible for your use or misuse of this software and documentation. I also can't support alternative uses, but I'm open to pull requests for improvements.**

### Install the unicornhathd and its dependencies

Follow [these instructions](https://github.com/pimoroni/unicorn-hat-hd), or do it manually:

```
sudo apt-get install python3-pip python3-dev python3-spidev
sudo pip3 install unicornhathd
```

### Enable SPI

```
sudo raspi-config nonint do_spi 0
sudo reboot
```

### Clone this git repo

```
git clone https://github.com/aw/hw-statuspage
cd hw-statuspage
```

### Run the script

```
sudo ./statuspage.py "www.githubstatus.com www.37status.com"
```

## How it works

**Personal note:** This is my first Python project, the code is far from optimal.

The script will run in an infinite loop, fetching status updates of one URL, then it will sleep for 60 seconds (`SLEEP_TIMEOUT` variable) before fetching the status updates of the next URL.

It will first fetch the summary from the `summary.json` URL to obtain the blended status of the site. It will cache the results in a temporary file in `/tmp` (`FILE_PREFIX` variable), and then update the current site status (above the _horizontal blue line_).

If the temporary file exists, it will check its age and use the existing file if it's less than 24 hours old (`MAX_AGE_SUMMARY` constant). This is to prevent constantly hitting the API to obtain historical data that technically shouldn't change (unless someone has a time machine...).

If the blended status is more than 5 minutes old (`MAX_AGE_STATUS` constant), it will fetch a new status from the `status.json` URL.

The summary data will then be used to update today's component status (right of the _vertical blue line_).

Next, the script will fetch the historical incident data from the `incidents.json` URL and update the historical component status (left of the _vertical blue line_). Similar to the `summary.json`, the file will be cached in a temporary location for up to 24 hours and re-used to avoid hitting the API too often.

## Contributing

  * For bugs, issues, or feature requests, please [create an issue](https://github.com/aw/hw-statuspage/issues/new).

## License

[MIT License](LICENSE)

Copyright (c) 2024 Alexander Williams, https://a1w.ca
