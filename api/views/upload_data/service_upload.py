from rest_framework.response import Response
from backend.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
import random
from django.http import HttpResponse,JsonResponse
import csv
from app.settings.base import BASE_DIR
import string



def insert_service(request,df,sync_data,branch_id,length,user_id):
    try:
        user = User.objects.get(id=user_id)
        try:
            salon = SalonDetails.objects.get(user=user)
            branch_detail = Branch.objects.get(id=branch_id,salon=salon)
        except:
            salon = None
            branch_detail = Branch.objects.get(id=branch_id,manager=user)

        try:
            salon = SalonDetails.objects.get(user=user)
        except Exception:
            salon = None
    except:
        return Response({
            'message':"ERROR",
            'status':400
        })


    try:
        service_name = df["Service Name"]
        service_price = df['Service Price']
        service_discount = df['Discount']
        service_time_taken = df['Service Time']
        service_description = df['Short Description']
        service_category = df['Category Name']
    except Exception:
        response = {
                    "message": "Upload Correct CSV file",
                    'status':402
                    }
        return response

    for i in range(0, length):
        try:
            service_name = df["Service Name"][i]
            service_price = df['Service Price'][i]
            service_discount = df['Discount'][i]
            service_time_taken = df['Service Time'][i]
            service_description = df['Short Description'][i]
            service_category = df['Category Name'][i]
            if str(service_discount) == "nan" or str(service_discount) == "":
                service_discount = 0
            if str(service_time_taken) == "nan" or str(service_time_taken) == "":
                service_time_taken = 0
            if str(service_description) == 'nan' or str(service_description) == "":
                service_description = ''
            if str(service_category) == 'nan' or str(service_category) == "":
                service_category = ''

            if Service.objects.filter(branch=branch_detail,name=service_name):
                pass
            else:
                add_service = Service(
                                    user=salon,
                                    branch=branch_detail,
                                    name=service_name,
                                    description=service_description,
                                    price= int(service_price),
                                    category = service_category,
                                    time_for_each_service=service_time_taken)
                add_service.save()

                if str(service_discount) == 'nan' or service_discount == None or not service_discount or service_discount == 0.0 or service_discount == 0:
                    pass
                else:
                    add_discount = DiscountDetails(
                                                    salon=salon,
                                                    branch=branch_detail,
                                                    service=add_service,
                                                    offer_percent= float(service_discount)
                                                )
                    add_discount.save()
        except Exception as e:
            pass

    response = {
                "message": "Service Uploaded Successfully",
                'status':200
                }
    return response