"""Time-bounded building management access, with null legacy starts."""
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone


def current_management_q(prefix='', at=None):
    at = at or timezone.now()
    stem = f'{prefix}__' if prefix else ''
    return (
        (Q(**{stem + 'start_at__isnull': True}) | Q(**{stem + 'start_at__lte': at}))
        & (Q(**{stem + 'end_at__isnull': True}) | Q(**{stem + 'end_at__gt': at}))
    )


def client_visible_visits(visits, clients):
    """Current managers see open work; former managers see closed work from their tenure."""
    from visit.models import BuildingClient, Visit

    links = BuildingClient.objects.filter(
        building_id=OuterRef('building_id'), client__in=clients,
    )
    at_creation = links.filter(
        Q(start_at__isnull=True) | Q(start_at__lte=OuterRef('datetime_created')),
    ).filter(
        Q(end_at__isnull=True) | Q(end_at__gt=OuterRef('datetime_created')),
    )
    return visits.annotate(
        managed_now=Exists(links.filter(current_management_q())),
        managed_when_created=Exists(at_creation),
    ).filter(
        Q(managed_now=True, status__in=(Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND))
        | Q(managed_when_created=True, status__in=(Visit.COMPLETED, Visit.APPROVED, Visit.REJECTED))
    )
