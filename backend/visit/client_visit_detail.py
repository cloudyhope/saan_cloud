"""A narrow, client-owned visit detail and completed answer readout."""
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import authorized_role_views
from core.media_access import media_read_url
from visit.management import client_visible_visits
from visit.models import Client, Visit
from visit.report_snapshot import report_answers, report_photos


def scoped_client_visit(request, view, id):
    grants = authorized_role_views(request, view, view_name='ClientVisitsAPIView')
    if not grants.filter(role__asset_scope='client').exists():
        return None
    project_id = int(request.query_params['p'])
    clients = Client.objects.filter(project_id=project_id, userclient__user=request.user)
    visits = Visit.objects.filter(type__project_id=project_id,
                                  building__project_id=project_id, is_deleted=False)
    return get_object_or_404(client_visible_visits(visits, clients).select_related(
        'type', 'building', 'expert'), pk=id)


class ClientVisitDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        visit = scoped_client_visit(request, self, id)
        if visit is None:
            return Response({'detail': 'دسترسی به جزئیات خدمت مجاز نیست.'}, status=403)
        project_id = int(request.query_params['p'])
        pending = (not visit.is_active and visit.status == Visit.NOTVISITED and
                   visit.service_submissions.exists())
        elevator_rows = list(visit.elevator.filter(project_id=project_id).values('id', 'title'))
        report = []
        photos = []
        parts = []
        wage = None
        snapshot = None
        if visit.status in (Visit.COMPLETED, Visit.APPROVED):
            snapshot = visit.report_snapshots.order_by('-version').first()
            if snapshot:
                report = snapshot.payload.get('answers') or []
                raw_photos = snapshot.payload.get('photos') or []
                parts = snapshot.payload.get('parts') or []
                wage = snapshot.payload.get('wage')
            else:
                report = report_answers(visit)
                raw_photos = report_photos(visit)
            for item in raw_photos:
                link = item.get('link')
                signed = media_read_url(link, request) if link else None
                photos.append({
                    'id': item.get('id'),
                    'type_id': item.get('type_id'),
                    'type_name': item.get('type_name'),
                    'url': signed,
                    'created_at': item.get('created_at'),
                })
        expert_name = ' '.join(filter(None, (
            visit.expert.first_name, visit.expert.last_name))) if visit.expert else ''
        from visit.field_ops import chat_open, ensure_completion_code
        from visit.management import current_management_q
        from visit.models import BuildingClient
        current = BuildingClient.objects.filter(
            building_id=visit.building_id, client__userclient__user=request.user).filter(current_management_q()).exists()
        # The code is shown only to current managers while the work is open; the worker asks for it on site.
        code = ensure_completion_code(visit) if (current and visit.is_active and visit.status in (
            Visit.NOTVISITED, Visit.INPROGRESS, Visit.RETRY, Visit.SUSPEND)) else ''
        return Response({
            'id': visit.pk,
            'type_name': visit.type.verbose_name or visit.type.title,
            'building': {'id': visit.building_id,
                         'name': visit.building.verbose_name or visit.building.name,
                         'code': visit.building.code},
            'elevators': elevator_rows,
            'status': visit.status,
            'is_pending_request': pending,
            'created_at': visit.datetime_created,
            'due_date': visit.due_date if visit.has_due_date else None,
            'started_at': visit.start_datetime,
            'expert_name': expert_name,
            'report': report,
            'photos': photos,
            'parts': parts,
            'wage': wage,
            'report_version': snapshot.version if snapshot else None,
            'report_captured_at': snapshot.created_at if snapshot else None,
            'completion_code': code,
            'chat_open': current and chat_open(visit),
            'is_current_manager': current,
        })
