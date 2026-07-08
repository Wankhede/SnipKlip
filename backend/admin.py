from django.contrib import admin
from backend.models import *


class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'name', 'company_name', 'user_type', 'ratings', 'user_status', 'mobile', 'subscription_type',
                    'dob', 'gender', 'send_alerts_to', 'address', 'state', 'city', 'image', 'language', 'instagram_profile')
    list_filter = ('user_type', 'user_status', 'subscription_type', 'language')
    search_fields = ('username', 'email', 'name', 'company_name',
                     'mobile', 'address', 'state', 'city', 'instagram_profile')
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal info', {'fields': ('name', 'first_name', 'last_name', 'company_name', 'user_type', 'ratings', 'user_status', 'mobile',
         'subscription_type', 'dob', 'gender', 'send_alerts_to', 'address', 'state', 'city', 'image', 'language', 'instagram_profile')}),
        ('Permissions', {'fields': ('is_active', 'is_staff',
         'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


class ServiceAdmin(admin.ModelAdmin):
    search_fields = ('category', 'name')


admin.site.register(CouponCode)
admin.site.register(Membership)
admin.site.register(User, UserAdmin)
admin.site.register(UserType)
admin.site.register(AuditLog)
admin.site.register(Service, ServiceAdmin)
admin.site.register(Employee)
admin.site.register(Salary)
admin.site.register(Invoice)
admin.site.register(BranchCustomerMobile)
admin.site.register(Branch_Time_Schedule)


class SubscriptionTypeAdmin(admin.ModelAdmin):
    list_display = ('subscription_type', 'price', 'offer_in_percentage')
    search_fields = ('subscription_type', 'price', 'offer_in_percentage')


admin.site.register(SubscriptionType, SubscriptionTypeAdmin)
admin.site.register(AllowedPath)
admin.site.register(AccessKeyRemove)
admin.site.register(SubscriptionAccessKeyAssociation)


class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'salon', 'name_of_subscription',
                    'start_date', 'end_date')
    # search_fields = ('subscription_type','price','offer_in_percentage')


admin.site.register(Subscription, SubscriptionAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'collection')
    list_filter = ('category', 'collection', 'availablity')
    search_fields = ('name', 'category')


class ProductItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'type', 'date_created')
    list_filter = ('type', 'date_created')
    search_fields = ('product__name',)


class ProductInvoiceAdmin(admin.ModelAdmin):
    list_display = ('transaction', 'customer', 'total', 'date_created')
    list_filter = ('date_created',)
    search_fields = ('transaction', 'customer')


class ProductInvoiceItemAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity',
                    'status', 'rate', 'tax', 'due_date')
    list_filter = ('status', 'due_date')
    search_fields = ('invoice__transaction', 'product__name')


admin.site.register(Product, ProductAdmin)
admin.site.register(Data_CSV)
admin.site.register(Expense)
admin.site.register(PaymentMode)
admin.site.register(ProductItem, ProductItemAdmin)
admin.site.register(ProductInvoice, ProductInvoiceAdmin)


class CustomerAdmin(admin.ModelAdmin):
    search_fields = ('username', 'email')


admin.site.register(Customer, CustomerAdmin)


class Branch_ImagesAdmin(admin.StackedInline):
    model = Branch_Images


class BranchAdmin(admin.ModelAdmin):
    inlines = [Branch_ImagesAdmin]


class BranchAdmin(admin.ModelAdmin):
    list_display = ['branch_name', 'owner_contact_no', 'address', 'locality', 'city',
                    'state', 'pincode', 'availability_status', 'lat', 'lng', 'total_seat', 'total_staff']
    search_fields = ['branch_name', 'owner_contact_no',
                     'address', 'locality', 'city', 'state', 'pincode']
    list_filter = ['availability_status',
                   'online_booking_appointment', 'salon_type']
    list_editable = ['availability_status', 'total_seat', 'total_staff']
    list_per_page = 10


class SalonDetailsAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'reg_no',
                    'contact_no', 'owner_name', 'owner_email']
    search_fields = ['name', 'email', 'reg_no',
                     'contact_no', 'owner_name', 'owner_email']
    list_per_page = 10


admin.site.register(SalonDetails, SalonDetailsAdmin)
admin.site.register(Branch, BranchAdmin)


@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('user', 'leavetype', 'startdate', 'enddate', 'status')
    list_filter = ('leavetype', 'status', 'is_approved')
    search_fields = ('user__username', 'leavetype', 'status')
    ordering = ('-created',)
    readonly_fields = ('created', 'updated', 'defaultdays', 'is_approved')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'salon', 'branch', 'user',
                    'totalPrice', 'isPaid', 'booking_status')
    list_filter = ('salon', 'branch', 'user', 'isPaid', 'booking_status')
    search_fields = ('order_id', 'salon__name',
                     'branch__branch_name', 'user__username')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'qty', 'price')
    list_filter = ('service',)
    search_fields = ('name', 'service__name')


admin.site.register(Appointment, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)


class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'salon', 'branch',
                    'rating', 'comment', 'createdAt')
    list_filter = ('salon', 'branch', 'rating')
    search_fields = ('user__username', 'salon__name', 'branch__branch_name')
    readonly_fields = ('id', 'createdAt')
    ordering = ('-createdAt',)


admin.site.register(Review, ReviewAdmin)


class KanbanUserStoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
    ordering = ('id',)


class KanbanCommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment')
    search_fields = ('comment',)
    ordering = ('id',)


class KanbanItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'dueDate', 'priority')
    search_fields = ('title', 'description',)
    ordering = ('id',)


class KanbanProfileAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'salon', 'branch')
    list_filter = ('salon', 'branch')
    search_fields = ('user__username', 'salon__name', 'branch__branch_name')


class KanbanColumnAdmin(admin.ModelAdmin):
    list_display = ('id', 'title')
    search_fields = ('title',)
    ordering = ('id',)


# Register the models and admin classes
admin.site.register(KanbanComment, KanbanCommentAdmin)
admin.site.register(KanbanItem, KanbanItemAdmin)
admin.site.register(KanbanProfile, KanbanProfileAdmin)
admin.site.register(KanbanUserStory, KanbanUserStoryAdmin)
admin.site.register(KanbanColumn, KanbanColumnAdmin)
