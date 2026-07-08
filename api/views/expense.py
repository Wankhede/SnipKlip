from api.common import apply_filters, custom_pagination, get_all_table_records, log_error_with_api_endpoint
from api.decorators import jwt_authentication_required
from api.throttles import SustainedRateThrottle
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from api.serializers import ExpenseSerializer
from backend.models import Branch, Expense, Employee
from api.constants import *

# @group_required('Manager')
@api_view(['GET',"POST",'PUT'])
@throttle_classes([SustainedRateThrottle])
@jwt_authentication_required
def getAllExpenses(request, column_name=None, column_value=None):
    if request.method == "GET":
        try:
            if column_value is None:
                branch_id = request.GET['branch_id']
                request_args = request.GET
                if branch_id == '-1':
                    all_expenses = get_all_table_records(request, Expense)
                else:
                    branch = Branch.objects.get(id=branch_id)
                    all_expenses = Expense.objects.filter(branch=branch).order_by('-id')

                final_expenses_list = apply_filters(Expense, all_expenses, request_args)

                total_rows = final_expenses_list.count()

                # Call the custom_pagination function to get the paginated items.
                final_expenses_list = custom_pagination(request, final_expenses_list)            

                serializer = ExpenseSerializer(final_expenses_list, many=True)
                # Return the serialized data in the response
                return Response({
                    "data": {
                        "count": total_rows,
                        "rows": list(serializer.data)
                    },
                    "message": APIMessages.ALL_EXPENSE_RETRIEVED.value,
                    "status": SUCCESS_STATUS_CODE,
                })
            else:
                try:
                    # Check if column_name is a valid field in the Expense model
                    valid_fields = [f.name for f in Expense._meta.get_fields()]
                    if column_name not in valid_fields:
                        return Response({"message": f"Invalid column name: {column_name}", "status":400})

                    # Build a dynamic filter using double-underscore notation
                    filter_kwargs = {f"{column_name}__exact": column_value} if column_name else {}
                    all_expenses = Expense.objects.get(**filter_kwargs)
                    
                    serializer = ExpenseSerializer(all_expenses, many=False)
                    # Return the serialized data in the response
                    return Response({
                            "data": {
                                "count": 0,
                                "rows": [serializer.data]
                            },
                            "message": APIMessages.EXPENSE_RETRIEVED.value,
                            "status": SUCCESS_STATUS_CODE,
                        })
                except Employee.DoesNotExist:
                    return Response({
                        "message": APIMessages.EXPENSE_NOT_FOUND.value,
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
            description = request.data.get('description')
            amount = request.data.get('amount')

            try:
                expen = Expense(
                    branch = branch,
                    description = description,
                    amount = float(amount)
                )
                expen.save()

                return Response({
                    "message": APIMessages.EXPENSE_CREATED.value,
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
                description = request.data.get('description')
                amount = request.data.get('amount')
                status = request.data.get('status')

                if len("".join(description.split(" "))) == 0 or not description or not amount or amount == None or amount == "":
                    return Response({
                        "message": APIMessages.FILL_FIELDS.value,
                        "status": FAILED_STATUS_CODE,
                    })
                
                try:
                    expen = Expense.objects.get(
                        id=id
                    )
                    expen.amount = amount
                    expen.description = description
                    expen.status = status
                    expen.save()

                    return Response({
                        "message": APIMessages.EXPENSE_UPDATED.value,
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