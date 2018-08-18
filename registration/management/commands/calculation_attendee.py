from datetime import datetime

from django.core.management.base import BaseCommand

from registration.models import IssueTicket, Registration


class Command(BaseCommand):
    help = 'Calculating attendee count per Option'

    def handle(self, *args, **options):
        all_tickets = IssueTicket.objects.all()
        categorized_tickets = {}

        for ticket in all_tickets:
            if ticket.registration.option.name in categorized_tickets:
                if ticket.registration not in categorized_tickets[ticket.registration.option.name]:
                    categorized_tickets[ticket.registration.option.name].append(ticket.registration)
            else:
                categorized_tickets[ticket.registration.option.name] = [ticket.registration]

        all_registration = Registration.objects.all()

        print(datetime.now())

        for key in categorized_tickets.keys():
            print('{} - {}/{}'.format(key, len(categorized_tickets[key]),
                                      all_registration.filter(option__name=key).count()))
