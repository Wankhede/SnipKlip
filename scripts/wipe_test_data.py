#!/usr/bin/env python3
"""
Wipe all SnipKlip application database rows after exploratory / e2e testing.

- Deletes business + auth session data so the DB is clean for the next run.
- NEVER deletes log files (django.log, .run/*.log, etc.).
- Re-seeds minimal bootstrap (admin, AllowedPath, SubscriptionType, access keys,
  one salon + branch) so subsequent tests can still authenticate.

Usage:
    python scripts/wipe_test_data.py [--settings app.settings.local] [--no-reseed]
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
os.chdir(PROJECT_ROOT)


def parse_args():
    parser = argparse.ArgumentParser(description="Wipe SnipKlip DB data; keep log files.")
    parser.add_argument(
        "--settings",
        default=os.getenv("DJANGO_SETTINGS_MODULE", "app.settings.local"),
    )
    parser.add_argument(
        "--no-reseed",
        action="store_true",
        help="Do not recreate admin / access-control bootstrap after wipe",
    )
    parser.add_argument(
        "--keep-admin",
        action="store_true",
        help="Deprecated alias: reseed is default; use --no-reseed to skip",
    )
    return parser.parse_args()


# Models whose rows are wiped (business + app data). Auth.User is handled via backend.User.
WIPE_MODELS = [
    # Kanban / messaging
    "backend.KanbanComment",
    "backend.KanbanItem",
    "backend.KanbanColumn",
    "backend.KanbanProfile",
    "backend.KanbanUserStory",
    "backend.Messaging",
    "backend.AuditLog",
    "backend.Todo",
    "backend.Job",
    # Commerce / bookings
    "backend.UsedCoupon",
    "backend.Refund",
    "backend.Review",
    "backend.ProductInvoiceItem",
    "backend.ProductInvoice",
    "backend.ProductItem",
    "backend.Invoice",
    "backend.Appointment",
    "backend.OrderItem",
    "backend.DiscountDetails",
    "backend.Payment",
    "backend.CouponCode",
    "backend.Membership",
    "backend.Expense",
    "backend.Salary",
    "backend.Leave",
    "backend.Department",
    "backend.PaymentMode",
    "backend.Product",
    "backend.Service_CSV",
    "backend.Data_CSV",
    "backend.Service",
    "backend.Employee",
    "backend.BranchCustomerMobile",
    "backend.Customer",
    "backend.Branch_Time_Schedule",
    "backend.Branch_Images",
    "backend.Branch",
    "backend.Subscription",
    "backend.SalonDetails",
    # Access control associations (reseeded)
    "backend.SubscriptionAccessKeyAssociation",
    "backend.AccessKeyRemove",
    "backend.AllowedPath",
    "backend.SubscriptionType",
    "backend.UserType",
]

# Django framework tables that accumulate during tests
FRAMEWORK_WIPE = [
    "token_blacklist.OutstandingToken",
    "token_blacklist.BlacklistedToken",
    "authtoken.Token",
    "sessions.Session",
    "admin.LogEntry",
    "account.EmailAddress",
    "account.EmailConfirmation",
    "socialaccount.SocialAccount",
    "socialaccount.SocialToken",
    "socialaccount.SocialApp",
    "social_django.UserSocialAuth",
    "social_django.Nonce",
    "social_django.Association",
    "social_django.Code",
    "social_django.Partial",
]


def get_model(label: str):
    from django.apps import apps

    try:
        return apps.get_model(label)
    except LookupError:
        return None


def wipe_model(label: str) -> int:
    model = get_model(label)
    if model is None:
        return 0
    count = model.objects.count()
    if count:
        model.objects.all().delete()
    return count


def wipe_database() -> dict:
    from django.contrib.auth.models import Group
    from django.db import connection, transaction

    summary: dict = {"deleted": {}, "preserved_logs": True}

    with transaction.atomic():
        for label in WIPE_MODELS + FRAMEWORK_WIPE:
            deleted = wipe_model(label)
            if deleted:
                summary["deleted"][label] = deleted

        # Users last (backend.User extends auth.User)
        user_model = get_model("backend.User")
        if user_model is not None:
            n = user_model.objects.count()
            if n:
                user_model.objects.all().delete()
                summary["deleted"]["backend.User"] = n

        Group.objects.all().delete()

        # Reset sqlite sequences so reseeded IDs stay predictable when possible
        if connection.vendor == "sqlite":
            with connection.cursor() as cursor:
                cursor.execute("DELETE FROM sqlite_sequence")

    return summary


def reseed_bootstrap() -> dict:
    """Restore admin + access essentials + one salon/branch for the next test cycle."""
    from django.contrib.auth.models import Group
    from backend.models import (
        AllowedPath,
        Branch,
        SalonDetails,
        Subscription,
        SubscriptionType,
        User,
    )
    from defaults.populate_json_data import (
        load_Access_Control_Keys,
        load_Allowed_Path,
        load_Subscription_Types,
    )

    info: dict = {}

    load_Subscription_Types()
    load_Allowed_Path()
    load_Access_Control_Keys()
    info["allowed_paths"] = AllowedPath.objects.count()
    info["subscription_types"] = SubscriptionType.objects.count()

    admin_group, _ = Group.objects.get_or_create(name="Admin")
    admin, created = User.objects.get_or_create(
        username=os.getenv("SNIPKLIP_ADMIN_USER", "admin"),
        defaults={
            "email": "admin@snipklip.local",
            "is_staff": True,
            "is_superuser": True,
            "is_active": True,
        },
    )
    password = os.getenv("SNIPKLIP_ADMIN_PASSWORD", "Admin@123")
    admin.set_password(password)
    admin.is_staff = True
    admin.is_superuser = True
    admin.is_active = True
    admin.save()
    admin.groups.add(admin_group)
    info["admin"] = {"username": admin.username, "created": created, "id": admin.id}

    salon, _ = SalonDetails.objects.get_or_create(
        id=int(os.getenv("SNIPKLIP_SALON_ID", "3")),
        defaults={
            "user": admin,
            "name": "ADMIN",
            "email": "admin@snipklip.local",
            "reg_no": "ADMIN-001",
            "contact_no": "9999999999",
            "owner_name": "Admin",
            "owner_email": "admin@snipklip.local",
        },
    )
    # Ensure FK even if row already existed empty
    if salon.user_id is None:
        salon.user = admin
        salon.save(update_fields=["user"])

    branch, _ = Branch.objects.get_or_create(
        id=int(os.getenv("SNIPKLIP_BRANCH_ID", "1")),
        defaults={
            "salon": salon,
            "branch_name": "Main",
            "owner_contact_no": "9999999999",
            "address": "Test Address",
            "locality": "Test",
            "city": "Pune",
            "state": "MH",
            "pincode": "411001",
        },
    )
    if branch.salon_id != salon.id:
        branch.salon = salon
        branch.save(update_fields=["salon"])

    # Active subscription so middleware does not deny Admin bootstrap paths
    # Model choices use uppercase PREMIUM / STANDARD / STANDARD PLUS
    sub_name = 'PREMIUM'
    if SubscriptionType.objects.filter(subscription_type__iexact='Premium').exists():
        sub_name = (
            SubscriptionType.objects.filter(subscription_type__iexact='Premium')
            .first()
            .subscription_type
        )
    elif SubscriptionType.objects.exists():
        sub_name = SubscriptionType.objects.first().subscription_type

    from django.utils import timezone
    from datetime import timedelta

    Subscription.objects.filter(salon=salon).delete()
    Subscription.objects.create(
        salon=salon,
        user=admin,
        name_of_subscription=str(sub_name).upper() if str(sub_name).upper() in {
            'STANDARD', 'STANDARD PLUS', 'PREMIUM'
        } else 'PREMIUM',
        paid=True,
        start_date=timezone.now(),
        end_date=timezone.now() + timedelta(days=365),
        type='YEARLY',
    )

    info["salon_id"] = salon.id
    info["branch_id"] = branch.id
    return info


def assert_logs_untouched() -> list[str]:
    candidates = [
        PROJECT_ROOT / "django.log",
        PROJECT_ROOT.parent / ".run" / "backend.log",
        PROJECT_ROOT.parent / ".run" / "frontend.log",
    ]
    existing = [str(p) for p in candidates if p.exists()]
    return existing


def main():
    args = parse_args()
    os.environ["DJANGO_SETTINGS_MODULE"] = args.settings

    import django

    django.setup()

    logs_before = assert_logs_untouched()
    summary = wipe_database()
    reseed = None if args.no_reseed else reseed_bootstrap()
    logs_after = assert_logs_untouched()

    print("===== DB WIPE COMPLETE =====")
    print(f"deleted_tables: {len(summary['deleted'])}")
    for label, count in sorted(summary["deleted"].items()):
        print(f"  - {label}: {count}")
    print(f"log_files_preserved: {logs_after}")
    if set(logs_before) - set(logs_after):
        print("WARNING: some log files disappeared (unexpected)")
    if reseed:
        print(f"reseed: {reseed}")
    else:
        print("reseed: skipped (--no-reseed)")


if __name__ == "__main__":
    main()
