# Generated by Django 5.1.1 on 2024-10-15 04:07

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PalabraClave',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('palabra', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Requisito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('descripcion', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Propuesta',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
                ('objetivo', models.TextField()),
                ('cantidad_alumnos', models.PositiveIntegerField()),
                ('cantidad_profesores', models.PositiveIntegerField()),
                ('fecha_creacion', models.DateTimeField(auto_now_add=True)),
                ('fecha_actualizacion', models.DateTimeField(auto_now=True)),
                ('autor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='propuestas', to=settings.AUTH_USER_MODEL)),
                ('palabras_clave', models.ManyToManyField(to='propuestas.palabraclave')),
                ('requisitos', models.ManyToManyField(to='propuestas.requisito')),
            ],
            options={
                'ordering': ['-fecha_creacion'],
                'indexes': [models.Index(fields=['nombre'], name='propuestas__nombre_81bcac_idx'), models.Index(fields=['fecha_creacion'], name='propuestas__fecha_c_394c78_idx')],
            },
        ),
    ]
