"""Small, scoped overview for the client home screen."""

from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import authorized_role_views
from visit.management import current_management_q, client_visible_visits
from visit.models import (
    Building, BuildingElevator, Client, ServiceRequestSubmission, Visit,
)


class ClientDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Reuse the two capabilities already required by the existing client flow.
        # A role must explicitly have client scope and the corresponding GET grant.
        for name in ('BuildingClientListCreateAPIView', 'ClientVisitsAPIView'):
            if not authorized_role_views(request, self, view_name=name).filter(
                role__asset_scope='client'
            ).exists():
                return Response({'detail': 'دسترسی به داشبورد کلاینت مجاز نیست.'}, status=403)

        project_id = int(request.query_params['p'])
        clients = Client.objects.filter(
            project_id=project_id, userclient__user=request.user,
        )
        buildings = Building.objects.filter(
            project_id=project_id, buildingclient__client__in=clients,
        ).filter(current_management_q('buildingclient')).distinct()
        elevators = BuildingElevator.objects.filter(
            building__in=buildings, elevator__project_id=project_id,
        )

        submission = ServiceRequestSubmission.objects.filter(visits=OuterRef('pk'))
        visits = client_visible_visits(Visit.objects.filter(
            type__project_id=project_id, building__in=buildings,
            building__project_id=project_id, is_deleted=False,
        ), clients).annotate(has_submission=Exists(submission))
        pending = visits.filter(status=Visit.NOTVISITED, is_active=False, has_submission=True)
        active = visits.filter(status__in=(Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND))
        active = active.exclude(status=Visit.NOTVISITED, is_active=False, has_submission=True)
        today = timezone.localdate()
        upcoming = active.filter(has_due_date=True, due_date__gte=today).order_by('due_date', 'id')
        overdue = active.filter(has_due_date=True, due_date__lt=today)

        preview = buildings.annotate(
            elevator_count=Count(
                'buildingelevator__elevator',
                filter=Q(buildingelevator__elevator__project_id=project_id),
                distinct=True,
            ),
        ).order_by('id').values(
            'id', 'name', 'verbose_name', 'code', 'address', 'elevator_count',
        )[:4]
        recent = visits.select_related('building', 'type').order_by('-datetime_created', '-id')[:3]
        next_visit = upcoming.select_related('building', 'type').first()

        def visit_item(visit):
            return {
                'id': visit.id,
                'building_id': visit.building_id,
                'building_name': visit.building.verbose_name or visit.building.name,
                'type_name': visit.type.verbose_name or visit.type.title,
                'status': visit.status,
                'is_pending_request': bool(
                    visit.has_submission and not visit.is_active and visit.status == Visit.NOTVISITED
                ),
                'due_date': visit.due_date,
                'datetime_created': visit.datetime_created,
            }

        return Response({
            'counts': {
                'buildings': buildings.count(),
                'elevators': elevators.values('elevator_id').distinct().count(),
                'pending': pending.count(),
                'active': active.count(),
                'overdue': overdue.count(),
                'completed': visits.filter(status__in=(Visit.COMPLETED, Visit.APPROVED)).count(),
            },
            'next_visit': visit_item(next_visit) if next_visit else None,
            'recent_visits': [visit_item(visit) for visit in recent],
            'buildings': list(preview),
        })
