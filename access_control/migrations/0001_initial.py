import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessElement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('description', models.CharField(blank=True, default='', max_length=255)),
            ],
            options={
                'db_table': 'business_elements',
            },
        ),
        migrations.CreateModel(
            name='AccessRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_permission', models.BooleanField(default=False)),
                ('read_permission', models.BooleanField(default=False)),
                ('read_all_permission', models.BooleanField(default=False)),
                ('update_permission', models.BooleanField(default=False)),
                ('update_all_permission', models.BooleanField(default=False)),
                ('delete_permission', models.BooleanField(default=False)),
                ('delete_all_permission', models.BooleanField(default=False)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_rules', to='users.role')),
                ('element', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='access_rules', to='access_control.businesselement')),
            ],
            options={
                'db_table': 'access_roles_rules',
                'unique_together': {('role', 'element')},
            },
        ),
    ]
