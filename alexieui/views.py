from collections import OrderedDict
from django.shortcuts import render, redirect
from acct.models import AcctType, Acct, Txn, Preset


def index(request):
    startdate = request.GET.get('startdate', '2000-01-01')
    enddate = request.GET.get('enddate', '2100-01-01')
        
    atypes = OrderedDict()
    accts = OrderedDict()

    
    # Initialize dict of account types
    for atype in AcctType.objects.all():
        atypes[atype.id] = atype
        atypes[atype.id].accts = []
        atypes[atype.id].bal = 0

        
    # assign an account to dict of all accounts
    for acct in Acct.objects.filter(user=request.user):
        accts[acct.id] = acct
        accts[acct.id].bal = 0

        
    # alter balances
    for t in Txn.objects.filter(user=request.user,
                                date__gte=startdate,
                                date__lte=enddate):
        dracct = accts[t.debit.id]
        cracct = accts[t.credit.id]
        
        dracct.bal += t.amt * dracct.acctType.sign
        cracct.bal -= t.amt * cracct.acctType.sign

        
    # place account into its account type's list
    for acct in accts.values():
        atypes[acct.acctType.id].accts.append(acct)
        atypes[acct.acctType.id].bal += acct.bal
        
    
    return render(request, 'alexieui/index.html',
                  {'startdate': startdate,
                   'enddate': enddate,
                   'atypes': atypes})


def addform(request, presetid):
    preset = Preset.objects.get(user=request.user, id=presetid)
    selectAccts = Acct.objects.filter(user=request.user, acctType=preset.acctTypeSelect)
    
    return render(request, 'alexieui/addform.html',
                  {'presetid': presetid,
                   'preset': preset,
                   'selectAccts': selectAccts})


def add(request):
    if request.method == "POST":
        user = request.user

        addform = request.POST['addform']
        date = request.POST['date']
        desc = request.POST['desc']
        amt = request.POST['amt']
        debit = request.POST['debit']
        credit = request.POST['credit']
        
        return redirect('alexieui:addform', addform)
    else:
        return render(request, 'alexieui/redirect.html',
                      {'msg': "Could not process request."})
        
                    
