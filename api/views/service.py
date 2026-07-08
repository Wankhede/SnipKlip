from api.common import apply_filters, custom_pagination, get_all_table_records, log_error_with_api_endpoint
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import ServiceSerializer
from backend.models import Branch, Employee, Service
from api.constants import *

# @group_required('Manager')
@api_view(['GET',"POST",'PUT'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllServices(request, column_name=None, column_value=None):
    if request.method == "GET":
        try:
            if column_value is None:
                branch_id = request.GET['branch_id']
                request_args = request.GET
                if branch_id == '-1':
                    all_services = get_all_table_records(request, Service)
                else:
                    branch = Branch.objects.get(id=branch_id)
                    all_services = Service.objects.filter(branch=branch).order_by('-id')

                final_services_list = apply_filters(Service, all_services, request_args)

                total_rows = all_services.count()

                # Call the custom_pagination function to get the paginated items.
                final_services_list = custom_pagination(request, final_services_list)            

                serializer = ServiceSerializer(final_services_list, many=True)
                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": total_rows,
                        "rows": list(serializer.data)
                    },
                    "message": APIMessages.ALL_SERVICE_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                try:
                    # Check if column_name is a valid field in the Service model
                    valid_fields = [f.name for f in Service._meta.get_fields()]
                    if column_name not in valid_fields:
                        return Response({"message": f"Invalid column name: {column_name}", "status":400})

                    # Build a dynamic filter using double-underscore notation
                    filter_kwargs = {f"{column_name}__exact": column_value} if column_name else {}
                    all_services = Service.objects.get(**filter_kwargs)
                    
                    serializer = ServiceSerializer(all_services, many=False)
                    # Return the serialized data in the response
                    return Response({
                            "data": {
                                "count": 0,
                                "rows": [serializer.data]
                            },
                            "message": APIMessages.SERVICE_RETRIEVED.value,
                            "status": SUCCESS_STATUS_CODE,
                        })
                except Employee.DoesNotExist:
                    return Response({
                        "message": APIMessages.SERVICE_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })  

    elif request.method == 'POST':
        try:
            selected_branch_id = request.data.get('branch_id')
            branch = Branch.objects.get(id=selected_branch_id)
            name = request.data.get('name')
            price = request.data.get('price')
            category = request.data.get('category')
            description = request.data.get('description')
            time_for_each_service = request.data.get('time_for_each_service')

            try:
                expen = Service(
                    name = name,
                    branch = branch,
                    description = description,
                    price = float(price),
                    category = category,
                    time_for_each_service = time_for_each_service
                )
                expen.save()

                return Response({
                    "message": APIMessages.SERVICE_CREATED.value,
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

    elif request.method == 'PUT':
        try:
            id = request.data.get('id', None)
            if id is not None:
                selected_branch_id = request.data.get('branch_id', 1)
                branch = Branch.objects.get(id=selected_branch_id)
                name = request.data.get('name')
                category = request.data.get('category')
                price = request.data.get('price')
                time_for_each_service = request.data.get('time_for_each_service')
                description = request.data.get('description')
                if len("".join(description.split(" "))) == 0 or not description or not price or price == None or price == "":
                    return Response({
                        "message": APIMessages.FILL_FIELDS.value,
                        "status": FAILED_STATUS_CODE,
                    })
                
                try:
                    service = Service.objects.get(
                        id=id
                    )
                    service.name = name
                    service.price = price
                    service.category = category
                    service.description = description
                    service.time_for_each_service = time_for_each_service
                    service.save()

                    return Response({
                        "message": APIMessages.SERVICE_UPDATED.value,
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