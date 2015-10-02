from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from explorer.models import User, Collection, UserProfile


class Command(BaseCommand):
    help = 'Setup yang-explorer initial database'

    def create_superuser(self):
        User.objects.create_superuser(username='admin', password='admin', email='')

    def create_guestuser(self):
        guest = User()
        guest.username = 'guest'
        guest.first_name = 'Guest'
        guest.last_name = 'User'
        guest.set_password('guest')
        guest.is_staff = True
        guest.save()

        # add permissions
        for table in ['session', 'collection', 'userprofile', 'deviceprofile']:
            for code in ['add', 'change', 'delete']:
                code_name = code + '_' + table
                permission = Permission.objects.get(codename=code_name)
                guest.user_permissions.add(permission)

        # create default model
        profile = UserProfile(user=guest, module='ietf-interfaces@2013-12-23')
        profile.save()

        # add default collection
        col = Collection(name='default', user=guest, description='Default Collection')
        col.save()

    def handle(self, *args, **options):
        self.create_superuser()
        self.create_guestuser()