# Generated by Django 3.1.7 on 2021-03-01 17:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('scraper', '0002_articles'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Articles',
            new_name='LatestArticles',
        ),
    ]
