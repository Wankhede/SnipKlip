from django.urls import path
from .common import login, getServices, getStaff, getServicesCustom
from api.views import (
    booking, slot, upload, user_profile, salon_profile,
    billing, employee, expense, reports, customer,
    dashboard, calendar, salon, subscription, todos,
    contact_us, inventory, sendCode, upload, access_control, job, kanban, voucher, salary, membership, service,
    review)
from api.views.message_notification import invoice_notification,main,review_notification
from defaults import populate_json_data

urlpatterns = [
    path('login/', login, name='login'),
    path('change-password/', user_profile.change_password, name="Change Password"),
    path('send-email/', sendCode.send_code_email, name="send_code_email"),

    path('get-user/', user_profile.get_user_profile, name='get_user_profile'),
    path('user-details/', user_profile.get_user_detail, name='get_user_details'),
    path('salon-details/<str:user_id>/',
         salon_profile.get_salon_profile, name='get_salon_profile'),
    path('add-salon/', salon.add_salon_api, name='add_salon_api'),
    path('add-branch/', salon.add_branch_api, name='add_branch_api'),
    path('salon-details/', salon.getSalon, name='getSalon'),

    path('get-services/', getServices, name='get_services'),
    path('get-services-custom/', getServicesCustom, name='get_services'),

    path('dashboard/', dashboard.getDashboardDetails,
         name='get_dashboard_details'),
    path('get-subscription-type/', subscription.getSubscriptionType,
         name='getSubscriptionType'),

    path('bookings/', booking.getAllBookings, name='get_all_bookings'),
    path('bookings/<str:column_name>/<int:column_value>/',
         booking.getAllBookings, name='get_all_bookings'),
    path('customer_booking_history/<int:customer_id>/',
         booking.getCustomerBookingHistory, name='get_all_bookings'),
    path('availed-booking/', booking.bookingAvailed, name='bookingAvailed'),

    path('customer-booking-history/<int:id>/',
         customer.getCustomerBookings, name='getCustomerBookings'),

    path('check-availability/', slot.check_seat_availability,
         name='check_availability'),
    path('availability-check/', booking.check_seat_available,
         name='check_seat_available'),

    path('customers/', customer.getAllCustomers, name='get_all_customers'),
    path('customers/<str:column_name>/<int:column_value>/',
         customer.getAllCustomers, name='get_all_customers'),

    path('products/', inventory.getAllProducts, name='get_all_products'),
    path('delete-product/<int:product_id>/',
         inventory.deleteProduct, name='delete_product'),
    path('products/<str:column_name>/<int:column_value>/',
         inventory.getAllProducts, name='get_all_products'),

    path('jobs/', job.getAllJobs, name='get_all_jobs'),
    path('delete-job/<int:job_id>/', job.deleteJob, name='delete_product'),
    path('jobs/<int:branch_id>/', job.getAllJobs, name='get_all_jobs'),

    path('memberships/', membership.getAllMembership, name='get_all_jobs'),
    path('memberships/<str:column_name>/<int:column_value>/',
         membership.getAllMembership, name='get_all_jobs'),

    path('coupons/', voucher.getAllCouponCodes, name='get_all_jobs'),
    path('coupons/<str:column_name>/<int:column_value>/',
         voucher.getAllCouponCodes, name='get_all_jobs'),
     path('check-coupon-code/', voucher.checkCouponCode, name='check-coupon-code'),

    path('upload-file/', upload.UploadData, name='upload_customers'),
    path('download-template-file/', upload.UploadData, name='upload_customers'),

    path('employees/', employee.getAllEmployees, name='get_all_employees'),
    path('employees/<str:column_name>/<int:column_value>/',
         employee.getAllEmployees, name='get_all_employees'),
    path('get-available-staff/', slot.getAvailableStaff, name='getAvailableStaff'),

    path('billings/', billing.getAllBillings, name='get_all_billings'),
    path('billings/<str:column_name>/<int:column_value>/',
         billing.getAllBillings, name='get_all_billings'),

    path('expenses/', expense.getAllExpenses, name='get_all_expenses'),
    path('expenses/<str:column_name>/<int:column_value>/',
         expense.getAllExpenses, name='get_all_expenses'),

    path('reviews/', review.getAllReviews, name='get_all_reviews'),
    path('reviews/<str:column_name>/',review.getAllReviews, name='get_all_reviews'),

    path('services/', service.getAllServices, name='get_all_services'),
    path('services/<str:column_name>/<int:column_value>/',
         service.getAllServices, name='get_all_services'),

    path('calendar/', calendar.getAllAppointments, name='get_all_appointments'),
    path('calendar/<str:column_name>/<int:column_value>/',
         calendar.getAllAppointments, name='get_all_appointments'),
    path('calendar/add/', calendar.addEvents, name='add_events'),
    path('calendar/update/', calendar.updateEvents, name='update_events'),
    path('calendar/delete/', calendar.deleteEvents, name='delete_events'),
    path('calendar/events/', calendar.getEvents, name='get_events'),

    path('get-invoice/', billing.getAllBillings, name='get_all_billings'),
    path('get-a-invoice/', billing.getInvoice, name='getInvoice'),
    path('send-invoice-notification/', invoice_notification.send_invoice_notification, name='send_invoice_notification'),

    path('send-review-notification-to-customer/', review_notification.send_review_notification_to_customer, name='send_review_notification_to_customer'),
    
    path('reports/', reports.get_all_reports, name='get_all_reports'),
    path('employee-reports/', reports.employee_reports, name='employee_reports'),
    path('performance-reports/', reports.performance_reports,
         name='performance_reports'),
    path('revenue-reports/', reports.revenue_reports, name='revenue_reports'),
    path('payment-reports/', reports.payment_details, name='payment_details'),

    path('get-employees/', getStaff, name='get_staff'),
    path('salary/', salary.getAllSalary, name='get_all_salary'),
    path('salary/<str:column_name>/<int:column_value>/',
         salary.getAllSalary, name='get_all_salary'),
    path('salary/<str:column_name>/<int:column_value>/',
         salary.editSalary, name='EditSalary'),

    path('todos/', todos.todos_api, name='todo-list'),
    path('todos/<str:column_name>/<int:column_value>/',
         todos.todos_api, name='todo-list'),

    path('contact-us/', contact_us.contactus, name='contact-us'),

    path('paymentCallback/', subscription.payment_callback, name='payment_callback'),
    path('createPayment/', subscription.create_payment, name='create_payment'),
    path('subscription/', subscription.getSubscriptions, name='getSubscriptions'),

    path('kanban/add-item/', kanban.add_kanban_items, name='kanban-add-item'),
    path('kanban/reorder-items/',
         kanban.reorder_kanban_items, name='kanban-add-item'),
    path('kanban/profiles/', kanban.handle_profiles,
         name='kanbanprofile-list-create'),
    path('kanban/items/', kanban.handle_items,
         name='kanbanitem-list-create'),
    path('kanban/columns/', kanban.handle_columns,
         name='kanbancolumn-list-create'),
    path('kanban/columns/<int:column_id>/', kanban.handle_columns,
         name='kanban-column-delete'),
    path('kanban/add-column/', kanban.add_columns,
         name='kanbancolumn-list-create'),

    path('kanban-items/', kanban.Kanban, name='kanbanitem-list-create'),
    path('kanban-items/<int:pk>/', kanban.Kanban, name='kanbanitem-detail'),

    path('kanban-profiles/', kanban.Kanban, name='kanbanprofile-list-create'),
    path('kanban-profiles/<int:pk>/', kanban.Kanban, name='kanbanprofile-detail'),

    path('kanban-columns/', kanban.Kanban, name='kanbancolumn-list-create'),
    path('kanban-columns/<int:pk>/', kanban.Kanban, name='kanbancolumn-detail'),

    path('kanban-comments/', kanban.Kanban, name='kanbancomment-list-create'),
    path('kanban-comments/<int:pk>/', kanban.Kanban, name='kanbancomment-detail'),

    path('access-control-association/', access_control.get_data_grouped_by_tag,
         name='access-control-association-grouped-by-tag'),
    path('add-all-access-control-essentials/', populate_json_data.load_JSON_data,
         name='add-all-access-control-essentials'),
]
