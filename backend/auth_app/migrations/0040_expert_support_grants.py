from django.db import migrations


def grant_expert_support(apps, schema_editor):
    role_model = apps.get_model('auth_app', 'Role')
    role_view = apps.get_model('auth_app', 'RoleView')
    view_method = apps.get_model('auth_app', 'ViewMethod')
    alias = schema_editor.connection.alias
    visit_views = view_method.objects.using(alias).filter(
        view_name__in=('PromoterVisitsAPIView', 'SupervisionVisitsListView'),
        method='GET', roleview__can_view=True,
    ).values('roleview__role_id')
    roles = role_model.objects.using(alias).filter(
        asset_scope__in=('assigned', 'supervised'), pk__in=visit_views,
    )
    for role in roles.iterator():
        for name in ('ExpertSupportTicketsAPIView', 'ExpertSupportTicketDetailAPIView'):
            for method, capability in (('GET', 'can_view'), ('POST', 'can_create')):
                view, _ = view_method.objects.using(alias).get_or_create(view_name=name, method=method)
                if not role_view.objects.using(alias).filter(role_id=role.pk, view_method_name_id=view.pk).exists():
                    role_view.objects.using(alias).create(
                        role_id=role.pk, view_method_name_id=view.pk, **{capability: True})


class Migration(migrations.Migration):
    dependencies = [('auth_app', '0039_otp_consumed_at_otp_failed_attempts_alter_otp_otp')]
    operations = [migrations.RunPython(grant_expert_support, migrations.RunPython.noop)]
