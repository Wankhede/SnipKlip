from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.fields import BLANK_CHOICE_DASH
# from django.db.models import JSONField
from django.utils import timezone
from datetime import datetime
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext as _
from jsonschema import ValidationError
from backend.manager import LeaveManager
from jsonfield import JSONField
from django.contrib.auth.models import Group
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType

USER_STATUS = (
    (0, 'Inactive'),
    (1, 'Active'),
)

STATUS = (
    ('Inactive', 'Inactive'),
    ('Active', 'Active'),
)

PRODUCT_STATUS = (
    ('Out of Stock', 'Out of Stock'),
    ('In Stock', 'In Stock'),
)

SUBSCRIPTION_TYPE = (
    (1, 'Free'),
    (2, 'Premium'),
)


SERVICE_OFFERED_LIST = ('Bikini Line - Sugar Wax', 'Nose Waxing', ' Full Body - Liposoluble', ' Brazillian - Beed Wax', ' Brazillian - Sugar Wax', ' Bikini Line - Liposoluble', 'Stomach - Liposoluble', 'Front - Liposoluble', 'Back (Full) - Liposoluble', 'Back (Half) - Liposoluble', 'Legs (Half) - Liposoluble', 'Full Face - Beed', 'Ear - Beed', 'Any Three (Face) - Beed Wax', 'Side-Locks - Beed Wax', 'Jawline - Beed Wax', 'Forehead - Beed Wax', 'UnderArms - Beed Wax', 'Neck - Beed Wax', 'Chin - Beed Wax', 'Upper-Lip - Beed Wax', 'Stomach - Sugar Wax', 'Front - Sugar Wax', 'Back (Full) - Sugar Wax', 'Back (Half) - Sugar Wax', 'Legs (Full) - Sugar Wax', 'Legs (Half) - Sugar Wax', 'Arms (Full) - Sugar Wax', 'UnderArms - Sugar Wax', 'Legs (Full) - Liposoluble', 'Arms (Full) - Liposoluble', 'UnderArms - Liposoluble', 'Nail Paint - Feet', 'Nail Paint - Hands', 'Cut File Polish - Feet', 'Cut File Polish - Hands', 'Luxe Manicure', 'Luxe Pedicure', 'Oriental Spa Manicure', 'Oriental Spa Pedicure', 'Manicure - Classic', 'Pedicure - Classic', 'Heal Peel', 'Cut - File', 'Premium Pedicure', 'Premium Manicure', 'Foot Massage', 'Prelightening - upto neck', 'Pre-lightening Below Shoulder', 'Split Ends Removal and Wash', 'Fringe/Bangs Cut', 'SKP Fiber Clinix - Men', 'SKP Fiber Clinix - Upto Waist', 'SKP Fiber Clinix - Below Shoulder', 'SKP Fiber Clinix - Upto Shoulder', 'SKP Fiber Clinix - Upto Neck', 'Scalp Treatment', 'Vivids - Creative', 'Head Massage - Female', 'Head Massage - Male', 'Male Haircut - Style Director', 'Female Haircut - Style Director', 'VIVIDS - Men', 'Cysteine / Keratin - Upto Waist', 'Cysteine / Keratin - Below Shoulder', 'Cysteine / Keratin - Upto Shoulder', 'Cysteine / Keratin - Upto Neck', 'Cysteine / Keratin - Fringe', 'Smoothning / Straightening - Upto Waist', 'Smoothning / Straightening - Below Shoulder', 'Smoothning / Straightening - Upto Shoulder', 'Smoothning / Straightening - Upto Neck', 'Smoothning / Straightening - Fringe', 'Power Mix Upto Waist', 'Power Mix - Below Shoulder', 'Power Mix - Male', 'Power Mix - Upto Shoulder', 'Power Mix - Upto Neck', 'Hair Spa Upto Waist', 'Hair Spa Below Shoulder', 'Hair Spa Upto Shoulder', 'Hair Spa Upto Neck',
                        'Hair Spa Men', 'Male Prelightening', 'Male Highlights', 'Side Locks & Moustache Color', 'Beard Color', 'Male - Color (Upto Neck)', 'Male - Color (Standerd Length)', 'Male - Wash & Style', 'Male - Shampoo & Conditioning', 'Shaving', 'Beard Crafting', 'Smart Bond - Upto Waist', 'Smart Bond - Below Shoulder', 'Smart Bond - Upto Shoulder', 'Smart Bond - Upto Neck', 'VIVIDS - Ombre / Balayage - Below Shoulder', 'VIVIDS - Special Effect (4-5 Foils)', 'VIVIDS - Per Streak', 'Highlight - Upto Waist', 'Highlight - Below Shoulder', 'Highlight - Upto Shoulder', 'Highlight - Upto Neck', 'Global Color - Upto Waist', 'Global Color - Below Shoulder', 'Global Color - Upto Shoulder', 'Global Color - Upto Neck', 'Streak - Per Foil', 'Root Touch up - 4 inch', 'Root Touch up - 2 inch', 'Ironing / Tongs - Below Shoulder', 'Ironing / Tongs - Upto Shoulder', 'Blowdry - Upto Waist', 'Blowdry - Below Shhoulder', 'Shampoo & Blowdry - Upto Waist', 'Shampoo & Blowdry - Below Shoulder', 'Shampoo & Conditioning - Upto Waist', 'Shampoo & Conditioning - Below Shoulder', 'Hair Cut - Female', 'Hair Cut - Male', 'Color Correction - Below Shoulder', 'K18 Upto Shoulder', 'K18 Below Shoulder', 'K18 Upto Waist', 'Color Application - Male', 'Metal DX - Upto Shoulder', 'Metal DX - Below Shoulder', 'Metal DX - Upto Waist', 'Prelightening - Upto Shoulder', 'Prelifting - Any Length', 'TEST', 'Head Shaving', 'Advance Skin Treatment - Men', 'Advance Skin Treatment - Women', 'Advance Facial - Women', 'Advance Facial - Men', 'Basic facial - Women', 'Basic facial - Men', 'Clean Up', 'Full Body - DeTan', 'Back - DeTan', 'Full Legs - DeTan', 'Full Hands - DeTan', 'Face - DeTan', 'Full Body - Bleach', 'Front - Bleach', 'Back - Bleach', 'Feet - Bleach', 'Legs (Half) - Bleach', 'Legs (Full) - Bleach', 'Arms (Full) - Bleach', 'Arms (Half) - Bleach', 'Face Bleach (Oxy Gold)', 'Face Bleach (Oxy)', 'UnderArms - Bleach', 'Back of Palms - Bleach', 'Upper-Lip - Bleach', 'Any Five (Face) - Threading', 'Side-Locks Threading', 'Jawline Threading', 'Forehead Threading', 'Neck Threading', 'Chin Threading', 'Nose Threading', 'Lower Lip Threading', 'Upper-Lip Threading', 'Eyebrow Threading', 'Any Three (Face) - Threading')
