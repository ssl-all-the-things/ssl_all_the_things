from django.core.management.base import BaseCommand, CommandError
from server.work.models import *
from itertools import combinations_with_replacement


class Command(BaseCommand):
    args = ''
    help = 'Init work database.'

    def handle(self, *args, **options):
        for block in combinations_with_replacement(range(256), 3):
            # Filter RFC 1918
            if block[0] == 10: continue
            if block[0] == 127 and block[1] > 15 and block[1] < 32: continue
            if block[0] == 192 and block[1] == 168: continue
            if block[0] == 0: continue
            block_str = "%d %d %d" % (block[0], block[1], block[2])
            t = Task(bucket = block_str)
            t.save()
