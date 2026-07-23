from rest_framework import serializers
from backend.models import *
from backend.models import Subscription
import datetime
import pytz


class SubscriptionSerializer(serializers.ModelSerializer):
    branch_name = serializers.CharField(source='branch.branch_name')

    class Meta:
        model = Subscription
        fields = ['branch_name', 'branch', 'credit_balance', 'end_date', 'id',
                  'name_of_subscription', 'order_id', 'paid', 'start_date', 'type', 'user']


class SalonDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalonDetails
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    group = serializers.StringRelatedField(
        source='groups.first', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email',
                  'mobile', 'date_joined', 'is_active', 'group']


class BranchSerializer(serializers.ModelSerializer):
    manager = UserSerializer()
    salon = SalonDetailsSerializer()
    manager_name = serializers.SerializerMethodField()

    class Meta:
        model = Branch
        fields = ['manager', 'manager_name', 'salon', 'id', 'branch_name', 'lat', 'lng', 'total_seat',
                  'total_staff', 'online_booking_appointment', 'salon_type', 'availability_status', 'address']

    def get_manager_name(self, obj):
        if not obj.manager_id or not obj.manager:
            return None
        return obj.manager.name or obj.manager.username or None


class SalarySerializer(serializers.ModelSerializer):
    date_issued = serializers.SerializerMethodField()
    total_salary = serializers.SerializerMethodField()
    product_incentive_amount = serializers.SerializerMethodField()
    service_incentive_amount = serializers.SerializerMethodField()

    class Meta:
        model = Salary
        fields = ['id', 'employee', 'basic', 'total_salary', 'date_issued', 'month',
                  'service_incentive_amount', 'product_incentive_amount', 'deduction', 'paid', 'note']

    def get_date_issued(self, obj):
        try:
            # Adjust the format string to use a space (' ') as the separator and include the time zone offset
            formatted_date = datetime.datetime.strptime(
                str(obj.date_issued), '%Y-%m-%d %H:%M:%S.%f%z')
        except Exception:
            # Adjust the format string to use a space (' ') as the separator and include the time zone offset
            formatted_date = datetime.datetime.strptime(
                str(obj.date_issued), '%Y-%m-%d %H:%M:%S%z')

        # Define the UTC timezone
        utc_timezone = pytz.timezone('UTC')

        # Convert the datetime object to UTC
        utc_date = formatted_date.astimezone(utc_timezone)

        # Define the Indian Standard Time (IST) timezone
        ist_timezone = pytz.timezone('Asia/Kolkata')

        # Convert the datetime object to IST
        ist_date = utc_date.astimezone(ist_timezone)

        formatted_datetime = ist_date.strftime('%Y-%m-%d %H:%M:%S')

        return formatted_datetime

    def get_total_salary(self, obj):
        total_salary = obj.basic + obj.service_incentive_amount + \
            obj.product_incentive_amount - \
            obj.deduction
        salary = Salary.objects.get(employee=obj.employee, month=obj.month)
        salary.total_salary = total_salary
        salary.save()
        return int(total_salary)

    def get_product_incentive_amount(self, obj):
        total_product_incentive = 0
        employee_staff = None
        pi_count = 0
        for appointment in Appointment.objects.filter(category='Product'):
            staff_count = appointment.staff_assigned.count()
            for staff in appointment.staff_assigned.filter(id=obj.employee.id):
                employee_staff = Employee.objects.get(id=staff.id,status="Active")
                total_product_incentive += ((employee_staff.product_incentive/staff_count)/100 * (
                    int(appointment.totalPrice) - int(appointment.discount_price)))
                pi_count += 1
                print(pi_count, appointment.totalPrice)
        if pi_count == 0:
            return int(total_product_incentive)
        salary = Salary.objects.get(employee=employee_staff, month=obj.month)
        salary.product_incentive_amount = total_product_incentive
        salary.save()

        return int(total_product_incentive)

    def get_service_incentive_amount(self, obj):
        total_service_incentive = 0
        si_count = 0
        for appointment in Appointment.objects.filter(category='Service'):
            staff_count = appointment.staff_assigned.count()
            for staff in appointment.staff_assigned.filter(id=obj.employee.id):
                employee_staff = Employee.objects.get(id=staff.id,status="Active")
                total_service_incentive += ((employee_staff.service_incentive/staff_count)/100 * (
                    int(appointment.totalPrice) - int(appointment.discount_price)))
                si_count += 1
                print(si_count, appointment.total_service_incentive)
        if si_count == 0:
            return int(total_service_incentive)
        salary = Salary.objects.get(employee=employee_staff, month=obj.month)
        salary.service_incentive_amount = total_service_incentive
        salary.save()

        return int(total_service_incentive)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = '__all__'


