from decimal import Decimal
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from .models import AcctType, Acct, Txn


class AcctTypeTest(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='heitor',
                                        email='heitorpontual@gmail.com',
                                        password='secret')

        
    def test_acct_type_creation(self):
        at = AcctType.objects.create(name='assets',
                                     sign=1, order=1)
        self.assertEqual(len(AcctType.objects.all()), 1)


    def test_acct_creation(self):
        at = AcctType.objects.create(name='assets',
                                     sign=1, order=1)

        a = Acct.objects.create(user=self.user,
                                acctType=at,
                                name='bank',
                                budget=Decimal("0.00"))

        self.assertEqual(len(Acct.objects.all()), 1)


    def test_txn_creation(self):
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
                                  date=date(2020, 3, 1),
                                  desc="transfer",
                                  amt=Decimal("100.00"),
                                  debit=wallet,
                                  credit=bank)
        
        self.assertEqual(len(Txn.objects.all()), 1)
        
