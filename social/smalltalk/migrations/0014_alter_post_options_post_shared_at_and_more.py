# Generated by Django 5.2.1 on 2025-06-11 11:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('smalltalk', '0013_remove_post_is_shared_remove_post_original_post_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-created_at', '-shared_at']},
        ),
        migrations.AddField(
            model_name='post',
            name='shared_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='shared_content',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='post',
            name='shared_user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='shared_posts', to=settings.AUTH_USER_MODEL),
        ),
        migrations.DeleteModel(
            name='Repost',
        ),
    ]