SERVICE_OFFERED = []
for i in range(0, len(SERVICE_OFFERED_LIST)):
    SERVICE_OFFERED.append(
        ((SERVICE_OFFERED_LIST[i], (SERVICE_OFFERED_LIST[i]))))

ALTERTS_TO = (
    (0, 'NO'),
    (2, 'SMS'),
    (1, 'EMAIL'),
    (3, 'EMAIL&SMS'),
)

SALON_TYPE = (
    ('MEN', 'MEN'),
    ('WOMEN', 'WOMEN'),
    ('UNISEX', 'UNISEX'),
)

ONLINE_APPOINTMENT = (
    ('YES', 'YES'),
    ('NO', 'NO'),
)

LANGUAGE = (
    ('hi', 'HINDI'),
    ('en', 'ENGLISH'),
    ('mr', 'MARATHI')
)


class UserType(models.Model):
    name = models.CharField(max_length=100, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class User(AbstractUser):
    GENDER_CHOICES = (
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    )
    # email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    company_name = models.CharField(max_length=50, null=True, blank=True)
    user_type = models.ForeignKey(
        'UserType', on_delete=models.CASCADE, null=True, blank=True)
    ratings = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True)
    user_status = models.IntegerField(
        choices=USER_STATUS, blank=True, null=True)
    mobile = models.CharField(max_length=20, null=True, blank=True)
    subscription_type = models.IntegerField(
        choices=SUBSCRIPTION_TYPE, blank=True, null=True)
    send_alerts_to = models.IntegerField(
        choices=ALTERTS_TO, blank=True, null=True)
    address = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=50, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    dob = models.DateField(null=True, blank=True, default=None)
    image = models.ImageField(
        upload_to="images/profile_photo/", default=None, null=True, blank=True)
    language = models.CharField(
        max_length=20, choices=LANGUAGE, blank=True, null=True)
    instagram_profile = models.CharField(
        max_length=2000, default=None, blank=True, null=True)
    gender = models.CharField(blank=True, null=True,
                              choices=GENDER_CHOICES, max_length=100)
    registration_id = models.CharField(
        max_length=255, default="", null=True, blank=True)

    def __str__(self):
        return self.username

    def get_name(self):
        return f"{self.first_name} {self.last_name}"

    # to save the data
    def register(self):
        self.save()

    @staticmethod
    def get_customer_by_email(email):
        try:
            return User.objects.get(email=email)
        except:
            return False

    def isExists(self):
        if User.objects.filter(email=self.email):
            return True

        return False


