from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import *

@receiver(post_save, sender=User)
@receiver(post_save, sender=SalonDetails)
@receiver(post_save, sender=Branch)
@receiver(post_save, sender=Employee)
def create_update_audit_log(sender, instance, created, **kwargs):
    action_type = 'CREATE' if created else 'UPDATE'
    AuditLog.objects.create(
        user=instance.user,
        action_type=action_type,
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.id,
    )

@receiver(post_delete, sender=User)
@receiver(post_delete, sender=SalonDetails)
@receiver(post_delete, sender=Branch)
@receiver(post_delete, sender=Employee)
def delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.user,
        action_type='DELETE',
        content_type=ContentType.objects.get_for_model(sender),
        object_id=instance.id,
    )