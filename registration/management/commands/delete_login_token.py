from datetime import datetime, timedelta

from django.core.management.base import BaseCommand

from pyconkr.models import EmailToken


class Command(BaseCommand):
    help = 'Delete token 10 mins past'

    def handle(self, *args, **options):
        filtering_time = datetime.now() - timedelta(minutes=10)
        all_email_token = EmailToken.objects.filter(created__lt=filtering_time).all()
        all_email_token.delete()
