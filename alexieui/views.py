from django.shortcuts import render
from acct.models import AcctType, Acct, Txn


def index(request):
    atypes = AcctType.objects.all()

    for atype in atypes:
        atype.accts = Acct.objects.filter(user=request.user, acctType=atype)
        
    ts = Txn.objects.filter(user=request.user)
    
    return render(request, 'alexieui/index.html',
                  {'atypes': atypes,
                   'ts': ts})
