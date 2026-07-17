import json

import requests
from django.conf import settings


def sms():
    url = "https://www.fast2sms.com/dev/bulk"
    my_data = {
        "sender_id": "FSTSMS",
        "message": "This is a test message",
        "language": "english",
        "route": "p",
        "numbers": "9999999999",
    }
    headers = {
        "authorization": settings.FAST2SMS_API_KEY,
        "Content-Type": "application/x-www-form-urlencoded",
        "Cache-Control": "no-cache",
    }
    # make a post request
    response = requests.request("POST", url, data=my_data, headers=headers)
    # load json data from source
    returned_msg = json.loads(response.text)

    # print the send message
    return
