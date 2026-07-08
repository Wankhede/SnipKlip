from rest_framework.response import Response
from backend.models import *
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import Group
import random
from django.http import HttpResponse,JsonResponse
import csv
from app.settings.base import BASE_DIR
import string

def add_remark(csv_file, arg, remark_arg, loop_count):
    """
    Function to add remarks to a CSV file.

    Parameters:
        csv_file (File): The CSV file to be modified.
        arg (str): The operation to be performed ('Add Value' in this case).
        remark_arg (str): The remark to be added.
        loop_count (int): The loop count for row index.

    Returns:
        None
    """
    data = []
    existing_file_path = str(BASE_DIR) + "/media/" + str(csv_file.file)
    new_column_header = 'Remark'

    # Open CSV file
    with open(existing_file_path, 'r') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)

    # Adding "Remark" column if needed in CSV file
    try:
        if data[0][3] or data[0][4] == new_column_header:
            pass
    except Exception:
        data[0].append(new_column_header)

    # Adding Value for each Row
    if arg == "Add Value":
        if len(data[loop_count + 1]) == 4:
            data[loop_count + 1][3] = remark_arg
        else:
            data[loop_count + 1].append(remark_arg)

    # Writing all Rows values into File
    with open(existing_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerows(data)

def create_customer(request, id, username, email, mobile, branch_id):
    """
    Function to create a customer.

    Parameters:
        request: The Django request object.
        id (int): User ID.
        username (str): Username.
        email (str): Email.
        mobile (str): Mobile number.
        branch_id (int): Branch ID.

    Returns:
        Response: JSON response.
    """
    # Basic validation
    if not User.objects.filter(id=id).exists() or not Branch.objects.filter(id=branch_id).exists():
        return Response({'message': "User Not Found", 'status': 200})

    user = User.objects.get(id=id)

    # Check if customer already exists
    if Customer.objects.filter(user=user,status='Active').exists():
        customer = Customer.objects.get(user=user)
        branch = Branch.objects.get(id=branch_id)

        # Check if mobile number for branch-customer pair already exists
        if not BranchCustomerMobile.objects.filter(customer_user=customer, branch=branch).exists():
            branch_mobile = BranchCustomerMobile(branch=branch, customer_user=customer, mobile=mobile)
            branch_mobile.save()
            customer.mobile_number.add(branch_mobile)
            customer.save()
        else:
            pass
    else:
        # Create new customer
        first_name = username.split(" ")[0]
        if len(username.split(" ")) >= 2:
            last_name = username.split(" ")[1]
        else:
            last_name = ""

        branch = Branch.objects.get(id=branch_id)
        customer = Customer(user=user, email=email, name=username,first_name=first_name,last_name=last_name)
        customer.save()

        # Add mobile number for branch-customer pair
        try:
            branch_mobile = BranchCustomerMobile(branch=branch, customer_user=customer, mobile=str(mobile))
            branch_mobile.save()
            customer.mobile_number.add(branch_mobile)
            customer.save()
        except Exception as e:
            pass
    return Response({'message': "Customer created successfully", 'status': 200})

def insert_customer(request,df,sync_data,branch_id,length,data):
    characters = string.ascii_letters + string.digits
    random_string = ''.join(random.choices(characters, k=8))

    if User.objects.get(id=2).is_superuser:
        if sync_data:
            all_user = User.objects.all()
            for user in all_user:
                if Customer.objects.filter(user=user,status='Active'):
                    customer_user = Customer.objects.get(user=user)
                    branch = Branch.objects.get(id=branch_id)

                    if BranchCustomerMobile.objects.filter(customer_user=customer_user,branch=branch):
                        pass
                    else:
                        branch_mobile = BranchCustomerMobile(branch=branch,customer_user=customer_user,mobile=user.mobile)
                        branch_mobile.save()

                        customer_user.mobile_number.add(branch_mobile)
                        customer_user.save()
                else:
                    if user.mobile == None or user.mobile == "":
                        user.mobile = None
                    if user.email == 'nan' or user.email == "" or user.email == None:
                        user.email = ""
                    
                    # Create new customer
                    first_name = (user.username).split(" ")[0]
                    if len(user.username).split(" ") >= 2:
                        last_name = username.split(" ")[1]
                    else:
                        last_name = ""

                    customer = Customer(user=user,email=user.email,username=user.username,first_name=first_name,last_name=last_name)
                    customer.save()

                    branch_mobile = BranchCustomerMobile(branch=branch,customer_user=customer,mobile=user.mobile)
                    branch_mobile.save()

                    customer.mobile_number.add(branch_mobile)
                    customer.save()

    df['Remark'] = ""
    for i in range(0, length):
        if User.objects.filter(username=df["Name"][i]):
            user_count = len(User.objects.filter(username__icontains = df["Name"][i]))
            user_sr = int(user_count)+1 
            username = df["Name"][i] + " " + str(user_sr)
        else:
            username = df["Name"][i]

        first_name = username.split(" ")[0]
        if len(username.split(" ")) >= 2:
            last_name = username.split(" ")[1]
        else:
            last_name = ""

        if df["Email"][i] == None or str(df["Email"][i]) == "nan" or len(str(df["Email"][i]).split("@")) != 2:
            email = ""
        else:
            email = df["Email"][i]

        try:
            user_added = User(
                username=username,
                name=first_name + ' ' + last_name,
                email=email,
                mobile=df["Mobile"][i],
                password = make_password(random_string),
                first_name = first_name,
                last_name = last_name
            ) 
            if user_added.email == "":
                if User.objects.filter(mobile=user_added.mobile):
                    df.at[i, 'Remark'] = "it will Not get Save(mobile Matched)"
                    add_remark(data,'Add Value',"it will Not get Save(mobile Matched)",i)
                    user_added = User.objects.get(mobile=user_added.mobile)
                    create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
                else:
                    df.at[i, 'Remark'] = "Success"
                    add_remark(data,"Add Value","Success",i)
                    user_added.save()
                    create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
                    try:
                        group = Group.objects.get(name='Customer')
                    except Exception:
                        group = Group(name="Customer")
                        group.save()
                    user_added.groups.add(group)
            elif len(user_added.email) >= 5:
                if User.objects.filter(email=user_added.email) and User.objects.filter(mobile=user_added.mobile):
                    df.at[i, 'Remark'] = "it will Not get Save(email and mobile Matched)"
                    add_remark(data,"Add Value","it will Not get Save(email and mobile Matched)",i)
                    user_added = User.objects.get(mobile=user_added.mobile,email=user_added.email)
                    create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
                else:
                    user_added.save()
                    df.at[i, 'Remark'] = "Success"
                    add_remark(data,"Add Value","Success",i)
                    try:
                        group = Group.objects.get(name='Customer')
                    except Exception:
                        group = Group(name="Customer")
                        group.save()
                    user_added.groups.add(group)
                    create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
            else:
                try:
                    data[i+1].append("Success")
                    user_added.save()
                    create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
                except Exception:
                    data[i+1].append("it will Not get Save (Something Happened)")
                    
        except Exception:
            user_added = User.objects.get(name = user_added.name)
            create_customer(request,user_added.id,user_added.name,user_added.email,user_added.mobile,branch_id)
            data[i+1].append("it will Not get Save (name mathed)")
            
    ############### Finally Adding all Remarks, which we have Added Values above for each Row ##############
    add_remark(data,"","",0)
        