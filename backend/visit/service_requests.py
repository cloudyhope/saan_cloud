"""Validate a complete service request and persist it atomically with retry protection."""
import hashlib
import json
import uuid
from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from visit.asset_access import AssetAccess
from visit.models import BuildingElevator, ServiceRequestSubmission, Visit, VisitType


class ServiceBuildingInput(serializers.Serializer):
    building = serializers.IntegerField(min_value=1)
    elevators = serializers.ListField(child=serializers.IntegerField(min_value=1), allow_empty=False)

    def validate_elevators(self, values):
        if len(set(values)) != len(values):
            raise serializers.ValidationError('آسانسور تکراری انتخاب شده است.')
        return values


class ServiceRequestInputSerializer(serializers.Serializer):
    buildings = ServiceBuildingInput(many=True, allow_empty=False)
    type = serializers.PrimaryKeyRelatedField(queryset=VisitType.objects.all())
    request_key = serializers.UUIDField(required=False)

    def validate_buildings(self, values):
        if len({row['building'] for row in values}) != len(values):
            raise serializers.ValidationError('هر ساختمان باید فقط یک بار در درخواست باشد.')
        elevator_ids = [pk for row in values for pk in row['elevators']]
        if len(set(elevator_ids)) != len(elevator_ids):
            raise serializers.ValidationError('یک آسانسور نمی‌تواند در چند ساختمان انتخاب شود.')
        return values


def submit_service_request(request, view, values):
    access = AssetAccess(request, view)
    if not access.scopes.intersection({'client', 'project'}):
        raise PermissionDenied('ثبت درخواست خدمت نیازمند دسترسی کلاینت یا مدیریت پروژه است.')
    visit_type = values['type']
    if visit_type.project_id != access.project_id or not visit_type.is_active:
        raise serializers.ValidationError({'type': 'نوع خدمت در پروژه انتخاب‌شده فعال نیست.'})
    rows = values['buildings']
    canonical = {'type': visit_type.pk, 'buildings': sorted([
        {'building': row['building'], 'elevators': sorted(row['elevators'])} for row in rows
    ], key=lambda row: row['building'])}
    fingerprint = hashlib.sha256(json.dumps(canonical, sort_keys=True).encode()).hexdigest()
    key = values.get('request_key') or uuid.uuid4()

    with transaction.atomic():
        # Validate every row before creating any visit or idempotency record.
        for index, row in enumerate(rows):
            if not access.buildings.filter(pk=row['building']).exists():
                raise serializers.ValidationError({'buildings': {index: {
                    'building': 'ساختمان در محدوده مدیریت یا دسترسی این پروژه نیست.',
                }}})
            matches = BuildingElevator.objects.filter(
                building_id=row['building'], elevator_id__in=row['elevators'],
                elevator__in=access.elevators,
            ).values_list('elevator_id', flat=True).distinct()
            if set(matches) != set(row['elevators']):
                raise serializers.ValidationError({'buildings': {index: {
                    'elevators': 'آسانسورها باید متعلق به همین ساختمان و پروژه باشند.',
                }}})
        submission, created = ServiceRequestSubmission.objects.get_or_create(
            creator=request.user, project_id=access.project_id, request_key=key,
            defaults={'payload_hash': fingerprint},
        )
        submission = ServiceRequestSubmission.objects.select_for_update().get(pk=submission.pk)
        if submission.payload_hash != fingerprint:
            raise serializers.ValidationError({'request_key': 'این شناسه قبلاً برای درخواست دیگری استفاده شده است.'})
        if not created:
            return submission, True
        for row in rows:
            # Pending company review: creation does not dispatch an active expert visit.
            visit = Visit.objects.create(
                creator=request.user, type=visit_type, building_id=row['building'],
                status=Visit.NOTVISITED, is_active=False,
            )
            visit.elevator.set(row['elevators'])
            submission.visits.add(visit)
        return submission, False
