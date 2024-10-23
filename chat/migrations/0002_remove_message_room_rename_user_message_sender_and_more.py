# Generated by Django 5.1.1 on 2024-10-22 23:51

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chat', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='room',
        ),
        migrations.RenameField(
            model_name='message',
            old_name='user',
            new_name='sender',
        ),
        migrations.AddField(
            model_name='message',
            name='read_by',
            field=models.ManyToManyField(blank=True, related_name='read_messages', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(blank=True, max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_group', models.BooleanField(default=False)),
                ('participants', models.ManyToManyField(related_name='conversations', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='message',
            name='conversation',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='messages', to='chat.conversation'),
            preserve_default=False,
        ),
        migrations.DeleteModel(
            name='Room',
        ),
    ]