class EmployeeSerializer(serializers.ModelSerializer):
    user = UserSerializer(many=False)
    customer_name = serializers.CharField(source='user.name')
    first_name = serializers.CharField(source='user.first_name')
    last_name = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')
    mobile = serializers.CharField(source='user.mobile')

    class Meta:
        model = Employee
        fields = ['id', 'user', 'first_name', 'last_name', 'customer_name', 'email', 'mobile',
                  'employee_type', 'status', 'created', 'product_incentive', 'service_incentive', 'base_salary']


class AppointmentSerializer(serializers.ModelSerializer):
    booking_date = serializers.CharField(source='date')
    price = serializers.CharField(source='totalPrice')
    payment_status = serializers.SerializerMethodField()
    staff_assigned = EmployeeSerializer(many=True)
    service = ServiceSerializer(many=True)
    product = ProductSerializer(many=True)
    category = serializers.CharField()
    user = UserSerializer(many=False)
    customer_name = serializers.CharField(source='user.name')
    customer_id = serializers.SerializerMethodField()
    invoice_id = serializers.SerializerMethodField()
    salon = SalonDetailsSerializer(many=False)

    class Meta:
        model = Appointment
        fields = ['id', 'salon', 'order_id', 'customer_name', 'customer_id', 'user', 'booking_date', 'start_time', 'end_time', 'price', 'booking_status',
                  'payment_status', 'id', 'mode_of_payment', 'createdAt', 'staff_assigned', 'service', 'product', 'category', 'discount_price', 'booking_platform', 'invoice_id']

    def get_invoice_id(self, obj):
        all_invoice = Invoice.objects.all()
        for inv in all_invoice:
            if obj in inv.appointment.all():
                return inv.id
            

    def get_payment_status(self, obj):
        if obj.isPaid == True:
            return "Paid"
        else:
            return 'Not Paid'

    def get_customer_id(self, obj):
        return f"{obj.user.id}"




class CustomerSerializer(serializers.ModelSerializer):
    first_name = serializers.SerializerMethodField()
    last_name = serializers.SerializerMethodField()
    customer_name = serializers.SerializerMethodField()
    name = serializers.CharField()
    customer_id = serializers.SerializerMethodField()
    email = serializers.CharField()
    gender = serializers.CharField(source='user.gender')
    mobile = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='user.date_joined')

    def get_mobile(self, obj):
        mobile_numbers = obj.mobile_number.all()
        if mobile_numbers.exists():
            return mobile_numbers.first().mobile
        else:
            return None

    def get_customer_id(self, obj):
        return obj.id

    def get_first_name(self, obj):
        return f"{obj.first_name}"

    def get_last_name(self, obj):
        return f"{obj.last_name}"

    def get_customer_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"

    def get_gender(self, obj):
        user = obj.user
        gender = user.gender
        return f"{gender}"

    class Meta:
        model = Customer
        fields = ['id', 'customer_id', 'name', 'first_name', 'last_name',
                  'customer_name', 'email', 'mobile', 'status', 'date_joined', 'gender']


class JobSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = '__all__'


class TodoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Todo
        fields = ('id', 'name', 'created_on', 'updated_on', 'status')


class AccessKeyRemoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessKeyRemove
        fields = '__all__'


