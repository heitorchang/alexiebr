from django.contrib import admin
from .models import AcctType, Acct, Txn, Preset

admin.site.register([AcctType, Acct, Txn, Preset])
