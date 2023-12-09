import requests


def fetch_data(data):
    url = 'http://localhost:8008/myip/'
    res = requests.post(url, json=data).json()
    return res