class AllowedPathSerializer(serializers.ModelSerializer):
    class Meta:
        model = AllowedPath
        fields = '__all__'


class SubscriptionAccessKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionAccessKeyAssociation
        fields = '__all__'

class ReviewSerializer(serializers.ModelSerializer):
    service = ServiceSerializer(many=True)
    service_name = serializers.SerializerMethodField()

    def get_service_name(self, obj):
        service = obj.service.all()
        service_name = []
        for serv in service:
            service_name.append(serv.name)
        return f"{service_name}"
    
    class Meta:
        model = Review
        fields = '__all__'

class KanbanItemSerializer(serializers.ModelSerializer):
    assign = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"{obj.id}"

    def get_assign(self, obj):
        return f"{obj.assign.name}"

    class Meta:
        model = KanbanItem
        fields = ('id', 'assign', 'attachments', 'commentIds',
                  'description', 'priority', 'dueDate', 'title', 'status', 'image')


class KanbanProfileSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"{obj.id}"

    def get_name(self, obj):
        user = getattr(obj, 'user', None)
        if user is None:
            return 'Unassigned'
        display = (getattr(user, 'name', None) or '').strip()
        if not display:
            display = (user.get_full_name() or '').strip()
        if not display:
            display = user.username or f'User {user.id}'
        return display

    class Meta:
        model = KanbanProfile
        fields = ('id', 'name')


class KanbanCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanComment
        fields = '__all__'


class KanbanColumnSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    def get_id(self, obj):
        return f"{obj.id}"

    class Meta:
        model = KanbanColumn
        fields = ('id', 'title', 'itemIds')

class MembershipSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.name')
    customer_id = serializers.SerializerMethodField()


    class Meta:
        model = Membership
        fields = '__all__'

    def get_customer_name(self, obj):
        # Assuming `customer` is the ForeignKey to Customer model
        return obj.customer.name  # Adjust the attribute name as per your Customer model

    def get_customer_id(self, obj):
        # Assuming `customer` is the ForeignKey to Customer model
        return obj.customer.id  # Adjust the attribute name as per your Customer model

class CouponCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CouponCode
        fields = '__all__'


class UsedCouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsedCoupon
        fields = '__all__'


class MessageSerializer(serializers.Serializer):
    class Meta:
        model = Messaging
        fields = '__all__'


class SubscriptionTypeSerializer(serializers.Serializer):
    class Meta:
        model = SubscriptionType
        fields = '__all__'


class InvoiceSerializer(serializers.ModelSerializer):
    appointment = AppointmentSerializer(many=True)
    customer_name = serializers.SerializerMethodField()
    coupon_code = CouponCodeSerializer()
    membership = MembershipSerializer()
    price_cut_by_membership = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = ['id', 'total', 'mode_of_payment', 'customer_name', 'due_payment', 'date_created',
                'status', 'appointment', 'actual_amount', 'discount_added', 'transaction', 'tax_added',
                'coupon_code', 'membership', 'price_cut_by_membership', 'discount_percentage', 'tax_percentage', 'price_cut_by_coupon_code']

    def get_customer_name(self, obj):
        all_appointments = obj.appointment.all()
        if len(all_appointments) != 0:
            appointment = all_appointments[0]
            user = appointment.user
            customer = Customer.objects.get(user=user)
            return f"{customer.name}"

    def get_price_cut_by_membership(self, obj):
        if obj.membership:
            membership_percentage = obj.membership.discount_percent
            price_cut_by_membership = int(membership_percentage / 100 * obj.total)
        else:
            appointment = obj.appointment.first()
            branch = appointment.branch
            user = appointment.user
            customer = Customer.objects.get(user=user)
            try:
                membership = Membership.objects.get(customer=customer, branch=branch)
                membership_percentage = membership.discount_percent
                price_cut_by_membership = int(membership_percentage / 100 * obj.total)
            except Membership.DoesNotExist:
                price_cut_by_membership = 0
        return price_cut_by_membership