from rest_framework.decorators import api_view
from api.constants import SUCCESS_STATUS_CODE, APIMessages
from rest_framework.response import Response
from api.serializers import SalarySerializer
from backend.models import *

@api_view(['GET'])
def getAllSalary(request, column_name=None, column_value=None):
    data = request.GET
    if request.method == "GET":
        if column_value is None:
            branch = Branch.objects.get(id=data['branch_id'])
            employee = Employee.objects.get(
                branch=branch,
                id=data['employee_id']
            )
            salary = Salary.objects.filter(employee=employee)
            serializer = SalarySerializer(salary, many=True)
            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": len(serializer.data),
                    "rows": serializer.data
                },
                "message": APIMessages.SALARY_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })
        else:
            valid_fields = [f.name for f in Expense._meta.get_fields()]
            if column_name not in valid_fields:
                return Response({"message": f"Invalid column name: {column_name}", "status": 400})

            # Build a dynamic filter using double-underscore notation
            filter_kwargs = {
                f"{column_name}__exact": column_value} if column_name else {}
            salary = Salary.objects.get(**filter_kwargs)
            serializer = SalarySerializer(salary, many=False)
            # Return the serialized data in the response
            return Response({
                "data": {
                    "count": 1,
                    "rows": [serializer.data]
                },
                "message": APIMessages.SALARY_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

@api_view(['PUT'])
def editSalary(request):
    data = request.data
    try:
        user = User.objects.get(id=data['user_id'])
        salon = SalonDetails.objects.get(id=data['salon_id'], user=user)
        branch = Branch.objects.get(id=data['branch_id'], salon=salon)
        employee = Employee.objects.get(id=data['employee'], branch=branch,status="Active")
        salary = Salary.objects.get(
            employee=employee, id=data['object_id'], month=data['month'])
        salary.deduction = data['deduction']
        salary.total_salary = data['total_salary']
        salary.paid = bool(data['paid'])
        salary.date_issued = datetime.datetime.now()
        salary.save()
        return Response({
            "message": f"Successfully Made Salary For Employee {salary.employee}",
            "status": 200,
        })
    except Exception:
        return Response({
            'message': "Error",
            'status': 500
        })

def staffSalary(request, obj, month, date_issued, parameter):
    if parameter == "ADD-SALARY":
        for appointment in obj.appointment.all():
            staff_count = appointment.staff_assigned.count()
            for staff in appointment.staff_assigned.all():
                stf = Employee.objects.get(id=staff.id,status="Active")
                service_incentive_amount = 0
                product_incentive_amount = 0
                if appointment.category == 'Product':
                    product_incentive_amount = ((stf.product_incentive/staff_count)/100 * (
                        int(appointment.totalPrice) - int(appointment.discount_price)))
                elif appointment.category == 'Service':
                    service_incentive_amount = ((stf.service_incentive/staff_count)/100 * (
                        int(appointment.totalPrice) - int(appointment.discount_price)))
                if Salary.objects.filter(employee=stf, month=month):
                    salary = Salary.objects.get(employee=stf, month=month)
                    salary.total_salary = salary.total_salary + service_incentive_amount
                    salary.service_incentive_amount = salary.service_incentive_amount + \
                        service_incentive_amount
                    salary.product_incentive_amount = salary.product_incentive_amount + \
                        product_incentive_amount
                    salary.save()
                else:
                    salary = Salary(
                        month=month,
                        employee=stf,
                        basic=stf.base_salary,
                        service_incentive_amount=service_incentive_amount,
                        product_incentive_amount=product_incentive_amount,
                        total_salary=stf.base_salary + service_incentive_amount + product_incentive_amount,
                        date_issued=date_issued
                    )
                    salary.save()

    elif parameter == 'DELETE-SALARY':
        staff_count = obj.staff_assigned.count()
        for staff in obj.staff_assigned.all():
            stf = Employee.objects.get(id=staff.id,status="Active")
            service_incentive_amount = (
                (stf.service_incentive/staff_count)/100 * (int(obj.totalPrice) - int(obj.discount_price)))
            if Salary.objects.filter(employee=stf, month=month):
                salary = Salary.objects.get(employee=stf, month=month)
                salary.total_salary = salary.total_salary - service_incentive_amount
                salary.service_incentive_amount = salary.service_incentive_amount - \
                    service_incentive_amount
                salary.save()
                if salary.total_salary == 0:
                    salary.delete()
            else:
                pass
    return Response({
        "message": APIMessages.DELETE_ALL_SALARYS.value,
        "status": SUCCESS_STATUS_CODE,
    })
