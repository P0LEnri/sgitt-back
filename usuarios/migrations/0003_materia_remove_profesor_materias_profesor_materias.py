# Generated by Django 5.1.1 on 2024-10-26 04:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('usuarios', '0002_areaconocimiento_alter_profesor_options_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Materia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100, unique=True)),
            ],
            options={
                'ordering': ['nombre'],
            },
        ),
        migrations.RemoveField(
            model_name='profesor',
            name='materias',
        ),
        migrations.AddField(
            model_name='profesor',
            name='materias',
            field=models.ManyToManyField(related_name='profesores', to='usuarios.materia'),
        ),
    ]