class SalonDetails(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    reg_no = models.CharField(max_length=255)
    contact_no = models.CharField(max_length=255)
    owner_name = models.CharField(max_length=255)
    owner_email = models.CharField(max_length=255)
    logo = models.ImageField(null=True, blank=True,
                             default=None, upload_to="logo/")
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return self.name


class Branch_Images(models.Model):
    branch_id = models.IntegerField(null=True, blank=True, default=None)
    branch_image = models.ImageField(
        null=True, blank=True, default=None, upload_to="images/")

    def __str__(self):
        return str(self.branch_id) + "----->" + str(self.branch_image)
    


class Branch(models.Model):
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, null=True)
    branch_name = models.CharField(
        max_length=1000, default="", null=True, blank=True)
    owner_contact_no = models.CharField(max_length=255)
    address = models.CharField(max_length=400)
    locality = models.CharField(max_length=400)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    pincode = models.CharField(max_length=6)
    exp_desc = models.TextField(null=True, blank=True)
    availability_status = models.BooleanField(default=True)
    lat = models.FloatField(null=True, blank=True)
    lng = models.FloatField(null=True, blank=True)
    image = models.ManyToManyField(Branch_Images, blank=True)
    manager = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='manager', null=True, default=None, blank=True)
    total_seat = models.IntegerField(null=True, blank=True)
    total_staff = models.IntegerField(null=True, blank=True)
    online_booking_appointment = models.CharField(
        max_length=100, choices=ONLINE_APPOINTMENT, default="MEN", null=True, blank=True)
    salon_type = models.CharField(
        max_length=100, choices=SALON_TYPE, default="MEN", null=True, blank=True)

    def __str__(self):
        return str(self.branch_name)
    


class Branch_Time_Schedule(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=None, null=False, blank=False)
    is_open = models.BooleanField(default=True)

    sunday_start_time = models.TimeField(default=None)
    sunday_end_time = models.TimeField(default=None)

    monday_start_time = models.TimeField(default=None)
    monday_end_time = models.TimeField(default=None)

    tuesday_start_time = models.TimeField(default=None)
    tuesday_end_time = models.TimeField(default=None)

    wednesday_start_time = models.TimeField(default=None)
    wednesday_end_time = models.TimeField(default=None)

    thursday_start_time = models.TimeField(default=None)
    thursday_end_time = models.TimeField(default=None)

    friday_start_time = models.TimeField(default=None)
    friday_end_time = models.TimeField(default=None)

    saturday_start_time = models.TimeField(default=None)
    saturday_end_time = models.TimeField(default=None)

    def __str__(self):
        return str(self.branch) + " ------> " + str(self.is_open)

class Customer(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)
    mobile_number = models.ManyToManyField(
        'BranchCustomerMobile', default=None, blank=True, related_name="MOBILE_NUMBER_CUSTOMER_DATA")
    status = models.CharField(max_length=100, choices=STATUS, default="Active")

    def __str__(self):
        return str(self.name)


class BranchCustomerMobile(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    customer_user = models.ForeignKey(Customer, on_delete=models.CASCADE,
                                      default=None, null=True, blank=True, related_name="CUSTOMER_DATA")
    mobile = models.CharField(max_length=255, null=True, blank=True)
    note = models.CharField(max_length=255, default="", null=True, blank=True)

    def __str__(self):
        return str(self.branch) + " - " + str(self.customer_user.name) + " - " + str(self.mobile)


class Service(models.Model):
    user = models.ForeignKey(SalonDetails, on_delete=models.CASCADE, null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    name = models.CharField(
        max_length=100, choices=SERVICE_OFFERED, default=None, null=True, blank=True)
    image = models.ImageField(null=True, blank=True,
                              upload_to="images/service/")
    brand = models.CharField(max_length=200, null=True, blank=True)
    category = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    rating = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, null=True, blank=True)
    numReviews = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    id = models.AutoField(primary_key=True, editable=False)
    time_for_each_service = models.IntegerField(
        null=True, blank=True, default=0)

    def __str__(self):
        return str(self.name)

    @staticmethod
    def get_service_by_id(ids):
        return Service.objects.filter(id__in=ids)

    @staticmethod
    def get_all_service():
        return Service.objects.all()

    @staticmethod
    def get_all_service_by_categoryid(category_id):
        if category_id:
            return Service.objects.filter(category=category_id)
        else:
            return Service.get_all_service()


class Service_CSV(models.Model):
    file = models.FileField(upload_to="service_csv/",
                            default=None, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                               related_name="Branch_Name", default=None, null=True, blank=True)

    def __str__(self):
        return str(self.file) + "----->" + "Uploaded By" + " " + str(self.branch)


class Data_CSV(models.Model):
    file = models.FileField(upload_to="data_csv/",
                            default=None, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE,
                               related_name="Branch", default=None, null=True, blank=True)

    def __str__(self):
        return str(self.file) + "----->" + "Uploaded By Admin, of Branch:-" + str(self.branch)


class Payment(models.Model):
    stripe_charge_id = models.CharField(max_length=50)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.name


class DiscountDetails(models.Model):
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, to_field='id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    service = models.ForeignKey(
        Service, on_delete=models.CASCADE, to_field='id')
    offer_percent = models.PositiveIntegerField(default=0)
    from_date = models.DateTimeField(auto_now=False, null=True)
    to_date = models.DateTimeField(auto_now=False, null=True)
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.offer_percent) + "% " + "Discount At" + " " + str(self.salon)


