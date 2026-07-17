from django.contrib import messages
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from backend.models import User


@require_http_methods(['GET', 'POST'])
def signup_page(request):
    """Browser signup form for creating a Salon account."""
    if request.method == 'GET':
        return render(request, 'signup.html')

    email = (request.POST.get('email') or '').strip().lower()
    password = request.POST.get('password') or ''
    password_confirm = request.POST.get('password_confirm') or ''
    first_name = (request.POST.get('first_name') or '').strip()
    last_name = (request.POST.get('last_name') or '').strip()
    mobile = (request.POST.get('mobile') or '').strip()
    company_name = (request.POST.get('company_name') or '').strip()

    context = {
        'email': email,
        'first_name': first_name,
        'last_name': last_name,
        'mobile': mobile,
        'company_name': company_name,
    }

    if not email or not password:
        messages.error(request, 'Email and password are required.')
        return render(request, 'signup.html', context)

    if password != password_confirm:
        messages.error(request, 'Passwords do not match.')
        return render(request, 'signup.html', context)

    if len(password) < 8:
        messages.error(request, 'Password must be at least 8 characters.')
        return render(request, 'signup.html', context)

    if User.objects.filter(email__iexact=email).exists() or User.objects.filter(username__iexact=email).exists():
        messages.error(request, 'An account with this email already exists.')
        return render(request, 'signup.html', context)

    user = User.objects.create_user(
        username=email,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name,
        name=f'{first_name} {last_name}'.strip() or email,
        mobile=mobile or None,
        company_name=company_name or None,
        user_status=1,
    )
    group, _ = Group.objects.get_or_create(name='Salon')
    user.groups.add(group)

    messages.success(request, 'Account created. You can now log in to the admin panel (staff access requires an admin).')
    return redirect('/account-management/login/')
