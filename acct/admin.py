from django.contrib import admin
from .models import AcctType, Acct, Txn

admin.site.register([AcctType, Acct, Txn])
