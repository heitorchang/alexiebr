from collections import OrderedDict
from django.shortcuts import render
from acct.models import AcctType, Acct, Txn


def index(request):
    atypes = OrderedDict()
    accts = OrderedDict()

    # Initialize dict of account types
    for atype in AcctType.objects.all():
        atypes[atype.id] = atype
        atypes[atype.id].accts = []

    # assign an account to dict of all accounts
    for acct in Acct.objects.filter(user=request.user):
        accts[acct.id] = acct
        accts[acct.id].bal = 0
        
    # alter balances
    for t in Txn.objects.filter(user=request.user):
        dracct = accts[t.debit.id]
        cracct = accts[t.credit.id]
        
        dracct.bal += t.amt * dracct.acctType.sign
        cracct.bal -= t.amt * cracct.acctType.sign

    # place account into its account type's list
    for acct in accts.values():
        atypes[acct.acctType.id].accts.append(acct)
        
    
    return render(request, 'alexieui/index.html',
                  {'atypes': atypes})