class OrderItem(models.Model):
    service = models.ForeignKey(Service, on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=200, null=True, blank=True)
    qty = models.IntegerField(null=True, blank=True, default=0)
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.CharField(max_length=200, null=True, blank=True)
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.name)


class Employee(models.Model):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
    NOT_KNOWN = 'Not Known'

    GENDER = (
        (MALE, 'Male'),
        (FEMALE, 'Female'),
        (OTHER, 'Other'),
        (NOT_KNOWN, 'Not Known'),
    )

    MR = 'Mr'
    MRS = 'Mrs'
    MSS = 'Mss'
    DR = 'Dr'
    SIR = 'Sir'
    MADAM = 'Madam'

    TITLE = (
        (MR, 'Mr'),
        (MRS, 'Mrs'),
        (MSS, 'Mss'),
        (DR, 'Dr'),
        (SIR, 'Sir'),
        (MADAM, 'Madam'),
    )

    FULL_TIME = 'Full-Time'
    PART_TIME = 'Part-Time'
    CONTRACT = 'Contract'
    INTERN = 'Intern'

    EMPLOYEETYPE = (
        ('Manager', 'Manager'),
        ('Staff', 'Staff'),
    )

    STATUS = (
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('On Leave', 'On Leave'),
        ('Left', 'Left')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    base_salary = models.IntegerField(default=0, null=True, blank=True)
    image = models.FileField(upload_to='profiles', blank=True, null=True,
                             help_text='upload image size less than 2.0MB')  # work on path username-date/image
    branch = models.ForeignKey(
        Branch, on_delete=models.SET_NULL, null=True, default=None)
    start_date = models.DateField(default=None, blank=False, null=True)
    end_date = models.DateField(default=None, blank=True, null=True)
    employee_type = models.CharField(
        max_length=15, default=None, choices=EMPLOYEETYPE, blank=False, null=True)
    status = models.CharField(max_length=100, choices=STATUS, default="Active")
    created = models.DateTimeField(auto_now=True, null=True)
    updated = models.DateTimeField(auto_now=False, null=True)
    service_incentive = models.IntegerField(default=0, null=True, blank=True)
    product_incentive = models.IntegerField(default=0, null=True, blank=True)

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        ordering = ['-created']

    def __str__(self):
        return str(self.user)


class Product(models.Model):
    code = models.CharField(max_length=100, blank=True, null=True)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, default=None, blank=True, null=True)
    sku = models.CharField(max_length=1000, blank=True, null=True, default="")
    name = models.CharField(max_length=250, blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True, default=None)
    weight_unit = models.CharField(choices=(('KG', 'KG'), ('Gram', 'Gram'), (
        'ML', 'ML'), ('Gram', 'Gram'),), max_length=10, blank=True, null=True, default=None)
    description = models.TextField()
    price = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    currency = models.CharField(
        choices=(('INR', 'INR'),), max_length=10, blank=True, null=True, default=None)
    availablity = models.CharField(max_length=100, choices=PRODUCT_STATUS, default="In Stock")
    vendor = models.CharField(
        max_length=1000, blank=True, null=True, default="")
    category = models.CharField(choices=(('Shampoos and Conditioners', 'Shampoos and Conditioners'), ('Hairstyling Products', 'Hairstyling Products'), ('Hair Removal Products',
                                'Hair Removal Products'), ('Manicures and Pedicure Products and Tools', 'Manicures and Pedicure Products and Tools')), max_length=100, blank=True, null=True, default=None)
    collection = models.CharField(choices=(('Men', 'Men'), ('Female', 'Female'), ('Unisex', 'Unisex'), (
        'Others', 'Others'), ('All', 'All'),), max_length=40, blank=True, null=True, default=None)
    tag = models.CharField(max_length=1000, blank=True, null=True, default="")
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(
        upload_to="images/product_images/", default=None, null=True, blank=True)
    id = models.AutoField(primary_key=True, editable=False)

    objects = models.Manager()

    def __str__(self):
        return str(self.name)


