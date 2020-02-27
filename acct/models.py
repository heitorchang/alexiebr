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
        ordering = ['-id']

    def __str__(self):
        return "{} {} {} ({})".format(self.date, self.desc, self.amt, self.user)


class Preset(models.Model):
    """Convenience view with fixed account and select values from an AcctType.
    Defaults to fixed credit (source for expenses).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    name = models.CharField(max_length=63)
    isDebit = models.BooleanField(default=False)
    fixedAcct = models.ForeignKey(Acct, on_delete=models.CASCADE)
    acctTypeSelect = models.ForeignKey(AcctType, on_delete=models.CASCADE)

    class Meta:
        ordering = ['isDebit', 'fixedAcct', 'acctTypeSelect']

    def __str__(self):
        return "{} ({})".format(self.name, self.user)
