import json
import os

import requests


def whatsApp(messageParams=None, phoneNo='+919999999999', templateId=1):
    if messageParams is None:
        messageParams = []

    allowed_phone_numbers = ['+919999999999']

    if phoneNo not in allowed_phone_numbers:
        return
    templateMapping = {
        1 : 'welcome_to_snipklip',
        2 : 'otp',
        3 : 'thank_you',
        4 : 'order_confirmation',
        5 : 'payment_confirmation',
        6 : 'sample_purchase_feedback'
    }
    url = "https://graph.facebook.com/v13.0/100715709627999/messages"

    payload = json.dumps({
    "messaging_product": "whatsapp",
    "recipient_type": "individual",
    "to": phoneNo,
    "type": "template",
    "template": {
        "name": templateMapping[templateId],
        "language": {
        "code": "en_US"
        },
        "components": [
        #       {
        # "type": "header",
        # "parameters": [
        #     {
        #         "type": "document",
        #         "document": {
        #         "link": "https://snipklip.in/SnipKlip-Brochure.pdf"
        #         }
        #     }
        #     ]
        # },
        {
            "type": "body",
            "parameters": messageParams
        }
        ]
    }
    })

    FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {FACEBOOK_ACCESS_TOKEN}'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return

'''
"parameters": [
    {
        "type": "text",
        "text": "text-string"
    },
    {
        "type": "currency",
        "currency": {
            "fallback_value": "$100.99",
            "code": "USD",
            "amount_1000": 100990
        }
    },
    {
        "type": "date_time",
        "date_time": {
            "fallback_value": "February 25, 1977",
            "day_of_week": 5,
            "year": 1977,
            "month": 2,
            "day_of_month": 25,
            "hour": 15,
            "minute": 33,
            "calendar": "GREGORIAN"
        }
    }
]
'''