# Generated by Django 2.2.6 on 2019-11-23 09:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('my_app', '0017_order_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='amount',
            field=models.FloatField(default=20),
            preserve_default=False,
        ),
    ]
