"""Retired wallet shortcuts cannot bypass the invoice transaction flow."""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from auth_app.models import Project, Role, RoleAssignment, RoleView, ViewMethod
from wallet.models import WalletTransaction


class LegacyWalletEndpointTests(TestCase):
    def setUp(self):
        self.project = Project.objects.create(name='Legacy wallet project')
        self.staff = User.objects.create(username='legacy-wallet-staff', is_staff=True)
        self.regular = User.objects.create(username='legacy-wallet-regular')
        role = Role.objects.create(title='Legacy wallet role', title_abbreviation='M', asset_scope='project')
        for user in (self.staff, self.regular):
            RoleAssignment.objects.create(user=user, role=role, project=self.project)
        for name, method, capability in (
            ('WalletTransactionListCreateView', 'POST', 'can_create'),
            ('RefTransactionListCreateView', 'POST', 'can_create'),
            ('WalletTransactionLineListCreateView', 'POST', 'can_create'),
            ('TransactionTypeListCreateView', 'GET', 'can_view'),
            ('TransactionTypeListCreateView', 'POST', 'can_create'),
            ('CurrencyListCreateView', 'POST', 'can_create'),
            ('LayerListCreateView', 'POST', 'can_create'),
            ('WalletTypeListCreateView', 'POST', 'can_create'),
            ('AccountListCreateView', 'POST', 'can_create'),
            ('WalletListCreateView', 'POST', 'can_create'),
            ('AllowedTransactionRuleListCreateView', 'POST', 'can_create'),
            ('WalletTransactionLineTypeListCreateView', 'POST', 'can_create'),
            ('AccountEditsView', 'PATCH', 'can_update'),
        ):
            view, _ = ViewMethod.objects.get_or_create(view_name=name, method=method)
            RoleView.objects.create(role=role, view_method_name=view, **{capability: True})
        self.api = APIClient()
        self.api.force_authenticate(self.staff)

    def test_raw_ledger_writes_and_orphaned_shortcuts_are_unreachable(self):
        for path in ('wallet/transaction_type/list_create/',
                     'wallet/currency/list_create/', 'wallet/layer/list_create/',
                     'wallet/wallet_type/list_create/', 'wallet/allowed_transaction_rule/list_create/',
                     'wallet/transaction_line_type/list_create/'):
            response = self.api.post(f'/{path}?p={self.project.pk}', {}, format='json')
            self.assertEqual(response.status_code, 405, (path, response.status_code))
        self.assertFalse(WalletTransaction.objects.exists())
        self.assertEqual(self.api.patch(
            f'/wallet/account/edits/1/?p={self.project.pk}', {'user': self.regular.pk},
            format='json').status_code, 404)
        for path in ('wallet/place_transaction/', 'wallet/transaction/reverse/1/',
                     'wallet/create_for_user/', 'wallet/charge_by_username/',
                     'wallet/account/hyper_list/', 'wallet/api/v1/invoice_store/list/',
                     'wallet/account/list_create/', 'wallet/wallet/list_create/',
                     'wallet/wallet_transaction/list_create/', 'wallet/ref_transaction/list_create/',
                     'wallet/wallet_transaction_line/list_create/'):
            self.assertEqual(self.api.get(f'/{path}?p={self.project.pk}').status_code, 404)

    def test_transaction_types_require_staff_and_project_grant(self):
        path = f'/wallet/transaction_type/list_create/?p={self.project.pk}'
        self.assertEqual(self.api.get(path).status_code, 200)
        self.api.force_authenticate(self.regular)
        self.assertEqual(self.api.get(path).status_code, 403)