class Appointment(models.Model):
    BOOKING_STATUS = (
        ('Availed', 'Availed'),
        ('Booked', 'Booked'),
        ('Cancelled by user', 'Cancelled by user'),
        ('Cancelled by salon', 'Cancelled by salon'),
        ('Pending', 'Pending')
    )
    DAY = (
        ('Sunday', "Sunday"),
        ('Monday', "Monday"),
        ('Tuesday', "Tuesday"),
        ('Wednesday', "Wednesday"),
        ('Thursday', "Thursday"),
        ('Friday', "Friday"),
        ('Saturday', "Saturday"),
    )
    PAYMENT_METHOD = (
        ('CASH', 'CASH'),
        ('UPI', 'UPI'),
        ('CARD', 'CARD'),
        ('OTHERS', 'OTHERS')
    )
    BOOKING_PLATFORM = (
        ('ONLINE', 'ONLINE'),
        ('WALK IN', 'WALK IN'),
        ('BOOK APPOINTMENT', 'BOOK APPOINTMENT')
    )
    CATEGORY = (('Service', 'Service'),
                ('Product', 'Product')
                )
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    service = models.ManyToManyField(Service)
    product = models.ManyToManyField(Product,blank=True)
    category = models.CharField(max_length=7, default="Service", choices=CATEGORY)
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, to_field='id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, to_field='id')
    mode_of_payment = models.CharField(
        max_length=20, default="", null=True, blank=True, choices=PAYMENT_METHOD)
    totalPrice = models.DecimalField(
        max_digits=12, decimal_places=2, null=True, blank=True)
    order_id = models.CharField(
        max_length=300, default="", null=True, blank=True)
    isPaid = models.BooleanField(default=False)
    date = models.DateField(auto_now_add=False, null=True, blank=True)
    start_time = models.TimeField(auto_now_add=False, null=True, blank=True)
    end_time = models.TimeField(auto_now_add=False, null=True, blank=True)
    discount_price = models.FloatField(default=0, null=True, blank=True)
    paidAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    createdAt = models.DateTimeField(auto_now_add=False, null=True, blank=True)
    booking_status = models.CharField(max_length=200, choices=BOOKING_STATUS)
    booking_platform = models.CharField(
        max_length=200, choices=BOOKING_PLATFORM)
    staff_assigned = models.ManyToManyField(Employee)
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.order_id)

    def placeOrder(self):
        self.save()

    # def save(self, *args, **kwargs):
    #     # Extract the time component from the datetime
    #     if self.datetime_field:
    #         self.time_field = self.datetime_field.time()
    #     super(Appointment, self).save(*args, **kwargs)

    @staticmethod
    def get_orders_by_customer(customer_id):
        return Appointment.objects.filter(customer=customer_id).order_by('-date')



class Membership(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=None)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, default=None, blank=True, null=False)
    minimum_value_amount = models.IntegerField(default=0)
    discount_percent = models.IntegerField(default=0)
    expiry_date = models.DateTimeField(blank=True, null=True)
    no_of_time_used = models.IntegerField(default=0)
    used_in_appointment = models.ManyToManyField(Appointment)
    status = models.CharField(max_length=100, choices=STATUS, default="Active")

    def __str__(self):
        return str(self.customer.name)

class CouponCode(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, default=None)
    coupon_code = models.CharField(max_length=50, null=True, blank=True)
    minimum_value_amount = models.IntegerField(default=0)
    discount_percent = models.IntegerField(default=0)
    expiry_date = models.DateTimeField(blank=True, null=True)
    available_count = models.IntegerField(default=0)
    status = models.CharField(max_length=100, choices=STATUS, default="Active")

    def __str__(self):
        return self.coupon_code
    

class Invoice(models.Model):
    INVOICE_SEND_METHOD = (
        ('WHATSAPP', 'WHATSAPP'),
        ('EMAIL', 'EMAIL'),
        ('SMS', 'SMS')
    )
    PAYMENT_METHOD = (
        ('CASH', 'CASH'),
        ('UPI', 'UPI'),
        ('CARD', 'CARD'),
        ('OTHERS', 'OTHERS')
    )
    STATUS = (
        ('Paid', 'Paid'),
        ('Unpaid', 'Unpaid'),
        ('Cancelled', 'Cancelled'),
    )
    CATEGORY = (
        ('SERVICE', 'SERVICE'),
        ('PRODUCT', 'PRODUCT'),
        ('BOTH', 'BOTH')
    )
    send_invoice_on = models.CharField(
        choices=INVOICE_SEND_METHOD, default="", blank=True, null=True, max_length=100)
    transaction = models.CharField(max_length=250)
    appointment = models.ManyToManyField(Appointment)
    mode_of_payment = models.CharField(
        choices=PAYMENT_METHOD, default="", blank=True, null=True, max_length=100)
    total = models.FloatField(default=0)
    actual_amount = models.FloatField(default=0, null=True)
    discount_percentage = models.IntegerField(default=0,null=True)
    discount_added = models.FloatField(default=0, null=True)
    tax_percentage = models.IntegerField(default=0,null=True)
    tax_added = models.FloatField(default=0, null=True)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True, null=True)
    due_payment = models.IntegerField(default=0, null=True, blank=True)
    status = models.CharField(choices=STATUS, default="Paid", blank=True, null=True, max_length=100)
    price_cut_by_coupon_code = models.IntegerField(default=0, null=True, blank=True)
    coupon_code = models.ForeignKey(CouponCode,on_delete=models.CASCADE, null=True, blank=True, default=None)
    price_cut_by_membership = models.IntegerField(default=0, null=True, blank=True)
    membership = models.ForeignKey(Membership,on_delete=models.CASCADE, null=True, blank=True, default=None)

    def __str__(self):
        return self.transaction 


