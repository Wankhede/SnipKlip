from rest_framework.decorators import api_view
from rest_framework.response import Response
from backend.models import *
import pandas as pd
from app.settings.base import BASE_DIR
from django.http import HttpResponse,JsonResponse
import csv
from .upload_data.customer_upload import insert_customer
from .upload_data.product_upload import insert_product
from .upload_data.expense_upload import insert_expense
from .upload_data.employee_upload import insert_employee
from .upload_data.service_upload import insert_service
import os
from api.constants import *
from rest_framework import status
from django.db import transaction

@api_view(['POST', 'GET', 'PUT'])
def UploadData(request):
    """
    API endpoint to handle file upload and data insertion.

    Supported methods:
        - POST: Upload a CSV file and insert data into the database.
        - GET: (Not implemented) Retrieve data from the database.
        - PUT: (Not implemented) Update data in the database.

    Parameters:
        request: The Django request object.

    Returns:
        Response: JSON response.
    """
    if request.method == "POST":
        user_id = request.data.get('user_id')

        # Validate user credentials (only allow specific user roles)
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'message': 'User not found.', 'status': status.HTTP_404_NOT_FOUND})

        allowed_roles = ["Admin", "Salon", "Manager"]
        if not (user.groups.filter(name__in=allowed_roles).exists() or user.is_superuser):
            return Response({'message': 'Invalid user credentials.', 'status': status.HTTP_403_FORBIDDEN})

        # Retrieve necessary data from the request
        csv_data = request.FILES.get('file')
        branch_id = request.data.get('branch_id')
        sync_data = request.data.get('SYNC_DATA')

        # Validate branch existence
        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({'message': 'Branch not found.', 'status': status.HTTP_404_NOT_FOUND})

        # Save the CSV file to the database
        with transaction.atomic():
            data = Data_CSV(file=csv_data, branch=branch)
            data.save()

            # Read CSV data using Pandas
            try:
                df = pd.read_excel(str(BASE_DIR) + "/media/" + str(data.file)) if data.file.name.endswith('.xlsx') else pd.read_csv(str(BASE_DIR) + "/media/" + str(data.file))
                length = len(df)
            except Exception:
                return Response({'message': 'Invalid CSV file format.', 'status': status.HTTP_400_BAD_REQUEST})

            # Determine the template and call the appropriate insert function
            template = request.POST.get('template', '')
            if template == 'CUSTOMER':
                response = insert_customer(request, df, sync_data, branch_id, length, data)
            elif template == 'PRODUCT':
                response = insert_product(request, df, sync_data, branch_id, length)
            elif template == 'EMPLOYEE':
                response = insert_employee(request, df, sync_data, branch_id, length)
            elif template == 'EXPENSE':
                response = insert_expense(request, df, sync_data, branch_id, length)
            elif template == 'SERVICE':
                response = insert_service(request, df, sync_data, branch_id, length, user_id)
                response['url'] = "media/" + str(data.file)
            else:
                return Response({'message': 'Invalid template specified.', 'status': status.HTTP_400_BAD_REQUEST})
        
        # Convert DataFrame to CSV content
        csv_content = df.to_csv(index=False, quoting=csv.QUOTE_NONNUMERIC)

        # Create a response with the CSV content
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="customer.csv"'
        return response

    """
    API endpoint to get CSV templates.

    Supported methods:
        - GET: Generate and return a CSV template based on the specified template type.

    Parameters:
        request: The Django request object.

    Returns:
        HttpResponse: CSV response.
    """
    if request.method == "GET":
        # Validate the presence of the 'template' parameter in the request
        template_type = request.GET.get('template', '')
        if not template_type:
            return Response({'message': 'Missing template parameter.', 'status': status.HTTP_400_BAD_REQUEST})

        # Generate CSV data based on the specified template
        if template_type == 'EMPLOYEE':
            data = []  # You can add sample data if needed
            return generate_csv_response(template_type, data)
        elif template_type == 'CUSTOMER':
            data = []  # You can add sample data if needed
            return generate_csv_response(template_type, data)
        elif template_type == 'PRODUCT':
            data = []  # You can add sample data if needed
            return generate_csv_response(template_type, data)
        elif template_type == 'EXPENSE':
            data = []  # You can add sample data if needed
            return generate_csv_response(template_type, data)
        elif template_type == 'SERVICE':
            data = []  # You can add sample data if needed
            return generate_csv_response(template_type, data)
        else:
            return Response({'message': 'Invalid template specified.', 'status': status.HTTP_400_BAD_REQUEST})

def generate_csv_response(template, data):
    """
    Function to generate a CSV response based on the specified template.

    Parameters:
        template (str): The template name.
        data (list): List of data to be written to the CSV.

    Returns:
        HttpResponse: CSV response.
    """
    # Create the HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')

    # Create a CSV writer
    writer = csv.writer(response)

    # Write the header row based on the template
    if template == "EMPLOYEE":
        writer.writerow(['Name', 'Email', 'Mobile', 'BASE_SALARY', 'Employee_Type', 'Service_Incentive', 'Product_Incentive'])
    elif template == 'CUSTOMER':
        writer.writerow(['Name', 'Email', 'Mobile'])
    elif template == 'PRODUCT':
        writer.writerow(['Name', 'Description', 'Price', 'Quantity', 'Vendor', 'Weight', 'Weight_Unit', 'SKU'])
    elif template == 'EXPENSE':
        writer.writerow(['Description', 'Amount'])
    elif template == 'SERVICE':
        writer.writerow(['Category Name', 'Service Name', 'Service Price', 'Service Time', 'Discount', 'Short Description'])

    # Write data to the CSV
    writer.writerows(data)

    return response