from random import randint
from api.common import apply_filters, custom_pagination, get_all_table_records, log_error_with_api_endpoint
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import EmployeeSerializer
from backend.models import Branch, Expense, Employee, User
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
from backend.views.vendor.essentials import create_username
from api.constants import *

# @group_required('Manager')
@api_view(['POST', 'PUT', 'GET'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllEmployees(request, column_name=None, column_value=None):
    if request.method == "GET":
        try:
            if column_value is None:
                request_args = request.GET
                branch_id = request.GET['branch_id']
                if branch_id == '-1':
                    all_employees = get_all_table_records(request, Employee)
                else:
                    all_employees = Employee.objects.filter(
                        branch__id=branch_id).order_by('-id')
                
                final_employees_list = apply_filters(Employee,all_employees,request_args)
                
                total_rows = final_employees_list.count()

                # Call the custom_pagination function to get the paginated items.
                all_employees = custom_pagination(request, final_employees_list)

                serializer = EmployeeSerializer(final_employees_list, many=True)
                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": total_rows,
                        "rows": serializer.data
                    },
                    "message": APIMessages.ALL_EMPLOYEE_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                try:
                    # Check if column_name is a valid field in the Expense model
                    valid_fields = [f.name for f in Expense._meta.get_fields()]
                    if column_name not in valid_fields:
                        return Response({"message": f"Invalid column name: {column_name}", "status": 400})

                    # Build a dynamic filter using double-underscore notation
                    filter_kwargs = {
                        f"{column_name}__exact": column_value} if column_name else {}
                    all_employees = Employee.objects.get(**filter_kwargs)

                    serializer = EmployeeSerializer(all_employees, many=False)
                    # Return the serialized data in the response
                    return Response({
                        "data": {
                            "count": 0,
                            "rows": [serializer.data]
                        },
                        "message": APIMessages.EMPLOYEE_RETRIEVED.value,
                        "status": SUCCESS_STATUS_CODE,
                    })
                except Employee.DoesNotExist:
                    return Response({
                        "message": APIMessages.EMPLOYEE_NOT_FOUND.value,
                        "status": NOT_FOUND_STATUS,
                    })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })

    elif request.method == "POST":
        try:
            selected_branch_id = request.data['branch_id']
            first_name = request.data['first_name']
            last_name = request.data['last_name']
            username = create_username(first_name, last_name)
            email = request.data['email']
            mobile = request.data['mobile']
            employee_type = request.data['employee_type']
            password = username + str(randint(1000, 9999))
            product_incentive = request.data['product_incentive']
            service_incentive = request.data['service_incentive']
            base_salary = request.data['base_salary']

            # Check Email and Mobile Exists or Not
            if User.objects.filter(email=email, mobile=mobile):
                return Response({
                    "message": APIMessages.BOTH_ALREADY_EXISTS.value,
                    "status": FAILED_STATUS_CODE,
                })

            # Check Mobile Number Exists or Not
            if User.objects.filter(mobile=mobile):
                return Response({
                    "message": APIMessages.MOBILE_ALREADY_EXISTS.value,
                    "status": FAILED_STATUS_CODE,
                })

            # Check Email Exists or Not
            # if User.objects.filter(email=email):
            #     return Response({
            #         "message": APIMessages.EMAIL_ALREADY_EXISTS.value,
            #         "status": FAILED_STATUS_CODE,
            #     })

            # Create a new user and save it to the database
            user_save = User(
                username=username,
                first_name=first_name,
                last_name=last_name,
                name=first_name + ' ' + last_name,
                email=email,
                mobile=mobile,
                password=make_password(password)
            )
            user_save.save()

            # Check if the employee_type group exists, else create a new one
            try:
                group = Group.objects.get(name=employee_type)
            except Group.DoesNotExist:
                group = Group(name=employee_type)
                group.save()

            # Add the user to the employee_type group
            user_save.groups.add(group)

            # Get branch associated with the salon
            branch = Branch.objects.get(id=selected_branch_id)

            # Create a new employee and save it to the database
            emp_save = Employee(
                user=user_save,
                branch=branch,
                employee_type=employee_type,
                product_incentive=int(product_incentive),
                service_incentive=int(service_incentive),
                base_salary=base_salary
            )
            emp_save.save()

            if employee_type == "Manager":
                try:
                    branch_detail = Branch.objects.get(id=selected_branch_id)
                    branch_detail.manager = user_save
                    branch_detail.save()
                except Branch.DoesNotExist:
                    return Response({
                        "message": APIMessages.ERROR.value,
                        "status": FAILED_STATUS_CODE,
                    })

            # Return the serialized data in the response
            return Response({
                "message": APIMessages.EMPLOYEE_CREATED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })

    elif request.method == "PUT":
        try:
            id = request.data.get('id')
            if id is not None:
                first_name = request.data['first_name']
                mobile_no = request.data['mobile']
                email = request.data['email']
                last_name = request.data['last_name']
                username = create_username(first_name, last_name)
                selected_branch_id = request.data.get('branch_id')
                employee_type = request.data.get('employee_type')
                product_incentive = int(request.data.get('product_incentive'))
                service_incentive = int(request.data.get('service_incentive'))
                base_salary = int(request.data.get('base_salary'))
                status = request.data.get('status')

                # Get the salon user and their associated salon details
                branch = Branch.objects.get(id=selected_branch_id)
                emp_save = Employee.objects.get(id=id)

                user = User.objects.get(id=emp_save.user.id)
                user.name = first_name + ' ' + last_name
                user.first_name = first_name
                user.last_name = last_name
                user.mobile = mobile_no
                user.email = email
                user.save()

                emp_save.employee_type = employee_type
                emp_save.product_incentive = product_incentive
                emp_save.service_incentive = service_incentive
                emp_save.base_salary = base_salary
                emp_save.status = status

                emp_save.save()

                # Return the serialized data in the response
                return Response({
                    "message": APIMessages.EMPLOYEE_UPDATED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                # Return the serialized data in the response
                return Response({
                    "message": APIMessages.EMPLOYEE_NOT_FOUND.value,
                    "status": BAD_REQUEST_STATUS,
                })
        except Exception as e:
            log_error_with_api_endpoint(request, e)
            return Response({
                "message": APIMessages.INTERNAL_SERVER_ERROR.value,
                "status": FAILED_STATUS_CODE,
            })