def validate_rating(value):
    if value < 0 or value > 5:
        raise ValidationError('Rating must be between 0 and 5')

class Review(models.Model):
    invoice = models.ForeignKey(
        Invoice, on_delete=models.CASCADE, null=True, default=None)
    service = models.ManyToManyField(Service, default=None)
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True)
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, to_field='id')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    rating = models.PositiveIntegerField(null=False, blank=False, default=0,validators=[validate_rating])
    comment = models.TextField(null=False, blank=False, default="")
    createdAt = models.DateTimeField(auto_now_add=True)
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return str(self.rating)


class Refund(models.Model):
    order = models.ForeignKey(
        Appointment, on_delete=models.CASCADE, default=None)
    reason = models.TextField()
    accepted = models.BooleanField(default=False)
    email = models.EmailField()
    id = models.AutoField(primary_key=True, editable=False)

    def __str__(self):
        return f"{self.pk}"



class UsedCoupon(models.Model):
    coupon = models.ForeignKey(
        'CouponCode', on_delete=models.CASCADE, null=True, blank=True, default=None)
    user = models.ForeignKey(
        'User', on_delete=models.CASCADE, null=True, blank=True)
    used_date = models.DateTimeField()

    def __str__(self):
        return self.coupon.coupon_code


class Subscription(models.Model):
    TIME_PERIOD = (
        ('MONTHLY', 'MONTHLY'),
        ('YEARLY', 'YEARLY'),
    )
    SUBSCRIPTION = (
        ('STANDARD', 'STANDARD'),
        ('STANDARD PLUS', 'STANDARD PLUS'),
        ('PREMIUM', 'PREMIUM')
    )
    name_of_subscription = models.CharField(
        choices=SUBSCRIPTION, blank=True, null=True, max_length=1000)
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, default=None, null=True, blank=True)
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    credit_balance = models.IntegerField(default=0)
    type = models.CharField(choices=TIME_PERIOD,
                            blank=True, null=True, max_length=1000)
    paid = models.BooleanField(default=False, null=True, blank=True)
    order_id = models.CharField(
        default="", null=True, blank=True, max_length=10000)

    def __str__(self):
        return self.user.first_name


class ProductItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.FloatField(default=0)
    type = models.CharField(max_length=2, choices=(
        ('1', 'Stock-in'), ('2', 'Stock-Out')), default=1)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    id = models.AutoField(primary_key=True, editable=False)

    objects = models.Manager()

    def __str__(self):
        return self.product.code + ' - ' + self.product.name


class ProductInvoice(models.Model):
    transaction = models.CharField(max_length=250)
    customer = models.CharField(max_length=250)
    total = models.FloatField(default=0)
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    id = models.AutoField(primary_key=True, editable=False)
    objects = models.Manager()

    def __str__(self):
        return self.transaction


