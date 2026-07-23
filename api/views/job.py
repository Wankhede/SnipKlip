from api.common import custom_pagination, get_all_table_records
from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
from api.serializers import JobSerializer
from api.constants import *

    
@api_view(['PUT', 'POST','GET'])
def getAllJobs(request, id=None):
    if request.method == "GET":
        if id is None:
            branch_id = request.GET['branch_id']

            if branch_id == '-1':
                jobs = get_all_table_records(request, Job)
            else:
                salon = SalonDetails.objects.get(branch__id=branch_id)
                jobs = Job.objects.filter(salon=salon).order_by('-id').reverse()
            
            # Call the custom_pagination function to get the paginated items.
            jobs = custom_pagination(request, jobs)   
            
            serializer = JobSerializer(jobs, many=True)
            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": len(jobs),
                    "rows": serializer.data
                },
                "message": APIMessages.ALL_JOB_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            pass
    elif request.method == "PUT":
        # Update a product
        try:
            job = Job.objects.get(id=id)
        except Job.DoesNotExist:
            return Response({"error": APIMessages.PRODUCT_NOT_FOUND.value}, status=NOT_FOUND_STATUS)

        serializer = JobSerializer(job, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=BAD_REQUEST_STATUS)

    elif request.method == "POST":
        job_name = request.data.get('jobName','')
        job_price = request.data.get('price','')
        job_descrition = request.data.get('jobDescription','')
        job_sku = request.data.get('job_sku','')
        job_availablity = request.data.get('status','')
        job_weight = request.data.get('job_weight','')
        job_weight_unit = request.data.get('job_weight_unit','')
        job_price_currency = request.data.get('job_price_currenry','')
        job_vendor = request.data.get('job_vendor','')
        job_category = request.data.get('category','')
        job_collection = request.data.get('job_collection','')
        job_tag = request.data.get('job_tag','')
        job_image = request.FILES.get('job_image','')
        job_quantity = request.data.get('quantity','')
        data = request.data
        if not hasattr(data, 'get'):
            return Response({
                'message': 'Invalid JSON body; expected an object',
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        try:
            user = User.objects.get(id=data.get('user_id'))
            salon_associate = SalonDetails.objects.get(user=user)
        except (User.DoesNotExist, SalonDetails.DoesNotExist, TypeError, ValueError) as e:
            return Response({
                'message': f'Invalid job payload: {e}',
                'status': BAD_REQUEST_STATUS,
            }, status=BAD_REQUEST_STATUS)

        if job_image == None or not job_image or job_image == "":
            job_image= None
        else:
            job_image = job_image

        CREATED_CODE = 200
        ERROR_CODE = 400
        try:
            # Creating Job object with data from POST request
            job_save = Job(
                salon=salon_associate,
                name=job_name,
                price=job_price,
                description=job_descrition,
                category=job_category,
                image=job_image,
                availablity=job_availablity,
                quantity = job_quantity
            )
            job_save.save()
            return Response({
                    'message':APIMessages.PRODUCT_CREATED.value,
                    'status':CREATED_CODE
                })
        except Exception:
            return Response("Error", status=ERROR_CODE)
        
@api_view(['POST'])
def deleteJob(request,job_id):
    data = request.data
    if not Job.objects.filter(id=job_id) or not User.objects.filter(id=data['user_id']):
        return Response({
            'message':APIMessages.PRODUCT_NOT_FOUND.value,
            'status':BAD_REQUEST_STATUS
        })
    else:
        job = Job.objects.get(id=job_id)
        user = User.objects.get(id=data['user_id'])
        if not SalonDetails.objects.filter(user=user):
            return Response({
                'message':APIMessages.SALON_NOT_FOUND.value,
                'status':BAD_REQUEST_STATUS
            })
        else:
            salon = SalonDetails.objects.get(user=user)
            if not Job.objects.filter(id=job_id,salon=salon):
                return Response({
                    'message':APIMessages.PRODUCT_DOES_NOT_BELONGS_TO_YOU.value,
                    'status':BAD_REQUEST_STATUS
                })
            else:
                job.delete()
                return Response({
                    'message':APIMessages.PRODUCT_DELETE_SUCCESS.value,
                    'status':BAD_REQUEST_STATUS
                })

