"""Scoped personal acknowledgement and feedback for finished client visits."""
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.permissions import DeleteCreateUpdateGetPermission, authorized_role_views
from visit.management import client_visible_visits
from visit.models import Client, ClientVisitFeedback, Visit


class FeedbackInput(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5, required=False)
    note = serializers.CharField(max_length=1000, allow_blank=True, required=False)
    received = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if not attrs or (set(attrs) == {'received'} and attrs['received'] is False):
            raise serializers.ValidationError('امتیاز، توضیح یا تأیید دریافت لازم است.')
        return attrs


class ClientVisitFeedbackAPIView(APIView):
    permission_classes = [DeleteCreateUpdateGetPermission]

    def scoped_visit(self, request, id):
        grants = authorized_role_views(request, self)
        if not grants.filter(role__asset_scope='client').exists():
            return None
        project_id = int(request.query_params['p'])
        clients = Client.objects.filter(project_id=project_id, userclient__user=request.user)
        visits = Visit.objects.filter(type__project_id=project_id,
                                      building__project_id=project_id, is_deleted=False)
        return get_object_or_404(client_visible_visits(visits, clients), pk=id)

    @staticmethod
    def output(feedback):
        if not feedback:
            return {'rating': None, 'note': '', 'received_at': None}
        return {'rating': feedback.rating, 'note': feedback.note,
                'received_at': feedback.received_at}

    def get(self, request, id):
        visit = self.scoped_visit(request, id)
        if visit is None:
            return Response({'detail': 'دسترسی به بازخورد خدمت مجاز نیست.'}, status=403)
        feedback = ClientVisitFeedback.objects.filter(visit=visit, user=request.user).first()
        return Response(self.output(feedback))

    def post(self, request, id):
        visit = self.scoped_visit(request, id)
        if visit is None:
            return Response({'detail': 'دسترسی به بازخورد خدمت مجاز نیست.'}, status=403)
        if visit.status not in (Visit.COMPLETED, Visit.APPROVED):
            raise serializers.ValidationError('ثبت بازخورد پس از پایان خدمت ممکن است.')
        payload = FeedbackInput(data=request.data)
        payload.is_valid(raise_exception=True)
        with transaction.atomic():
            feedback, created = ClientVisitFeedback.objects.select_for_update().get_or_create(
                visit=visit, user=request.user)
            values = payload.validated_data
            if created and not (values.get('rating') or values.get('note') or values.get('received')):
                raise serializers.ValidationError('امتیاز، توضیح یا تأیید دریافت لازم است.')
            if values.get('received') is False and feedback.received_at:
                raise serializers.ValidationError('تأیید دریافت ثبت‌شده قابل بازگشت نیست.')
            if values.get('received') and not feedback.received_at:
                feedback.received_at = timezone.now()
            if 'rating' in values:
                feedback.rating = values['rating']
            if 'note' in values:
                feedback.note = values['note']
            feedback.save()
        return Response(self.output(feedback), status=201 if created else 200)
