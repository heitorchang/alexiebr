from django.contrib import admin
from .models import AcctType, Acct, Txn, Preset, HeaderBal, MonthlyRecord

class TxnAdmin(admin.ModelAdmin):
    ordering = ['user', '-id']
    search_fields = ['desc']
    

admin.site.register([AcctType, Acct, Preset, HeaderBal, MonthlyRecord])
admin.site.register(Txn, TxnAdmin)
