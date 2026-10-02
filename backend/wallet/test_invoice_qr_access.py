"""Invoice QR images require the issuing field user's active project membership."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from config.models import Config
from visit.models import Building, Visit, VisitType
from wallet.models import WalletInvoice


class InvoiceQRCodeAccessTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Invoice project')
        self.other_project = Project.objects.create(name='Other invoice project')
        self.expert = User.objects.create(username='qr-expert')
        self.other = User.objects.create(username='qr-other')
        self.role = Role.objects.create(title='Invoice expert', title_abbreviation='P', asset_scope='assigned')
        RoleAssignment.objects.create(user=self.expert, role=self.role, project=self.project)
        create_method = ViewMethod.objects.create(view_name='WalletInvoiceExpertListCreateView', method='POST')
        RoleView.objects.create(role=self.role, view_method_name=create_method, can_create=True)
        kind = VisitType.objects.create(project=self.project, title='Invoice service')
        building = Building.objects.create(project=self.project, code='QR-BUILDING')
        visit = Visit.objects.create(type=kind, building=building, creator=self.expert,
                                     expert=self.expert)
        self.invoice = WalletInvoice.objects.create(visit=visit, expert=self.expert,
                                                     client=self.other, amount_rials=100000)
        Config.objects.create(key='QR_WALLET_INVOICE_BASE_ADDRESS', value='https://example.test/pay/')
        self.api = APIClient()

    def url(self, project=None):
        return f'/wallet/invoice/get_qr_code/{self.invoice.pk}/?p={project or self.project.pk}'

    def test_owner_can_read_png_without_external_logo(self):
        self.api.force_authenticate(self.expert)
        response = self.api.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/png')
        self.assertTrue(response.content.startswith(b'\x89PNG\r\n\x1a\n'))
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_anonymous_other_user_project_and_closed_invoice_are_denied(self):
        self.assertEqual(self.api.get(self.url()).status_code, 401)
        self.api.force_authenticate(self.other)
        self.assertEqual(self.api.get(self.url()).status_code, 404)
        self.api.force_authenticate(self.expert)
        self.assertEqual(self.api.get(self.url(self.other_project.pk)).status_code, 404)
        self.invoice.is_closed = True
        self.invoice.save()
        self.assertEqual(self.api.get(self.url()).status_code, 404)
        self.invoice.is_closed = False
        self.invoice.save()
        RoleAssignment.objects.filter(user=self.expert, project=self.project).update(is_deleted=True)
        self.assertEqual(self.api.get(self.url()).status_code, 404)
        RoleAssignment.objects.filter(user=self.expert, project=self.project).update(is_deleted=False)
        RoleView.objects.filter(role=self.role).update(can_create=False)
        self.assertEqual(self.api.get(self.url()).status_code, 404)

    def test_missing_qr_configuration_fails_without_public_fallback(self):
        self.api.force_authenticate(self.expert)
        Config.objects.filter(key='QR_WALLET_INVOICE_BASE_ADDRESS').delete()
        self.assertEqual(self.api.get(self.url()).status_code, 503)
