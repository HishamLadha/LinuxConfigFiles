#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script is a simple wrapper which prefixes each i3status line with custom
# information. It is based on a Perl script to show the Bitcoin price and the next prayer time.
#
# To use it, ensure your ~/.i3status.conf contains this line:
#     output_format = "i3bar"
# in the 'general' section.
# Then, in your ~/.i3/config, use:
#     status_command i3status | ~/i3status/contrib/wrapper.py
# In the 'bar' section.
#

import sys
import json
import subprocess
from datetime import datetime
import re

def get_btc_price():
    """ Fetch Bitcoin price using curl """
    try:
        # Run curl and capture the output
        btc_price = subprocess.check_output(['curl', '-s', 'https://cryptoprices.cc/BTC']).decode('utf-8').strip()
        return btc_price if btc_price else 'N/A'
    except subprocess.CalledProcessError:
        return 'N/A'

def get_prayer_times():
    """ Fetch and parse prayer times from mosqueprayertimes.com """
    try:
        # Fetch the page HTML
        response = subprocess.check_output(['curl', '-s', 'https://mosqueprayertimes.com/micm']).decode('utf-8')
        
        # Extract the MPT JavaScript variable using regex
        mpt_match = re.search(r'MPT=\{([^}]+)\};', response)
        if not mpt_match:
            return None
        
        mpt_data = mpt_match.group(1)
        mpt_dict = {}

        # Convert the extracted data into a dictionary
        for item in mpt_data.split(','):
            if ':' in item:
                date, times = item.split(':')
                date = date.strip()
                times = times.strip().strip('"')
                mpt_dict[date] = times

        # Get today's date in the required format (YYYYMMDD)
        today = datetime.now().strftime("%Y%m%d")

        # Return today's prayer times if available
        return mpt_dict.get(today, None)
    except subprocess.CalledProcessError:
        return None

def get_next_prayer(prayer_times):
    """ Calculate the next prayer based on current time """
    if not prayer_times:
        return "No prayer times available"

    # Correct the indexing, starting at the 9th character (prayer times start here)
    timings = {
        'Fajr Adhan': prayer_times[8:12],
        'Fajr Iqama': prayer_times[12:16],
        'Shurooq': prayer_times[16:20],  # Shurooq time falls between Fajr Iqama and Dhuhr Adhan
        'Dhuhr Adhan': prayer_times[20:24],
        'Dhuhr Iqama': prayer_times[24:28],
        'Asr Adhan': prayer_times[28:32],
        'Asr Iqama': prayer_times[32:36],
        'Maghrib Adhan': prayer_times[36:40],
        'Maghrib Iqama': prayer_times[40:44],
        'Isha Adhan': prayer_times[44:48],
        'Isha Iqama': prayer_times[48:52],
    }
    

    # Convert current time to HHMM format as an integer (removing leading zeros)
    current_time = int(datetime.now().strftime("%H%M"))

    # Find the next prayer based on the current time
    for prayer, time in timings.items():
        # Ensure prayer time is also an integer for comparison
        time_int = int(time.lstrip('0') or '0')  # Remove leading zeros for proper comparison
        if current_time < time_int:
            next_prayer = f"{prayer} at {time[:2]}:{time[2:]}"
            return next_prayer

    return "No more prayers today"

def print_line(message):
    """ Non-buffered printing to stdout. """
    sys.stdout.write(message + '\n')
    sys.stdout.flush()

def read_line():
    """ Interrupted respecting reader for stdin. """
    try:
        line = sys.stdin.readline().strip()
        if not line:
            sys.exit(3)
        return line
    except KeyboardInterrupt:
        sys.exit()

if __name__ == '__main__':
    # Skip the first line which contains the version header.
    print_line(read_line())

    # The second line contains the start of the infinite array.
    print_line(read_line())

    while True:
        line, prefix = read_line(), ''
        # ignore comma at start of lines
        if line.startswith(','):
            line, prefix = line[1:], ','

        j = json.loads(line)

        # Fetch the Bitcoin price
        btc_price = get_btc_price()

        # Fetch prayer times and calculate the next prayer
        prayer_times = get_prayer_times()
        next_prayer = get_next_prayer(prayer_times) if prayer_times else "No prayer times available"

        # Insert Bitcoin price into the start of the JSON
        j.insert(0, {'full_text': '<span background="#4c7a5d"> BTC: $%s </span>' % btc_price, 'name': 'btc', 'markup': 'pango'})

        # Insert next prayer time into the JSON
        j.insert(1, {'full_text': '<span background="#5e81ac"> %s </span>' % next_prayer, 'name': 'prayer', 'markup': 'pango'})

        # Output the updated line as JSON
        print_line(prefix + json.dumps(j))
