from django.db import migrations, models


def map_all_roles_to_user(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.exclude(role='user').update(role='user')


def reverse_noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_update_user_roles'),
    ]

    operations = [
        migrations.RunPython(map_all_roles_to_user, reverse_noop),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[('user', 'Користувач')],
                default='user',
                max_length=20,
            ),
        ),
    ]
