# SnipKlip App Guide

## Getting Started and Salon Onboarding
Route: /apps/salon-onboarding
Aliases: onboarding, setup salon, create branch, add branch, salon setup, register salon, get started
Prerequisites: Sign up or log in as a salon owner first.
Steps:
1. Log in to SnipKlip.
2. Open Salon Onboarding.
3. Add your salon details.
4. Add a branch with its address.
5. Save to unlock the app.
Outcome: Your salon has a branch and is ready to use.
Limitations: Working hours, KYC, and GST are not set up here.

## Dashboard and Business Overview
Route: /dashboard/default
Aliases: dashboard, today overview, business summary, today's bookings, walk-ins, income today
Prerequisites: Finish onboarding and pick a branch.
Steps:
1. Open the Dashboard.
2. Check the selected branch.
3. View today's bookings, income, walk-ins, and pending work.
Outcome: A quick snapshot of today.
Limitations: No settlements or multi-branch totals.

## Bookings and Appointments
Route: /apps/bookings/manage-bookings
Aliases: booking, bookings, appointment, appointments, schedule appointment, add booking, book client, reschedule, manage booking, slot, availability, walk-in
Prerequisites: Pick a branch. You need a customer, a service, and active staff.
Steps:
1. Open Manage Bookings.
2. Click Add Booking.
3. Pick the customer, service, date, slot, and staff.
4. Confirm to save it.
5. For a walk-in, mark it done to bill it.
Outcome: The appointment shows in your booking list.
Limitations: No accept/reject queue, no-show flow, or customer self-booking.

## Customers
Route: /apps/customers/manage-customers
Aliases: customer, customers, client, clients, guest profile, add customer, manage customers, customer history
Prerequisites: Pick a branch. Save only details the guest allows.
Steps:
1. Open Manage Customers.
2. Search the list, or click Add Customer.
3. Enter name and contact details.
4. Edit a customer from its row actions.
Outcome: Customer profiles ready for booking and billing.
Limitations: No wallet, loyalty, or customer portal.

## Employees and Staff
Route: /apps/employees/manage-employees
Aliases: employee, employees, staff, team, stylist, barber, beautician, add staff, manage employees, salary, incentive
Prerequisites: Use a role that can manage staff. Pick a branch.
Steps:
1. Open Manage Employees.
2. Click Add Employee.
3. Enter name, contact, role, salary, and incentives.
4. Edit a staff member to change role or status.
Outcome: Staff appear in booking and staffing lists.
Limitations: No shift scheduling, leave approval, or attendance.

## Services
Route: /apps/services/manage-service
Aliases: service, services, menu, price list, service menu, duration, add service, manage services
Prerequisites: Pick a branch.
Steps:
1. Open Manage Services.
2. Click Add Service.
3. Enter name, category, price, and duration.
4. Edit a service when details change.
Outcome: Services ready for bookings and invoices.
Limitations: No peak pricing, happy hours, or GST setup.

## Inventory and Products
Route: /apps/e-commerce/product/manage-product
Aliases: inventory, product, products, stock, retail, consumable, add product, manage products, SKU
Prerequisites: Pick a branch.
Steps:
1. Open Manage Products.
2. Click Add Product.
3. Enter name, price, and quantity.
4. Edit or delete a product when stock changes.
Outcome: Products ready for billing.
Limitations: No purchase orders or auto stock updates.

## Billing and Invoices
Route: /apps/invoices/manage-invoices
Aliases: billing, invoice, invoices, bill, payment, checkout, POS, add invoice, manage invoices, receipt
Prerequisites: Pick a branch. The customer, services, and staff should exist.
Steps:
1. Open Manage Invoices.
2. Click Add Invoice.
3. Add the customer, items, staff, tax, and discount.
4. Apply a membership or coupon if valid.
5. Pick the payment mode and check the total.
6. Save the invoice.
Outcome: An invoice with items and payment details.
Limitations: No refunds, payouts, wallets, or PDF receipts.

## Expenses
Route: /contact-us
Aliases: expense, expenses, cost, salon expense, add expense, business expense
Prerequisites: Pick a branch. Use an account that can add expenses.
Steps:
1. Open the Expenses area if it is on your plan.
2. Add an expense with amount, note, and date.
3. Edit an expense to update it.
Outcome: Expenses saved for the branch.
Limitations: No fixed frontend route here, no receipts or categories. Use Contact Us if the menu is missing.

