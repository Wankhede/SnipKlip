from enum import Enum


class APIMessages(Enum):
    # Seat Availablity
    NO_SEAT_AVAILABLE = 'No Seat is Available for This Time Slot'
    SEAT_AVAILABLE = 'Hurray ...! Seat is Available'

    control = [
        {
            "access_key": "WEB_HEADER_MEMBERSHIP",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Membership Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_COUPON",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Coupon Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_KANABN",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Kanban Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_INVENTORY",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Inventory Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_EXPENSE",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Expense Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_DASHBOARD",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Dashboard Page",
            "subscription": ["PREMIUM", "STANDARD", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_EMPLOYEE",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Employee Page",
            "subscription": ["PREMIUM", "STANDARD", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_REPORT",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Report Page",
            "subscription": ["PREMIUM", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_BILLING",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Invoice Page",
            "subscription": ["PREMIUM", "STANDARD", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_CUSTOMER",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Customer Page",
            "subscription": ["PREMIUM", "STANDARD", "STANDARD PLUS"],
            "url": []
        },
        {
            "access_key": "WEB_HEADER_BOOKING",
            "tag": "WEB_HEADER",
            "section_name": "Header Menu",
            "description": "Booking Page",
            "subscription": ["PREMIUM", "STANDARD", "STANDARD PLUS"],
            "url": []
        }
    ]

    allowed_path = ['/api/v3/access-control-association/',
                    '/api/v3/login/', '/api/v3/contact-us/']

    # Invoice
    INVOICE_CREATED = 'Successfully created invoice'
    INVOICE_ID_NOT_FOUND = 'Invoice id not found'

    NOTIFICATION_CREATED = 'Notification send successfully'
    NOTIFICATION_FAILED = 'Notification send failed'

    # General messages
    SUCCESS = "Request successful."
    ERROR = "An error occurred."
    METHOD_NOT_ALLOWED = "Method not allowed."
    INTERNAL_SERVER_ERROR = "Internal Server Error."
    FILL_FIELDS = "Please Fill The Field Correctly."

    # User related messages
    USER_NOT_FOUND = "User not found."
    USER_ALREADY_EXISTS = "User already exists."
    USER_ID_NOT_FOUND = "User ID not found."
    USER_RETIREVED = "Successfully retrieved User."
    USER_UPDATED = "Successfully updated User"

    # Authentication messages
    INVALID_CREDENTIALS = "Invalid username or password."
    AUTHENTICATION_REQUIRED = "Authentication required."

    # Validation messages
    MISSING_FIELD = "Required field is missing: {}."
    INVALID_FIELD = "Invalid value for field {}: {}."

    # Employee related messages
    EMPLOYEE_NOT_FOUND = "Employee not found."
    EMPLOYEE_CREATED = "Employee created successfully."
    EMPLOYEE_UPDATED = "Employee updated successfully."
    EMPLOYEE_RETRIEVED = "Successfully retrieved employee."
    ALL_EMPLOYEE_RETRIEVED = "Successfully retrieved all employee(s)."

    # Billing related messages
    BILLING_NOT_FOUND = "Billing information not found."
    BILLING_CREATED = "Billing created successfully."
    BILLING_UPDATED = "Billing updated successfully."
    BILLING_RETRIEVED = "Successfully retrieved all billing records."
    BILLING_STATUS_UNPAID = "Billing was not created because the status 'UNPAID' was assigned."

    # Customer related messages
    CUSTOMER_NOT_FOUND = "Customer not found."
    CUSTOMER_CREATED = "Customer created successfully."
    CUSTOMER_UPDATED = "Customer updated successfully."
    CUSTOMER_RETRIEVED = "Successfully retrieved customer."
    ALL_CUSTOMER_RETRIEVED = "Successfully retrieved all customer(s)."

    # Booking related messages
    BOOKING_NOT_FOUND = "Booking not found."
    BOOKING_CREATED = "Booking created successfully."
    BOOKING_UPDATED = "Booking updated successfully."
    BOOKING_RETRIEVED = "Successfully retrieved booking."
    ALL_BOOKING_RETRIEVED = "Successfully retrieved all booking(s)."
    DELETE_ALL_BOOKINGS = 'All Bookings deleted assoictated to this invoice'
    BOOKING_AVAILED = 'Service is completed'

    # Appointment related messages
    APPOINTMENT_NOT_FOUND = "Appointment not found."
    APPOINTMENT_CREATED = "Appointment created successfully."
    APPOINTMENT_UPDATED = "Appointment updated successfully."
    APPOINTMENT_DELETED = "Appointment deleted successfully."
    APPOINTMENT_RETRIEVED = "Successfully retrieved appointment."
    APPOINTMENT_NOT_MENTIONED = "Please mention appointment to be deleted"
    ALL_APPOINTMENT_RETRIEVED = "Successfully retrieved all appointment(s)."

    # Invoice related messages
    INVOICE_RETRIEVED = "Successfully retrieved the invoice."
    ALL_INVOICE_RETRIEVED = "Successfully retrieved all invoice(s)."

    # Expense related messages
    EXPENSE_NOT_FOUND = "Expense not found."
    EXPENSE_CREATED = "Expense created successfully."
    EXPENSE_UPDATED = "Expense updated successfully."
    EXPENSE_RETRIEVED = "Successfully retrieved expense."
    ALL_EXPENSE_RETRIEVED = "Successfully retrieved all expense(s)."


    # Review related messages
    REVIEW_NOT_FOUND = "Review not found."
    REVIEW_CREATED = "Review created successfully."
    REVIEW_UPDATED = "Review updated successfully."
    REVIEW_RETRIEVED = "Successfully retrieved All Review."
    ALL_REVIEW_RETRIEVED = "Successfully retrieved all Review(s)."
    REVIEW_DELETED = "Successfully Deleted Review"
    CANT_SEE_REVIEW = "Thank You !You Have Submitted Your Feedback Successfully"

    # Service related messages
    SERVICE_NOT_FOUND = "Service not found."
    SERVICE_CREATED = "Service created successfully."
    SERVICE_UPDATED = "Service updated successfully."
    SERVICE_RETRIEVED = "Successfully retrieved expense."
    ALL_SERVICE_RETRIEVED = "Successfully retrieved all expense(s)."

    # Kanban related messages
    KANBAN_ITEM_NOT_FOUND = "Kanban item not found."
    KANBAN_ITEM_CREATED = "Kanban item created successfully."
    KANBAN_ITEM_UPDATED = "Kanban item updated successfully."
    KANBAN_ITEM_DELETED = "Kanban item deleted successfully."
    KANBAN_COLUMN_DELETED = "Kanban column deleted successfully."
    KANBAN_ITEM_RETRIEVED = "Successfully retrieved Kanban item."
    ALL_KANBAN_ITEMS_RETRIEVED = "Successfully retrieved all Kanban item(s)."

    # Booking related messages
    SALARY_NOT_FOUND = "Salary not found."
    SALARY_CREATED = "Salary created successfully."
    SALARY_UPDATED = "Salary updated successfully."
    SALARY_RETRIEVED = "Successfully retrieved salary."
    ALL_SALARY_RETRIEVED = "Successfully retrieved all salary(s)."
    DELETE_ALL_SALARYS = 'All salary deleted assoictated to this invoice'
    SALARY_AVAILED = 'Salary is completed'

    # Expense related messages
    MESSAGE_NOT_FOUND = "Message not found."
    MESSAGE_CREATED = "Message created successfully."
    MESSAGE_UPDATED = "Message updated successfully."
    MESSAGE_RETRIEVED = "Successfully retrieved message."
    ALL_MESSAGE_RETRIEVED = "Successfully retrieved all message(s)."

    # Membership related messages
    MEMBERSHIP_NOT_FOUND = "Membership not found."
    MEMBERSHIP_CREATED = "Membership created successfully."
    MEMBERSHIP_UPDATED = "Membership updated successfully."
    MEMBERSHIP_RETRIEVED = "Successfully retrieved Membership."
    ALL_MEMBERSHIP_RETRIEVED = "Successfully retrieved all Membership(s)."

    # Coupon related messages
    COUPON_NOT_FOUND = "Coupon not found."
    COUPON_CREATED = "Coupon created successfully."
    COUPON_UPDATED = "Coupon updated successfully."
    COUPON_RETRIEVED = "Successfully retrieved coupon."
    ALL_COUPON_RETRIEVED = "Successfully retrieved all coupon(s)."

    # Salon details related messages
    SALON_REGISTERED = "Salon successfully registered."
    SALON_NOT_FOUND = "Salon not found."
    SALON_CREATED = "Salon created successfully."
    SALON_UPDATED = "Salon updated successfully."
    ALL_SALON_DETAIL_RETRIEVED = 'All Salon Details Retrived'
    SALON_DETAIL_NOT_RETRIEVED = 'Error Occured'

    # Email and Mobile related messages
    BOTH_ALREADY_EXISTS = "Email & Mobile (Both) Already Exists."
    MOBILE_ALREADY_EXISTS = "Mobile Number Already Exists"
    EMAIL_ALREADY_EXISTS = "Email Already Exists"

    # Product related messages
    PRODUCT_NOT_FOUND = "Product not found."
    PRODUCT_DOES_NOT_BELONGS_TO_YOU = "Product does not belongs to you."
    PRODUCT_DELETE_SUCCESS = "Successfully deleted Product."
    PRODUCT_CREATED = "Product created successfully."
    PRODUCT_UPDATED = "Product updated successfully."
    PRODUCT_RETRIEVED = "Successfully retrieved Product."

    # Payment related messages
    AMOUNT_NOT_PROVIDED = 'Amount not provided.'
    PAYMENT_STARTED = 'Payment Process Started.'
    ALREADY_PURCHASED = 'You have already purchased this'
    UPGRADE_PURCHASED = 'You can only upgrade and not downgrade the subscription.'
    PAYMENT_DONE = 'Payment successfully done.'
    PAYMENT_FAILURE = 'Payment failed please try again.'

    # Todos related messages
    TODO_NOT_FOUND = "Todo not found"
    TODO_RETRIEVED = "Successfully retrieved given todo"
    ALL_TODO_RETRIEVED = "Successfully retrieved all todos"
    TODO_CREATED = "Todo created successfully"
    TODO_UPDATED = "Todo updated successfully"

    # Misscellaneous messages
    SELECT_SERVICE_AND_STAFF = "Please select Services and Staffs."
    MESSAGE_TO_SNIPKLIP = "Successfully sent message to SnipKlip Team"
    PASSWORD_MISMATCH = 'Password does not match'
    USENAME_ALREADY_TAKEN = 'Username Already Exists'
    SALON_NAME_ALREADY_TAKEN = 'Salon Name Already Exists'
    OWNER_EMAIL_ALREADY_TAKEN = 'Owner Email Already Exists'
    SALON_EMAIL_ALREADY_TAKEN = 'Salon Email Already Exists'
    CONTACT_ALREADY_TAKEN = 'Contact No. Already Exists'
    EMAIL_NOT_RECEIVED = "Did Not Recieved Email"
    EMAIL_SENT = "Email Sent To Your Mail"
    PASSWORD_RESET = 'Successfully reset the Password'
    OTP_MISMATCH = 'OTP Did Not Match... Try Again'
    USER_OR_BRANCH_NOT_EXISTS = 'User Id or Branch Id Does Not Exists'
    CSV_FILE_FORMAT = "CSV file Should be in .csv format"
    UPLOAD_SUCCESS = 'Successfully Uploaded'

    # Branch
    ALL_BRANCH_DETAIL_RETRIEVED = 'All Branch Details Retrived'
    BRANCH_DETAIL_NOT_RETRIEVED = 'Error Occured'

    # Subscription
    ALL_SUBSCRIPTION_RETRIEVED = 'All Subscription History Retrieved'
    SUBSCRIPTION_NOT_RETRIEVED = 'Error Occured'

    # Access Control
    ALL_ACCESS_KEY_ASSOCIATION_RETRIEVED = 'All Access Key Association Retrieved'
    ACCESS_KEY_ASSOCIATION_NOT_RETRIEVED = 'Access Key Association Not Retrieved'

    # Coupon Code
    VALID_COUPON = 'HURRAY !!! Coupon Code Applied'
    LIMIT_VALUE = 'Subtotal Price should be Rs '
    INVALID_COUPON = 'Invalid/Expired Coupon Code'


SUCCESS_STATUS_CODE = 200
CREATED_CODE = 201
BAD_REQUEST_STATUS = 400
UNAUTHORISED_CODE = 401
NOT_FOUND_STATUS = 404
METHOD_NOT_ALLOWED = 405
FAILED_STATUS_CODE = 500
