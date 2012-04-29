from django.core.management.base import BaseCommand, CommandError
from server.work.models import *
import datetime


class Command(BaseCommand):
    args = ''
    help = 'Clean timeouts.'

    def handle(self, *args, **options):
        t = Task.objects.filter(status="IP")
        t = t.filter(started__lt=datetime.datetime.now()-datetime.timedelta(minutes=15))
        t.update(status="O")
        print "%d Stale jobs cleared." % (len(t), )
        return None
