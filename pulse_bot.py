import requests
from datetime import datetime
import os

# --------------------------
# WEATHER
# --------------------------

def get_weather():
    try:
        url = "https://wttr.in/?format=j1"

        response = requests.get(url)
        response.raise_for_status()

        data = response.json()

        current = data["current_condition"][0]

        return {
            "temp": current["temp_C"],
            "humidity": current["humidity"],
            "condition": current["weatherDesc"][0]["value"]
        }

    except Exception as e:
        return {
            "error": str(e)
        }


# --------------------------
# QUOTE
# --------------------------

def get_quote():
    try:
        url = "https://zenquotes.io/api/random"

        response = requests.get(url)
        response.raise_for_status()

        data = response.json()[0]

        return f'{data["q"]} — {data["a"]}'

    except Exception:
        return "Stay focused and keep learning."


# --------------------------
# SUMMARY
# --------------------------

def build_summary(weather, quote):

    summary = f"""
=========================
 DAILY PULSE REPORT
=========================

Date: {datetime.now()}

WEATHER
--------

Temperature : {weather.get('temp', 'N/A')} °C
Humidity    : {weather.get('humidity', 'N/A')} %
Condition   : {weather.get('condition', 'N/A')}

QUOTE
-----

{quote}

=========================
"""

    return summary


# --------------------------
# SAVE
# --------------------------

def save_summary(summary):

    os.makedirs("summaries", exist_ok=True)

    filename = datetime.now().strftime(
        "summaries/report_%Y_%m_%d.txt"
    )

    with open(filename, "w", encoding="utf-8") as f:
        f.write(summary)

    return filename


# --------------------------
# RUN
# --------------------------

def run():

    weather = get_weather()

    quote = get_quote()

    summary = build_summary(weather, quote)

    file = save_summary(summary)

    print(summary)
    print("Saved:", file)


if __name__ == "__main__":
    run()