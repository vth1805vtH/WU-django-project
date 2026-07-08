from django.db import migrations


def create_payment_methods(apps, schema_editor):
    PaymentMethod = apps.get_model('accounts', 'PaymentMethod')
    PaymentMethod.objects.get_or_create(
        name='Visa Card',
        defaults={
            'slug': 'visa-card',
            'description': 'Pay with your Visa credit or debit card',
            'is_active': True,
        }
    )
    PaymentMethod.objects.get_or_create(
        name='ACLEDA Bank',
        defaults={
            'slug': 'acleda-bank',
            'description': 'Pay via ACLEDA Bank account (QR code)',
            'is_active': True,
        }
    )


def reverse_func(apps, schema_editor):
    PaymentMethod = apps.get_model('accounts', 'PaymentMethod')
    PaymentMethod.objects.filter(slug__in=['visa-card', 'acleda-bank']).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_paymentmethod_qr_code'),
    ]

    operations = [
        migrations.RunPython(create_payment_methods, reverse_func),
    ]
