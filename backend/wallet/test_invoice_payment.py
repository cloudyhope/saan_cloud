"""Payment code ownership, retry, and transaction commit invariants."""
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from config.models import Config
from visit.models import Building, Visit, VisitType
from wallet.models import Account, CodeForWalletInvoice, Wallet, WalletInvoice, WalletTransaction, WalletType


class InvoicePaymentTests(TestCase):
    def setUp(self):
        code_generator = patch('secrets.randbelow', return_value=2345)
        code_generator.start()
        self.addCleanup(code_generator.stop)
        self.project = Project.objects.create(name='Payment project')
        self.other_project = Project.objects.create(name='Payment other project')
        self.client = User.objects.create(username='payer')
        self.other_client = User.objects.create(username='other-payer')
        self.expert = User.objects.create(username='payee')
        role = Role.objects.create(title='Payment client', title_abbreviation='C', asset_scope='client')
        for user in (self.client, self.other_client):
            RoleAssignment.objects.create(user=user, role=role, project=self.project)
            RoleAssignment.objects.create(user=user, role=role, project=self.other_project)
        for name, method, capability in (
            ('WalletInvoiceClientRetrieveView', 'GET', 'can_view'),
            ('WalletInvoiceCodeRequestView', 'POST', 'can_create'),
            ('WalletInvoiceCodeValidateView', 'POST', 'can_create'),
            ('WalletReceiptRetrieve', 'GET', 'can_view'),
            ('WalletGetSignatureView', 'GET', 'can_view'),
        ):
            view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=view, **{capability: True})
        visit_type = VisitType.objects.create(project=self.project, title='Payment visit')
        building = Building.objects.create(project=self.project, code='PAY-BUILDING')
        visit = Visit.objects.create(type=visit_type, building=building, creator=self.expert,
                                     expert=self.expert, is_active=True)
        self.invoice = WalletInvoice.objects.create(
            visit=visit, expert=self.expert, client=self.client, type='CREDIT', amount_rials=100000)
        self.api = APIClient()
        self.api.force_authenticate(self.client)

    def request_code(self, project=None):
        return self.api.post(f'/wallet/invoice/code_request/?p={project or self.project.pk}',
                             {'wallet_invoice': str(self.invoice.pk)}, format='json')

    def validate_code(self, code, value=None, project=None, token=None):
        return self.api.post(f'/wallet/invoice/code_validate/?p={project or self.project.pk}', {
            'id': code.pk, 'wallet_invoice': str(self.invoice.pk),
            'verification_token': token or code.verification_token,
            'code': value or '12345',
        }, format='json')

    def test_request_is_owner_project_open_credit_only_and_code_never_leaks(self):
        response = self.request_code()
        self.assertEqual(response.status_code, 201, response.data)
        self.assertNotIn('code', response.data)
        self.assertNotIn('code_hash', response.data)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        stored = CodeForWalletInvoice.objects.get(wallet_invoice=self.invoice)
        self.assertNotEqual(stored.code_hash, '12345')
        from django.contrib.auth.hashers import check_password
        self.assertTrue(check_password('12345', stored.code_hash))
        self.assertEqual(self.request_code().status_code, 429)
        self.assertEqual(self.request_code(self.other_project.pk).status_code, 404)
        self.api.force_authenticate(self.other_client)
        self.assertEqual(self.request_code().status_code, 404)
        self.api.force_authenticate(self.client)
        self.invoice.type = WalletInvoice.TYPES.CASH
        self.invoice.save()
        self.assertEqual(self.request_code().status_code, 400)
        self.invoice.type = WalletInvoice.TYPES.CREDIT
        self.invoice.is_closed = True
        self.invoice.save()
        self.assertEqual(self.request_code().status_code, 404)

    def test_wrong_code_locks_after_five_attempts_without_closing_invoice(self):
        self.assertEqual(self.request_code().status_code, 201)
        code = CodeForWalletInvoice.objects.get(wallet_invoice=self.invoice)
        wrong = '00000'
        for _ in range(5):
            self.assertEqual(self.validate_code(code, value=wrong).status_code, 400)
        code.refresh_from_db()
        self.assertEqual(code.failed_attempts, 5)
        self.assertEqual(self.validate_code(code).status_code, 400)
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.is_closed)
        self.assertFalse(WalletTransaction.objects.exists())

    def test_wallet_balance_is_own_read_only_and_does_not_expose_signature(self):
        import json
        path = f'/wallet/get_signature/?p={self.project.pk}'
        response = self.api.get(path)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data['wallets'], [])
        self.assertFalse(Account.objects.exists())
        account = Account.objects.create(user=self.client)
        kind = WalletType.objects.create(key='LOCAL', name_fa='اعتبار آزمایشی')
        Wallet.objects.create(account=account, type=kind)
        response = self.api.get(path)
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(len(response.data['wallets']), 1)
        body = json.dumps(response.data)
        for secret in ('signature', 'signature_identifier', 'encryption_key', 'public_address'):
            self.assertNotIn(secret, body)
        self.api.force_authenticate(self.other_client)
        self.assertEqual(self.api.get(path).data['wallets'], [])

    def test_failed_transaction_keeps_invoice_open_and_success_consumes_code_once(self):
        self.assertEqual(self.request_code().status_code, 201)
        code = CodeForWalletInvoice.objects.get(wallet_invoice=self.invoice)
        for key, value in (
            ('QR_CREDIT_FROM_WALLET_TYPE_KEY', 'FROM'),
            ('QR_CREDIT_TO_WALLET_TYPE_KEY', 'TO'),
            ('QR_CREDIT_FROM_LAYER_TYPE_KEY', 'LAYER'),
            ('CREDIT_PAY_BY_QR_TRANSACTION_TYPE_KEY', 'PAY'),
        ):
            Config.objects.create(key=key, value=value)
        with (patch('wallet.core.WalletCore.safe_get_wallet', return_value=SimpleNamespace(public_address='wallet')),
              patch('wallet.core.WalletCore.place_transaction', side_effect=ValueError('Insufficient balance!'))):
            response = self.validate_code(code)
        self.assertEqual(response.status_code, 400, response.data)
        self.invoice.refresh_from_db()
        self.assertFalse(self.invoice.is_closed)
        self.assertEqual(self.invoice.status, WalletInvoice.STATUS.INITIAL)
        with (patch('wallet.core.WalletCore.safe_get_wallet', return_value=SimpleNamespace(public_address='wallet')),
              patch('wallet.core.WalletCore.place_transaction', side_effect=lambda *args, **kwargs: (
                  False, WalletTransaction.objects.create(creator=self.client).pk))):
            response = self.validate_code(code)
        self.assertEqual(response.status_code, 200, response.data)
        self.invoice.refresh_from_db()
        code.refresh_from_db()
        self.assertTrue(self.invoice.is_closed)
        self.assertEqual(self.invoice.status, WalletInvoice.STATUS.PAID)
        self.assertIsNotNone(code.consumed_at)
        self.assertEqual(self.validate_code(code).status_code, 404)
        self.assertEqual(WalletTransaction.objects.count(), 1)
        receipt = self.api.get(f'/wallet/api/v1/wallet_receipt/retrieve/{self.invoice.pk}/?p={self.project.pk}')
        self.assertEqual(receipt.status_code, 200, receipt.data)
        self.api.force_authenticate(self.other_client)
        self.assertEqual(self.api.get(f'/wallet/api/v1/wallet_receipt/retrieve/{self.invoice.pk}/?p={self.project.pk}').status_code, 404)
