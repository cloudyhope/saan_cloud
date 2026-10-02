"""Atomic transfer of current building management with a preserved history."""
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import authorized_role_views
from visit.models import Building, BuildingClient, Client


class TransferInput(serializers.Serializer):
    building = serializers.IntegerField(min_value=1)
    client = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class BuildingManagementTransferAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        grants = authorized_role_views(request, self, view_name='BuildingClientListCreateAPIView')
        if not grants.filter(role__asset_scope='project').exists():
            return Response({'detail': 'دسترسی انتقال مدیریت مجاز نیست.'}, status=403)
        serializer = TransferInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        project_id = int(request.query_params['p'])
        with transaction.atomic():
            building = Building.objects.select_for_update().filter(
                pk=data['building'], project_id=project_id,
            ).first()
            client = Client.objects.filter(pk=data['client'], project_id=project_id).first()
            if building is None or client is None:
                return Response({'detail': 'ساختمان یا کلاینت در پروژه پیدا نشد.'}, status=404)

            now = timezone.now()
            active = list(BuildingClient.objects.select_for_update().filter(
                building=building, end_at__isnull=True,
            ).order_by('id'))
            if any(link.start_at and link.start_at > now for link in active):
                return Response({'detail': 'برنامه مدیریت آینده باید ابتدا بررسی شود.'}, status=409)
            retained = next((link for link in active if link.client_id == client.pk), None)
            created = retained is None
            ended_ids = []
            for link in active:
                if link.pk == getattr(retained, 'pk', None):
                    continue
                link.end_at = now
                link.ended_by = request.user
                link.end_reason = data['reason']
                link.save(update_fields=['end_at', 'ended_by', 'end_reason'])
                ended_ids.append(link.pk)
            if created:
                retained = BuildingClient.objects.create(
                    building=building, client=client, start_at=now,
                    started_by=request.user, start_reason=data['reason'],
                )
            return Response({
                'building_id': building.pk,
                'client_id': client.pk,
                'management_id': retained.pk,
                'ended_ids': ended_ids,
                'changed': bool(ended_ids or created),
            }, status=201 if created else 200)
