import requests
import json

def sms():
    # mention url
    url = "https://www.fast2sms.com/dev/bulk"
    
    # create a dictionary
    my_data = {
        # Your default Sender ID
        'sender_id': 'FSTSMS', 
        
        # Put your message here!
        'message': 'This is a test message', 
        
        'language': 'english',
        'route': 'p',
        
        # You can send sms to multiple numbers
        # separated by comma.
        'numbers': '9999999999, 7777777777, 6666666666'    
    }
    
    # create a dictionary
    headers = {
        'authorization': 'YOUR API KEY HERE',
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache"
    }
    # make a post request
    response = requests.request("POST",
                                url,
                                data = my_data,
                                headers = headers)
    # load json data from source
    returned_msg = json.loads(response.text)
    
    # print the send message
    return