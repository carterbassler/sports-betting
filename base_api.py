import requests

def get_advantages(bet_type : str):
    url = "https://sportsbook-api2.p.rapidapi.com/v0/advantages/"
    querystring = {"type": bet_type}

    headers = {
        "x-rapidapi-key": "95df4a9406mshd45f4cfbf6a60f5p1f3a11jsnbbdd8a5b4c4d",
        "x-rapidapi-host": "sportsbook-api2.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    #Change Into Unified Structure
    print(response.text)

if __name__ == "__main__":
    get_advantages('PLUS_EV_AVERAGE')