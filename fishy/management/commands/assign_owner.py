"""
One-off command for the move to multi-user.

Gives every trip, catch, venue and bait that doesn't have an owner yet to
the named user. Safe to run more than once: records that already have an
owner are left alone.

    python manage.py assign_owner alanc
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from fishy.models import Bait, Catch, Trip, Venue


class Command(BaseCommand):
    help = "Assign all un-owned trips, catches, venues and baits to a user."

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        User = get_user_model()
        try:
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:
            raise CommandError(f"No user called '{options['username']}'")

        for model in (Venue, Bait, Trip, Catch):
            count = model.objects.filter(user__isnull=True).update(user=user)
            self.stdout.write(f"{model.__name__}: {count} assigned to {user.username}")

        self.stdout.write(self.style.SUCCESS("Done."))
