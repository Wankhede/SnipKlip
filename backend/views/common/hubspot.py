import hubspot
from hubspot.crm.deals import SimplePublicObjectInput, ApiException
from django.conf import settings
'''
https://developers.hubspot.com/docs/api/crm/deals
>>> from website.hubspot import createDeal
>>> createDeal()
'''
def createDeal(amount, closedate, dealname):
    client = hubspot.Client.create(access_token=settings.HUBSPOT_KEY)

    properties = {
        "amount": amount,
        "closedate": closedate,
        "dealname": dealname,
        "dealstage": "29041837",
        "hubspot_owner_id": "193567884",
        "pipeline": "default"
    }
    simple_public_object_input = SimplePublicObjectInput(properties=properties)
    try:
        api_response = client.crm.deals.basic_api.create(simple_public_object_input=simple_public_object_input)
        # print(api_response)
    except ApiException as e:
        print("Exception when calling basic_api->create: %s\n" % e)
    return

'''
HTTP 200
{
  "results": [
    {
      "id": "193567884",
      "email": settings.DEFAULT_FROM_EMAIL,
      "firstName": "Swapnil",
      "lastName": "Wankhede",
      "userId": 45548241,
      "createdAt": "2022-06-16T16:57:53.154Z",
      "updatedAt": "2022-07-23T10:42:00.760Z",
      "archived": false
    }
  ]
}
HTTP 201
{
  "id": "9575524881",
  "properties": {
    "amount": "1500.00",
    "amount_in_home_currency": "1500.00",
    "closedate": "2019-12-07T16:50:06.678Z",
    "createdate": "2022-07-23T14:18:09.069Z",
    "days_to_close": "0",
    "dealname": "Custom data integrations",
    "dealstage": "presentationscheduled",
    "hs_all_owner_ids": "193567884",
    "hs_closed_amount": "0",
    "hs_closed_amount_in_home_currency": "0",
    "hs_createdate": "2022-07-23T14:18:09.069Z",
    "hs_deal_stage_probability_shadow": "0.100000",
    "hs_forecast_amount": "1500.00",
    "hs_is_closed": "false",
    "hs_is_closed_won": "false",
    "hs_is_deal_split": "false",
    "hs_lastmodifieddate": "2022-07-23T14:18:09.069Z",
    "hs_object_id": "9575524881",
    "hs_projected_amount": "0",
    "hs_projected_amount_in_home_currency": "0",
    "hs_user_ids_of_all_owners": "45548241",
    "hubspot_owner_assigneddate": "2022-07-23T14:18:09.069Z",
    "hubspot_owner_id": "193567884",
    "pipeline": "default"
  },
  "createdAt": "2022-07-23T14:18:09.069Z",
  "updatedAt": "2022-07-23T14:18:09.069Z",
  "archived": false
}
'''