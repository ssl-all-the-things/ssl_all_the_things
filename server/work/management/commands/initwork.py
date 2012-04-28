from django.core.management.base import BaseCommand, CommandError
from server.work.models import *
from itertools import combinations_with_replacement


class Command(BaseCommand):
    args = ''
    help = 'Init work database.'

    def handle(self, *args, **options):
        for block in combinations_with_replacement(range(256), 3):
            block_str = "%d %d %d" % (block[0], block[1], block[2])
            t = Task(bucket = block_str)
            t.save()
