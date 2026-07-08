from api.common import log_error_with_api_endpoint
from rest_framework.decorators import api_view
from rest_framework.response import Response
from api.serializers import ReviewSerializer
from backend.models import *
from api.constants import *

@api_view(['GET',"POST",'PUT','DELETE'])
def getAllReviews(request, column_name=None):
    if request.method == "GET":
        data = request.GET
        salon = SalonDetails.objects.get(id=data['salon_id'])
        current_datetime = timezone.now()
        selected_branch = Branch.objects.get(salon=salon,id=data['branch_id'])
        if not Subscription.objects.filter(end_date__gt=current_datetime,
                                            name_of_subscription="PREMIUM",
                                            salon=salon,
                                            paid=True):
            return Response({
                    "message": "SALON DO NOT HAVE PREMIUM SUBSCRIPTION",
                    "status": FAILED_STATUS_CODE,
                    }) 
        review = Review.objects.filter(branch=selected_branch)
        review_serializer = ReviewSerializer(review, many=True)
        
        return Response({
            "data": {
                "count": len(review_serializer.data),
                "rows": review_serializer.data
            },
            "message": APIMessages.REVIEW_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    if request.method == 'POST':
        data = request.data
        if column_name != None:
            try:
                invoice = Invoice.objects.get(transaction=column_name)
                first_appointment = invoice.appointment.all().first()
                branch = first_appointment.branch
                all_appointment = invoice.appointment.all()
                salon = first_appointment.branch.salon
                comment = request.data.get('feedback')
                rating = request.data.get('rating')
                user = first_appointment.user
                customer = Customer.objects.get(user=user)

                current_datetime = timezone.now()

                if not Subscription.objects.filter(end_date__gt=current_datetime,
                                            name_of_subscription="PREMIUM",
                                            salon=salon,
                                            paid=True):
                    
                    return Response({
                        "message": "SALON DO NOT HAVE PREMIUM SUBSCRIPTION",
                        "status": FAILED_STATUS_CODE,
                        })

                try:
                    review = Review(
                        branch = branch,
                        invoice=invoice,
                        salon=salon,
                        comment=comment,
                        rating=rating,
                        user=customer,
                    )
                    review.save()

                    for appoint in all_appointment:
                        service = appoint.service.all().first()
                        review.service.add(service)

                    return Response({
                        "message": APIMessages.REVIEW_CREATED.value,
                        "status": SUCCESS_STATUS_CODE,
                        })
                
                except Exception:
                    return Response({
                        "message": APIMessages.ERROR.value,
                        "status": FAILED_STATUS_CODE,
                    })
            except Exception as e:
                log_error_with_api_endpoint(request, e)
                return Response({
                    "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                    "status": FAILED_STATUS_CODE,
                })
        else:
            transaction_number = data['invoice_id']
            try:
                invoice = Invoice.objects.filter(transaction=transaction_number).first()
                review = Review.objects.filter(invoice=invoice).first()
                if review.comment != "":
                    return Response({
                        "message": APIMessages.CANT_SEE_REVIEW.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
                else:
                    return Response({
                        "status": FAILED_STATUS_CODE,
                    })
            except Exception as e:
                log_error_with_api_endpoint(request, e)
                return Response({
                    "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                    "status": FAILED_STATUS_CODE,
                })  
    elif request.method == 'PUT':
        try:
            if column_name is not None:
                selected_branch_id = request.data.get('branch_id')
                customer_id = request.data.get('customer_id')
                service_id = request.data.get('service_id')
                service = Service.objects.get(id=service_id)
                branch = Branch.objects.get(id=selected_branch_id)
                salon = SalonDetails.objects.get(branch=branch)
                comment = request.data.get('comment')
                rating = request.data.get('rating')
                customer = Customer.objects.get(id=customer_id)

                try:
                    review = Review.objects.get(
                        id=column_name
                    )
                    if review.user != customer or review.service != service:
                        return Response({
                            "message": APIMessages.ERROR.value,
                            "status": FAILED_STATUS_CODE,
                        })
                    review.rating = rating
                    review.comment = comment
                    review.save()

                    return Response({
                        "message": APIMessages.REVIEW_UPDATED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
                
                except Exception:
                    return Response({
                        "message": APIMessages.ERROR.value,
                        "status": FAILED_STATUS_CODE,
                    })
                
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })  
    elif request.method == "DELETE":
        if column_name is not None:
            customer_id = request.data.get('customer_id')
            service_id = request.data.get('service_id')
            service = Service.objects.get(id=service_id)
            customer = Customer.objects.get(id=customer_id)

            try:
                review = Review.objects.get(
                    id=id
                )
                if review.user != customer or review.service != service:
                    return Response({
                        "message": APIMessages.ERROR.value,
                        "status": FAILED_STATUS_CODE,
                    })
                else:
                    review.delete()
                    return Response({
                        "message": APIMessages.REVIEW_DELETED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
            
            except Exception:
                return Response({
                    "message": APIMessages.ERROR.value,
                    "status": FAILED_STATUS_CODE,
                })
