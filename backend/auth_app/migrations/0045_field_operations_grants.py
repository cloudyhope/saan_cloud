from django.db import migrations

CAPABILITY = {'GET': 'can_view', 'POST': 'can_create', 'PUT': 'can_update', 'PATCH': 'can_update', 'DELETE': 'can_delete'}

FIELD = (('VisitAssignmentResponseView', 'POST'), ('VisitAssetContextView', 'GET'), ('PromoterVisitChatView', 'GET'),
         ('PromoterVisitChatView', 'POST'), ('PromoterPartRequestView', 'GET'), ('PromoterPartRequestView', 'POST'),
         ('PromoterPartRequestCancelView', 'POST'), ('PromoterEarningsView', 'GET'))
READER = (('VisitAssetContextView', 'GET'), ('AdminVisitFieldOpsView', 'GET'), ('MaintenancePlanListCreateView', 'GET'))
PLANNER = (('MaintenancePlanListCreateView', 'POST'), ('MaintenancePlanDetailView', 'PUT'),
           ('MaintenancePlanDetailView', 'DELETE'))
WAREHOUSE = (('PartRequestListView', 'GET'), ('PartRequestDecisionView', 'POST'))
CLIENT = (('ClientVisitChatView', 'GET'), ('ClientVisitChatView', 'POST'))


def grant_field_operations(apps, schema_editor):
    """Each new endpoint goes to the roles that already hold the closest existing grant."""
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias

    def roles(view_name, methods, scopes):
        # All methods of one call share a capability (PUT and PATCH are both updates).
        return set(role_view.objects.using(alias).filter(
            view_method_name__view_name=view_name, view_method_name__method__in=methods, role__asset_scope__in=scopes,
            **{CAPABILITY[methods[0]]: True}).values_list('role_id', flat=True))

    def grant(role_ids, endpoints):
        for name, method in endpoints:
            view, _ = view_method.objects.using(alias).get_or_create(view_name=name, method=method)
            for role_id in role_ids:
                row = role_view.objects.using(alias).filter(role_id=role_id, view_method_name_id=view.pk).first()
                if row is None:
                    role_view.objects.using(alias).create(role_id=role_id, view_method_name_id=view.pk,
                                                          **{CAPABILITY[method]: True})
                elif not getattr(row, CAPABILITY[method]):
                    setattr(row, CAPABILITY[method], True)
                    row.save(update_fields=[CAPABILITY[method]])

    grant(roles('PromoterVisitStatusChangeAPIView', ('PUT',), ('assigned', 'supervised')), FIELD)
    planners = roles('AdminUpdateVisitView', ('PUT', 'PATCH'), ('project',))
    grant(roles('AdminVisitsListView', ('GET',), ('project',)) | planners, READER)
    grant(planners, PLANNER)
    grant(roles('WareTransactionEzCreateView', ('POST',), ('project',)), WAREHOUSE)
    grant(roles('ClientVisitsAPIView', ('GET',), ('client',)), CLIENT)
    # The service-type settings page (wage, client code) edits types; roles that may create types may edit them.
    grant(roles('VisitTypeListCreateView', ('POST',), ('project',)),
          (('VisitTypeEditsView', 'GET'), ('VisitTypeEditsView', 'PATCH')))


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0044_priority_grants'), ('visit', '0099_field_operations'),
                    ('warehouse', '0015_field_operations')]
    operations = [migrations.RunPython(grant_field_operations, migrations.RunPython.noop)]