class ProductInvoiceItem(models.Model):
    invoice = models.ForeignKey(ProductInvoice, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    stock = models.ForeignKey(
        ProductItem, on_delete=models.CASCADE, blank=True, null=True)
    price = models.FloatField(default=0)
    quantity = models.FloatField(default=0)
    status = models.BooleanField(default=False)
    rate = models.FloatField(default=0)
    tax = models.FloatField(default=0)
    due_date = models.DateTimeField(auto_now=True)
    id = models.AutoField(primary_key=True, editable=False)

    objects = models.Manager()

    def __str__(self):
        return self.invoice.transaction


class Leave(models.Model):
    SICK = 'sick'
    CASUAL = 'casual'
    EMERGENCY = 'emergency'
    STUDY = 'study'
    MATERNITY = 'maternity'
    BEREAVEMENT = 'bereavement'
    QUARANTINE = 'quarantine'
    COMPENSATORY = 'compensatory'
    SABBATICAL = 'sabbatical'

    LEAVE_TYPE = (
        (SICK, 'Sick Leave'),
        (CASUAL, 'Casual Leave'),
        (EMERGENCY, 'Emergency Leave'),
        (STUDY, 'Study Leave'),
        (MATERNITY, 'Maternity Leave'),
        (BEREAVEMENT, 'Bereavement Leave'),
        (QUARANTINE, 'Self Quarantine'),
        (COMPENSATORY, 'Compensatory Leave'),
        (SABBATICAL, 'Sabbatical Leave')
    )

    DAYS = 30
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    startdate = models.DateField(verbose_name=_(
        'Start Date'), help_text='leave start date is on ..', null=True, blank=False)
    enddate = models.DateField(verbose_name=_(
        'End Date'), help_text='coming back on ...', null=True, blank=False)
    leavetype = models.CharField(
        choices=LEAVE_TYPE, max_length=25, default=SICK, null=True, blank=False)
    reason = models.CharField(verbose_name=_('Reason for Leave'), max_length=255,
                              help_text='add additional information for leave', null=True, blank=True)
    defaultdays = models.PositiveIntegerField(verbose_name=_(
        'Leave days per year counter'), default=DAYS, null=True, blank=True)
    # pending,approved,rejected,cancelled
    status = models.CharField(max_length=12, default='pending')
    is_approved = models.BooleanField(default=False)  # hide
    updated = models.DateTimeField(auto_now=True, auto_now_add=False)
    created = models.DateTimeField(auto_now=False, auto_now_add=True)
    id = models.AutoField(primary_key=True, editable=False)
    objects = LeaveManager()

    class Meta:
        verbose_name = _('Leave')
        verbose_name_plural = _('Leaves')
        ordering = ['-created']  # recent objects

    def __str__(self):
        return ('{0} - {1}'.format(self.leavetype, self.user))

    @property
    def pretty_leave(self):
        '''
        i don't like the __str__ of leave object - this is a pretty one :-)
        '''
        leave = self.leavetype
        user = self.user
        employee = user.employee_set.first().get_full_name
        return ('{0} - {1}'.format(employee, leave))

    @property
    def leave_days(self):
        days_count = ''
        startdate = self.startdate
        enddate = self.enddate
        if startdate > enddate:
            return
        dates = (enddate - startdate)
        return dates.days

    @property
    def leave_approved(self):
        return self.is_approved == True

    @property
    def approve_leave(self):
        if not self.is_approved:
            self.is_approved = True
            self.status = 'approved'
            self.save()

    @property
    def unapprove_leave(self):
        if self.is_approved:
            self.is_approved = False
            self.status = 'pending'
            self.save()

    @property
    def leaves_cancel(self):
        if self.is_approved or not self.is_approved:
            self.is_approved = False
            self.status = 'cancelled'
            self.save()

    @property
    def reject_leave(self):
        if self.is_approved or not self.is_approved:
            self.is_approved = False
            self.status = 'rejected'
            self.save()

    @property
    def is_rejected(self):
        return self.status == 'rejected'


class Department(models.Model):
    name = models.CharField(max_length=125)
    description = models.CharField(max_length=125, null=True, blank=True)
    created = models.DateTimeField(
        verbose_name=_('Created'), auto_now_add=True)
    updated = models.DateTimeField(verbose_name=_('Updated'), auto_now=True)
    id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        verbose_name = _('Department')
        verbose_name_plural = _('Departments')
        ordering = ['name', 'created']

    def __str__(self):
        return self.name


class Salary(models.Model):
    MONTH = (
        ('JANUARY', 'JANUARY'),
        ('FEBRUARY', 'FEBRUARY'),
        ('MARCH', 'MARCH'),
        ('APRIL', 'APRIL'),
        ('MAY', 'MAY'),
        ('JUNE', 'JUNE'),
        ('JULY', 'JULY'),
        ('AUGUST', 'AUGUST'),
        ('SEPTEMBER', 'SEPTEMBER'),
        ('OCTOBER', 'OCTOBER'),
        ('NOVEMBER', 'NOVEMBER'),
        ('DECEMBER', 'DECEMBER'),
    )
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, default=1)
    basic = models.FloatField(default=0.0, null=True)
    total_salary = models.FloatField(default=0.0)
    date_issued = models.DateTimeField(default=None, null=True)
    month = models.CharField(
        choices=MONTH, max_length=1000, default="", blank=True, null=True)
    service_incentive_amount = models.FloatField(default=0.0)
    product_incentive_amount = models.FloatField(default=0.0)
    deduction = models.FloatField(default=0.0)
    paid = models.BooleanField(default=False, null=True)
    note = models.TextField(default=None, null=True)

    def __str__(self):
        return str(self.employee.user.first_name) + "------->" + "Total:- " + str(self.total_salary) + " " + str(self.month)


class Expense(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE)
    amount = models.FloatField(default=0.0, null=True, blank=True)
    description = models.TextField(default=None, null=True, blank=True)
    date = models.DateTimeField(auto_now=True, null=True)
    status = models.CharField(max_length=100, choices=STATUS, default="Active")

    def __str__(self):
        return str(self.amount)


class PaymentMode(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, default=None,
                                null=True, blank=True, related_name="payment_mode_invoice")
    upi = models.FloatField(default=0.0, null=True, blank=True)
    card = models.FloatField(default=0.0, null=True, blank=True)
    cash = models.FloatField(default=0.0, null=True, blank=True)
    other = models.FloatField(default=0.0, null=True, blank=True)

    def __str__(self):
        return f"UPI:-{self.upi} `````````` CARD:-{self.card} ````````CASH:- {self.cash} ``````` OTHERS:-{self.other}"


class Todo(models.Model):
    name = models.CharField(max_length=255)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class SubscriptionType(models.Model):
    subscription_type = models.CharField(max_length=255)
    description = models.CharField(
        max_length=1000, default="", null=True, blank=True)
    price = models.IntegerField(default=0, null=True, blank=True)
    status = models.BooleanField(default=True)
    offer_in_percentage = models.IntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.subscription_type


