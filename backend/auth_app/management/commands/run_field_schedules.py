"""Daily field scheduling: open periodic maintenance visits and send due/overdue reminders.

Run once a day from the host scheduler (cron or a systemd timer); every step is idempotent.
"""
from datetime import date

from django.core.management.base import BaseCommand, CommandError

from visit.maintenance import generate_due_visits, send_due_alerts


class Command(BaseCommand):
    help = 'Open due maintenance visits and send due-date reminders (idempotent; run daily).'

    def add_arguments(self, parser):
        parser.add_argument('--date', help='Treat this ISO date as today (for catch-up or testing).')
        parser.add_argument('--project', type=int)
        parser.add_argument('--dry-run', action='store_true', help='Report maintenance visits without creating them.')
        parser.add_argument('--skip-alerts', action='store_true')

    def handle(self, *args, **options):
        try:
            today = date.fromisoformat(options['date']) if options['date'] else None
        except ValueError:
            raise CommandError('--date must be YYYY-MM-DD.')
        created, skipped = generate_due_visits(today, options['project'], dry_run=options['dry_run'])
        verb = 'Would open' if options['dry_run'] else 'Opened'
        self.stdout.write(f'{verb} {len(created)} maintenance visit(s): {created}')
        for plan_id, reason in skipped:
            self.stdout.write(f'  plan {plan_id} skipped: {reason}')
        if not options['skip_alerts'] and not options['dry_run']:
            self.stdout.write(f'Due-date notifications created: {send_due_alerts(today, options["project"])}')
