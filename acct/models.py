import datetime
from decimal import Decimal

from django.db import models
from django.contrib.auth.models import User


class AcctType(models.Model):
    """Generic, sitewide account types"""
    name = models.CharField(max_length=63)
    sign = models.IntegerField()

    # used for left-to-right ordering in views
    order = models.IntegerField()

    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name


class Acct(models.Model):
    """Owned by a User"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    acctType = models.ForeignKey(AcctType, on_delete=models.CASCADE)
    name = models.CharField(max_length=127)
    budget = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal("0.00"))
    
    class Meta:
        ordering = ['name']

    def __str__(self):
        return "{} ({})".format(self.name, self.user)


class Txn(models.Model):
    """Owned by a User"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    date = models.DateField(default=datetime.date.today)
    desc = models.CharField(max_length=127)
    amt = models.DecimalField(max_digits=22, decimal_places=2)
    debit = models.ForeignKey(Acct, on_delete=models.CASCADE, related_name="debit_txns")
    credit = models.ForeignKey(Acct, on_delete=models.CASCADE, related_name="credit_txns")
    
    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return "{} {} {} ({})".format(self.date, self.desc, self.amt, self.user)

