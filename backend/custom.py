from django import template
from .models import *
from backend.crypto_utils import load_fernet_key
register = template.Library()
from cryptography.fernet import Fernet

def load_key():
    return load_fernet_key()


# @register.filter
# def minus(num,i):
#     return int(num)-float(i)



@register.filter
def encryptfunc(transaction):
    # key is generated
    key = load_key()

    # Create a Fernet object with the key
    f = Fernet(key)

    # Encrypt the transaction parameter
    encrypted_token = f.encrypt(transaction.encode('utf-8'))

    # Use the encrypted token as needed
    return(encrypted_token)

@register.filter
def get_user(num):
    return User.objects.get(id=num)

@register.filter
def index(num, i):
    index_number = i-1
    return num[index_number]

@register.filter(name='times') 
def times(number):
    return range(number)

@register.filter
def floatconvert(num):
    return float(num)

@register.filter
def minusone(num):
    return num-1

@register.filter
def get_transaction(order_id):
    try:
        appointment = Appointment.objects.get(order_id=order_id)
        transaction = Invoice.objects.get(appointment=appointment).transaction
    except:
        transaction = None
    return transaction

@register.filter
def minus(num,i):
    return float(num) - float(i)


@register.filter
def get_mode_of_payment(val):
    appointment = Appointment.objects.get(id=val)
    invoice = Invoice.objects.get(appointment=appointment)
    return invoice.mode_of_payment



@register.filter
def get_sub_total(val):
    invoice = Invoice.objects.get(id=val)
    sub_total = (invoice.total - (invoice.discount_added/100*invoice.total))
    return sub_total


@register.filter
def get_gst(val):
    invoice = Invoice.objects.get(id=val)
    gst = (invoice.total - (invoice.discount_added/100*invoice.total)) * 0.18
    return int(gst)


@register.filter
def get_payment_recieved(val):
    invoice = Invoice.objects.get(id=val)
    payment_recieved = (invoice.actual_amount - invoice.due_payment)
    return int(payment_recieved)


@register.filter
def get_element(val,num):
    val = list(val)
    return val[num-1]


@register.filter(name='times') 
def times(number):
    return range(number)



@register.filter(name='not_rated') 
def not_rated(number):
    return range(5-number)

@register.filter(name='find_length') 
def find_length(invoice_id):
    if Invoice.objects.filter(id=invoice_id):
        invoice = Invoice.objects.get(id=invoice_id)
        if len(invoice.appointment.all()) == 3:
            return True
        else:
            return False

@register.filter
def convertfloatless(num):
    return "{:.1f}".format(num)

@register.filter
def convertint(num):
    if num == "" or num == None or not num:
        return 0
    else:
        return int(num)
    
@register.filter(name='has_group') 
def has_group(user, group_name):
    return user.groups.filter(name=group_name).exists() 

@register.filter
def length(lis):
    return len(lis)

@register.filter(name='dict_key')
def dict_item(dictionary, i):
    a = dictionary[i]
    return a

@register.filter
def to_or(value):
    return value.replace("/"," or ")

@register.filter
def round_filter(value, places=0):
    if places == 0:
        return round(value)
    else:
        return round(value, places)

@register.filter
def splitfirst(value):
    return value.split(" ")[0]