class SubscriptionAccessKeyAssociation(models.Model):
    key_name = models.CharField(max_length=255)
    tag = models.CharField(max_length=255)
    section_name = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    subscription = models.ManyToManyField(SubscriptionType)
    group = models.ManyToManyField(Group)

    def __str__(self):
        return self.key_name


class AccessKeyRemove(models.Model):
    subscription_key = models.ForeignKey(
        SubscriptionAccessKeyAssociation, on_delete=models.CASCADE)
    group_remove = models.ManyToManyField(Group)
    salon = models.ForeignKey(SalonDetails, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.group_remove.name) + ' Group From' + str(self.salon.name) + 'is Removed with' + str(self.subscription_key.key_name)


class AllowedPath(models.Model):
    path_name = models.CharField(
        max_length=255, null=True, default="", blank=True)

    def __str__(self):
        return self.path_name


class Job(models.Model):
    code = models.CharField(max_length=100, blank=True, null=True)
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, default=None, blank=True, null=True)
    sku = models.CharField(max_length=1000, blank=True, null=True, default="")
    name = models.CharField(max_length=250, blank=True, null=True)
    weight = models.IntegerField(blank=True, null=True, default=None)
    weight_unit = models.CharField(choices=(('KG', 'KG'), ('Gram', 'Gram'), (
        'ML', 'ML'), ('Gram', 'Gram'),), max_length=10, blank=True, null=True, default=None)
    description = models.TextField()
    price = models.FloatField(default=0)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    currency = models.CharField(
        choices=(('INR', 'INR'),), max_length=10, blank=True, null=True, default=None)
    availablity = models.BooleanField(default=False, null=True, blank=True)
    vendor = models.CharField(
        max_length=1000, blank=True, null=True, default="")
    category = models.CharField(choices=(('Shampoos and Conditioners', 'Shampoos and Conditioners'), ('Hairstyling Products', 'Hairstyling Products'), ('Hair Removal Products', 'Hair Removal Products'), (
        'Manicures and Pedicure Products and Tools', 'Manicures and Pedicure Products and Tools'), ('Manicures and Pedicure Products and Tools', 'Manicures and Pedicure Products and Tools'),), max_length=100, blank=True, null=True, default=None)
    collection = models.CharField(choices=(('Men', 'Men'), ('Female', 'Female'), ('Unisex', 'Unisex'), (
        'Others', 'Others'), ('All', 'All'),), max_length=40, blank=True, null=True, default=None)
    tag = models.CharField(max_length=1000, blank=True, null=True, default="")
    date_created = models.DateTimeField(default=timezone.now)
    date_updated = models.DateTimeField(auto_now=True)
    image = models.ImageField(
        upload_to="images/product_images/", default=None, null=True, blank=True)
    id = models.AutoField(primary_key=True, editable=False)

    objects = models.Manager()

    def __str__(self):
        return str(self.name)


class KanbanUserStory(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    acceptance = models.TextField()
    assign = models.CharField(max_length=255, null=True, blank=True)
    columnId = models.CharField(max_length=255)
    commentIds = JSONField(null=True, blank=True)
    description = models.TextField()
    dueDate = models.DateTimeField()
    itemIds = JSONField()
    title = models.CharField(max_length=255)
    priority = models.CharField(max_length=255)


class KanbanItem(models.Model):
    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    id = models.AutoField(primary_key=True, editable=False)
    assign = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    attachments = JSONField(null=True, blank=True)
    commentIds = JSONField(null=True, blank=True)
    description = models.TextField()
    dueDate = models.DateTimeField()
    image = models.CharField(max_length=255)
    priority = models.CharField(max_length=10, choices=[(
        'low', 'Low'), ('medium', 'Medium'), ('high', 'High')])
    title = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='TODO')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='TODO')


class KanbanColumn(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    title = models.TextField()
    itemIds = models.ManyToManyField(
        KanbanItem, related_name='columns', blank=True)


class KanbanProfile(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    salon = models.ForeignKey(
        SalonDetails, on_delete=models.CASCADE, to_field='id', null=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, null=True)
    kanban_items = models.ManyToManyField(
        KanbanItem, related_name='profiles', blank=True)
    kanban_columns = models.ManyToManyField(
        KanbanColumn, related_name='columns', blank=True)


class KanbanComment(models.Model):
    id = models.AutoField(primary_key=True, editable=False)
    comment = models.TextField()
    profile = models.ForeignKey(
        KanbanProfile, on_delete=models.CASCADE, null=True)


class Messaging(models.Model):
    from_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='sender', blank=True, null=True)
    to_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='receiver', blank=True, null=True)
    text = models.TextField()
    time = models.DateTimeField(auto_now=True, null=True)


class AuditLog(models.Model):
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
    )

    user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)
    action_type = models.CharField(max_length=10, choices=ACTION_CHOICES)
    action_time = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f"{self.user} - {self.action_type} - {self.content_object}"

    class Meta:
        ordering = ['-action_time']
