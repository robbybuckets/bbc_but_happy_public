# Generated by Django 3.1.7 on 2021-03-02 14:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0015_auto_20210302_0152'),
    ]

    operations = [
        migrations.AlterField(
            model_name='article',
            name='source',
            field=models.CharField(blank=True, default='', max_length=512),
        ),
    ]