## Reports and Analytics
Route: /apps/reports/dashboard
Aliases: reports, analytics, revenue report, employee report, performance report, payment report, business insights
Prerequisites: Pick a branch and record your bookings and invoices.
Steps:
1. Open Reports.
2. Pick a report: overview, employee, revenue, or payments.
3. Review the figures for that branch.
Outcome: Simple business insights.
Limitations: No exports, custom dashboards, or commission reports.

## Memberships
Route: /apps/membership/manage-membership
Aliases: membership, memberships, member plan, customer membership, discount plan
Prerequisites: Pick a branch and choose the customer.
Steps:
1. Open Manage Membership.
2. Create or edit a membership with discount and expiry.
3. Apply it at billing when offered.
Outcome: Members get a discount on invoices.
Limitations: No family plans or auto renewals.

## Coupons
Route: /apps/membership/manage-membership
Aliases: coupon, coupons, promo code, voucher, discount code, check coupon
Prerequisites: Pick a branch. Decide the code and rules.
Steps:
1. Open the coupons area.
2. Create a coupon with code, discount, expiry, and count.
3. Check the coupon before sharing it.
4. Apply it during billing.
Outcome: A discount you can apply at checkout.
Limitations: No campaign automation or gift cards.

## Reviews
Route: /apps/membership/manage-membership
Aliases: review, reviews, feedback, rating, customer review, service feedback
Prerequisites: A completed invoice. May need a Premium plan.
Steps:
1. Open the reviews area.
2. View or add feedback tied to an invoice.
3. Edit or remove a review if your role allows.
Outcome: Service feedback saved.
Limitations: No public widgets or Google review sync.

## Subscriptions and Plans
Route: /apps/profiles/account/basic
Aliases: subscription, subscriptions, plan, premium, standard, renew plan, razorpay, billing plan
Prerequisites: Use an account that manages salon billing.
Steps:
1. Open Account or Subscription settings.
2. Pick a plan: Standard, Standard Plus, or Premium.
3. Pay only to buy or renew.
4. Check the active plan after payment.
Outcome: Your plan controls which menus you see.
Limitations: This assistant cannot process payments. Use Contact Us for billing issues.

## Account, Branch, and Access
Route: /apps/profiles/account/basic
Aliases: account, profile, branch settings, access control, permissions, role, manager access, salon profile
Prerequisites: Sign in with your account.
Steps:
1. Open Account or Salon Profile.
2. Update the details your role allows.
3. Check the active branch before you work.
4. If a menu is missing, check your role and plan.
Outcome: Your role and plan set what you can do.
Limitations: The assistant cannot change roles or unlock menus.

## Password and Account Safety
Route: /forgot-password
Aliases: password, forgot password, reset password, login help, sign in issue, otp
Prerequisites: Use the email or phone on your account.
Steps:
1. Open the login page.
2. Click Forgot Password.
3. Follow the reset steps sent to you.
4. Set a new password and sign in.
Outcome: You get back into your account safely.
Limitations: Never share passwords or OTPs. Support will never ask for them.

## Getting Help
Route: /contact-us
Aliases: help, support, contact us, customer support, talk to support
Prerequisites: Have a general how-to question ready.
Steps:
1. Ask this assistant how a SnipKlip feature works.
2. If it can't help, open Contact Us.
3. Do not share passwords, OTPs, or payment details.
Outcome: Guidance from the guide, or support.
Limitations: The assistant cannot see your data or act for you.

## Unsupported Features
Route: /contact-us
Aliases: gift card, loyalty, referral, campaign, marketing automation, purchase order, barcode scanner, staff schedule, leave management, attendance, biometric, customer app, mobile app, zenoti go, waitlist, group booking, couples booking, cross-center booking, settlement, payout, commission, webhook, franchise, ai hairstyle, wallet, net banking, qr payment, google calendar invite, push notification, social media campaign
Prerequisites: None.
Steps:
1. This feature is not in the SnipKlip guide.
2. Try a supported area like bookings, customers, staff, services, inventory, invoices, reports, memberships, coupons, or reviews.
3. Use Contact Us for roadmap questions.
Outcome: Honest help without made-up features.
Limitations: Other salon tools are not SnipKlip.
