# Generated by Django 2.1.15 on 2021-11-05 18:13

from django.db import migrations, models
import recipe.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_recipe'),
    ]

    operations = [
        migrations.AddField(
            model_name='recipe',
            name='image',
            field=models.ImageField(null=True, upload_to=recipe.apps.core.models.recipe_image_file_path),
        ),
    ]
