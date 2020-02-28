from django.contrib import admin
from .models import AcctType, Acct, Txn, Preset, HeaderBal

class TxnAdmin(admin.ModelAdmin):
    ordering = ['-id']
    search_fields = ['desc']
    

admin.site.register([AcctType, Acct, Preset, HeaderBal])
admin.site.register(Txn, TxnAdmin)
