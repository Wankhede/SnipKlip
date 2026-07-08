from backend.views.common.conditions import in_group,group_match
from backend.models import *

def verified_condition(request):
    salon_verified = False
    customer_verified = False
    manager_verified = False
    staff_verified = False
    admin_verified = False
    vendor_verified = False
    if request.user.is_authenticated:
        if group_match('Manager',request) == True:
            salon_verified = False
            customer_verified = False
            manager_verified = True
            staff_verified = False
            vendor_verified = False
        elif group_match('Salon',request) == True and group_match('Manager',request) == False:
            salon_verified = True
            customer_verified = False
            manager_verified = False
            staff_verified = False
            vendor_verified = False
        elif group_match('Staff',request) == True:
            salon_verified = False
            customer_verified = False
            manager_verified = False
            staff_verified = True
            vendor_verified = False
        elif group_match('Customer',request) == True:
            salon_verified = False
            customer_verified = True
            manager_verified = False
            staff_verified = True
            vendor_verified = False
        elif group_match('Admin',request) == True:
            salon_verified = False
            customer_verified = False
            manager_verified = False
            staff_verified = False
            admin_verified = True
            vendor_verified = False
        elif group_match('Vendor',request) == True:
            salon_verified = False
            customer_verified = False
            manager_verified = False
            staff_verified = False
            admin_verified = False
            vendor_verified = True
        else:
            salon_verified = False
            customer_verified = False
            manager_verified = False
            staff_verified = False
            vendor_verified = False
    else:
        pass
    context = {
                'salon_verified':salon_verified,
                'customer_verified':customer_verified,
                'manager_verified':manager_verified,
                'staff_verified':staff_verified,
                'admin_verified':admin_verified
    }
    return context