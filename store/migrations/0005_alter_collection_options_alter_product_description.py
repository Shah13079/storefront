# Generated by Django 4.2.6 on 2024-08-22 07:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("store", "0004_auto_20231007_0453"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="collection",
            options={"ordering": ["title"]},
        ),
        migrations.AlterField(
            model_name="product",
            name="description",
            field=models.TextField(null=True),
        ),
    ]
