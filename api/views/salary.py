from rest_framework.decorators import api_view
from api.constants import SUCCESS_STATUS_CODE, APIMessages
from rest_framework.response import Response
from api.serializers import SalarySerializer
from backend.models import *
import datetime

@api_view(['GET', 'PUT', 'POST'])
def getAllSalary(request, column_name=None, column_value=None):
    if request.method in ("PUT", "POST"):
        return editSalary(request)

    data = request.GET
    try:
        if column_value is None:
            branch_id = data.get('branch_id')
            employee_id = data.get('employee_id')
            if not branch_id:
                return Response({"message": "branch_id is required", "status": 400})

            branch = Branch.objects.filter(id=branch_id).first()
            if branch is None:
                return Response({"message": "Branch not found", "status": 404})

            if employee_id:
                employee = Employee.objects.filter(branch=branch, id=employee_id).first()
                if employee is None:
                    return Response({"message": "Employee not found", "status": 404})
                salary = Salary.objects.filter(employee=employee)
            else:
                salary = Salary.objects.filter(employee__branch=branch)

            serializer = SalarySerializer(salary, many=True)
            return Response({
                "data": {
                    "count": len(serializer.data),
                    "rows": serializer.data
                },
                "message": APIMessages.SALARY_RETRIEVED.value,
                "status": SUCCESS_STATUS_CODE,
            })

        valid_fields = [f.name for f in Salary._meta.get_fields()]
        if column_name not in valid_fields:
            return Response({"message": f"Invalid column name: {column_name}", "status": 400})

        filter_kwargs = {f"{column_name}__exact": column_value} if column_name else {}
        salary = Salary.objects.filter(**filter_kwargs).first()
        if salary is None:
            return Response({"message": "Salary not found", "status": 404})
        serializer = SalarySerializer(salary, many=False)
        return Response({
            "data": {
                "count": 1,
                "rows": [serializer.data]
            },
            "message": APIMessages.SALARY_RETRIEVED.value,
            "status": SUCCESS_STATUS_CODE,
        })
    except Exception as exc:
        return Response({"message": str(exc), "status": 500})


def editSalary(request):
    data = request.data
    try:
        user = User.objects.filter(id=data.get('user_id')).first()
        salon = SalonDetails.objects.filter(id=data.get('salon_id'), user=user).first() if user else None
        branch = Branch.objects.filter(id=data.get('branch_id'), salon=salon).first() if salon else None
        employee = Employee.objects.filter(
            id=data.get('employee'), branch=branch, status="Active"
        ).first() if branch else None
        if employee is None:
            return Response({'message': "Employee not found", 'status': 404})

        salary = Salary.objects.filter(
            employee=employee, id=data.get('object_id'), month=data.get('month')
        ).first()
        if salary is None:
            return Response({'message': "Salary not found", 'status': 404})

        salary.deduction = data.get('deduction', salary.deduction)
        salary.total_salary = data.get('total_salary', salary.total_salary)
        salary.paid = bool(data.get('paid'))
        salary.date_issued = datetime.datetime.now()
        salary.save()
        return Response({
            "message": f"Successfully Made Salary For Employee {salary.employee}",
            "status": 200,
        })
    except Exception as exc:
        return Response({
            'message': str(exc) or "Error",
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
