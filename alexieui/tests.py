from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from acct.models import AcctType, Acct, Txn


class HomePageTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_superuser(username='admin',
                                                  email='admin@alexiebr.com',
                                                  password='secret')

        
    def test_redirects_to_login(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 302)

        
    def test_uses_home_template(self):
        self.client.login(username='admin', password='secret')
        
        response = self.client.get('/')
        self.assertTemplateUsed(response, 'alexieui/index.html')
        

    def test_shows_zero_balance(self):
        self.client.login(username='admin', password='secret')

        at = AcctType.objects.create(name='assets',
                                     sign=1, order=1)
        
        bank = Acct.objects.create(user=self.user,
                                   acctType=at,
                                   name='bank',
                                   budget=Decimal("0.00"))

        response = self.client.get('/')
        self.assertContains(response, "0,00")


    def test_recent_txn_affects_balance(self):
        self.client.login(username='admin', password='secret')

        at = AcctType.objects.create(name='assets',
                                     sign=1, order=1)
        
        bank = Acct.objects.create(user=self.user,
                                   acctType=at,
                                   name='bank',
                                   budget=Decimal("0.00"))

        wallet = Acct.objects.create(user=self.user,
                                     acctType=at,
                                     name='wallet',
                                     budget=Decimal("0.00"))

        xfer = Txn.objects.create(user=self.user,
                                  date=date.today(),
                                  desc="transfer",
                                  amt=Decimal("123.00"),
                                  debit=wallet,
                                  credit=bank)

        response = self.client.get('/')
        self.assertContains(response, "123,00")


    def test_old_txn_does_not_appear(self):
        self.client.login(username='admin', password='secret')

        at = AcctType.objects.create(name='assets',
                                     sign=1, order=1)
        
        bank = Acct.objects.create(user=self.user,
                                   acctType=at,
                                   name='bank',
                                   budget=Decimal("0.00"))

        wallet = Acct.objects.create(user=self.user,
                                     acctType=at,
                                     name='wallet',
                                     budget=Decimal("0.00"))

        xfer = Txn.objects.create(user=self.user,
                                  date=date(2001, 9, 9),
                                  desc="transfer",
                                  amt=Decimal("123.00"),
                                  debit=wallet,
                                  credit=bank)

        response = self.client.get('/')
        self.assertNotContains(response, "123,00")
