from django.db import migrations, models


def map_old_roles_to_new(apps, schema_editor):
    User = apps.get_model('users', 'User')
    role_mapping = {
        'student': 'buyer',
        'family': 'tenant',
    }

    for old_role, new_role in role_mapping.items():
        User.objects.filter(role=old_role).update(role=new_role)


def reverse_map_roles(apps, schema_editor):
    User = apps.get_model('users', 'User')
    reverse_mapping = {
        'buyer': 'student',
        'tenant': 'family',
    }

    for new_role, old_role in reverse_mapping.items():
        User.objects.filter(role=new_role).update(role=old_role)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(map_old_roles_to_new, reverse_map_roles),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('buyer', 'Покупець'),
                    ('tenant', 'Орендар'),
                    ('owner', 'Власник'),
                    ('realtor', 'Рієлтор'),
                    ('investor', 'Інвестор'),
                ],
                default='buyer',
                max_length=20,
            ),
        ),
    ]
