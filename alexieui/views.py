import datetime
from calendar import monthrange
from decimal import Decimal
from math import ceil, floor
from collections import OrderedDict
from django.shortcuts import render, redirect
from acct.models import AcctType, Acct, Txn, Preset, HeaderBal


def getHeaderBals(request):
    # get all-time header balances
    headerBals = OrderedDict()
    headerAcctIds = set()

    # get header bal accts
    for headerBal in HeaderBal.objects.filter(user=request.user):
        headerBals[headerBal.acct.id] = headerBal
        headerBals[headerBal.acct.id].bal = Decimal("0.00")
        headerAcctIds.add(headerBal.acct.id)
    
    for t in Txn.objects.filter(user=request.user):
        if t.debit.id in headerAcctIds:
            dracct = headerBals[t.debit.id]
            dracct.bal += t.amt * dracct.acct.acctType.sign
            
        if t.credit.id in headerAcctIds:
            cracct = headerBals[t.credit.id]
            cracct.bal -= t.amt * cracct.acct.acctType.sign

    return headerBals


def getAllTimeBal(request, acctid):
    bal = 0
    acct = Acct.objects.get(user=request.user, id=acctid)

    for t in Txn.objects.filter(user=request.user):
        if t.debit.id == acctid:
            bal += t.amt * acct.acctType.sign
            
        if t.credit.id == acctid:
            bal -= t.amt * acct.acctType.sign
    return bal

            
def getDateLabel(startdate):
    if startdate == "2000-01-01":
        return "All time"
    elif startdate == datetime.date.today().strftime("%Y-%m-01"):
        return "Now"
    else:
        return "Month"

    
def index(request):
    if not request.user.is_authenticated:
        return redirect('admin:index')
    
    startdate = request.GET.get('startdate', datetime.date.today().strftime("%Y-%m-01"))
    enddate = request.GET.get('enddate', '2100-01-01')
        
    atypes = OrderedDict()
    accts = OrderedDict()
    
    # Initialize dict of account types
    for atype in AcctType.objects.all():
        atypes[atype.id] = atype
        atypes[atype.id].accts = []
        atypes[atype.id].bal = Decimal("0.00")

        
    # assign an account to dict of all accounts
    for acct in Acct.objects.filter(user=request.user):
        accts[acct.id] = acct
        accts[acct.id].bal = Decimal("0.00")

        
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
        

    # get presets
    presets = Preset.objects.filter(user=request.user)

    headerBals = getHeaderBals(request)

    return render(request, 'alexieui/index.html',
                  {'startdate': datetime.datetime.strptime(startdate, "%Y-%m-%d"),
                   'enddate': datetime.datetime.strptime(enddate, "%Y-%m-%d"),
                   'datelabel': getDateLabel(startdate),
                   'presets': presets,
                   'headerBals': headerBals,
                   'atypes': atypes})


def addform(request, presetid):
    if presetid != 0:
        preset = Preset.objects.get(user=request.user, id=presetid)
        selectAccts = Acct.objects.filter(user=request.user, acctType=preset.acctTypeSelect)
    else:
        preset = None
        selectAccts = None

    numtxns = int(request.GET.get('numtxns', 10))
        
    allAccts = Acct.objects.filter(user=request.user)
    latestTxns = Txn.objects.filter(user=request.user)[:numtxns]

    headerBals = getHeaderBals(request)
    
    return render(request, 'alexieui/addform.html',
                  {'presetid': presetid,
                   'numtxns': numtxns,
                   'preset': preset,
                   'headerBals': headerBals,
                   'allAccts': allAccts,
                   'selectAccts': selectAccts,
                   'latestTxns': latestTxns})


def add(request):
    if request.method == "POST":
        user = request.user

        addform = request.POST['addform']
        date = request.POST['date']
        desc = request.POST['desc']
        amt = request.POST['amt'].replace(',', '.')
        debit = Acct.objects.get(user=user, id=int(request.POST['debit']))
        credit = Acct.objects.get(user=user, id=int(request.POST['credit']))

        Txn.objects.create(user=user,
                           date=date,
                           desc=desc,
                           amt=amt,
                           debit=debit,
                           credit=credit)
        
        return redirect('alexieui:addform', addform)
    else:
        return render(request, 'alexieui/redirect.html',
                      {'msg': "Could not process request."})
        
                    
def hist(request):
    return render(request, 'alexieui/hist.html')


def acctdetail(request, acctid):
    acct = Acct.objects.get(user=request.user, id=acctid)
    
    startdate = request.GET.get('startdate', '2000-01-01')
    enddate = request.GET.get('enddate', '2100-01-01')
    numtxns = int(request.GET.get('numtxns', 100))

    drtxns = []
    crtxns = []
    totaltxns = 0
    
    for txn in Txn.objects.filter(user=request.user,
                                  date__gte=startdate,
                                  date__lte=enddate).order_by('-date', '-id'):
        if totaltxns >= numtxns:
            break
        
        if txn.debit == acct:
            drtxns.append(txn)
            totaltxns += 1

        if txn.credit == acct:
            crtxns.append(txn)
            totaltxns += 1
    

    return render(request, 'alexieui/acctdetail.html',
                  {'acct': acct,
                   'startdate': datetime.datetime.strptime(startdate, "%Y-%m-%d"),
                   'enddate': datetime.datetime.strptime(enddate, "%Y-%m-%d"),
                   'datelabel': getDateLabel(startdate),
                   'alltimebal': getAllTimeBal(request, acctid),
                   'numtxns': numtxns,
                   'drtxns': drtxns,
                   'crtxns': crtxns})


def adj(request, acctid):
    acct = Acct.objects.get(user=request.user, id=acctid)
    acct.bal = Decimal('0.00')
        
    # get all-time balance
    for t in Txn.objects.filter(user=request.user):
        if t.debit.id == acctid:
            acct.bal += t.amt * acct.acctType.sign
            
        if t.credit.id == acctid:
            acct.bal -= t.amt * acct.acctType.sign
            
    if request.method == "POST":
        diff = Decimal(request.POST.get('newbal', '0.00').replace(',', '.')) - acct.bal
        sign = acct.acctType.sign
        
        if diff < 0:
            diff_sign = -1
        else:
            diff_sign = 1

        if diff_sign * sign == 1:
            debit = acct.id
            credit = int(request.POST.get('otheracct', '-1'))
        else:
            debit = int(request.POST.get('otheracct', '-1'))
            credit = acct.id

        date = datetime.date.today().strftime("%Y-%m-%d")
        desc = request.POST.get('desc', '[auto] adj')

        Txn.objects.create(user=request.user,
                           date=date,
                           desc=desc,
                           amt=abs(diff),
                           debit=Acct.objects.get(user=request.user, id=debit),
                           credit=Acct.objects.get(user=request.user, id=credit))
                           
        return redirect("alexieui:acctdetail", acctid)
    
    else:
        allaccts = Acct.objects.filter(user=request.user)
        
        return render(request, 'alexieui/adjform.html',
                      {'acct': acct,
                       'allaccts': allaccts})


def budget(request):
    accts = OrderedDict()
    acctids = set()
    startdate = request.GET.get('startdate', datetime.date.today().strftime("%Y-%m-01"))
    enddate = request.GET.get('enddate', '2100-01-01')
        
    spent_total = 0
    budget_total = 0
    
    # assign an account to dict of all accounts
    for acct in Acct.objects.filter(user=request.user, budget__gt=0):
        accts[acct.id] = acct
        accts[acct.id].bal = Decimal("0.00")
        acctids.add(acct.id)
        budget_total += acct.budget


    # alter balances
    for t in Txn.objects.filter(user=request.user,
                                date__gte=startdate,
                                date__lte=enddate):
        if t.debit.id in acctids:
            dracct = accts[t.debit.id]
            dracct.bal += t.amt * dracct.acctType.sign

        if t.credit.id in acctids:
            cracct = accts[t.credit.id]
            cracct.bal -= t.amt * cracct.acctType.sign


    # update spent_total
    for acct in accts.values():
        spent_total += acct.bal

        # compute percentages and remaining
        acct.percent = ceil(acct.bal / acct.budget * 100)
        acct.remaining = floor(acct.budget - acct.bal)
        if acct.remaining < 0:
            acct.remaining = "({:,})".format(abs(acct.remaining)).replace(",", ".")
        else:
            acct.remaining = "{:,}".format(acct.remaining).replace(",", ".")
    
    total_percent = ceil(spent_total / budget_total * 100)
    total_remaining = floor(budget_total - spent_total)
    if total_remaining < 0:
        total_remaining = "({:,})".format(abs(total_remaining)).replace(",", ".")
    else:
        total_remaining = "{:,}".format(total_remaining).replace(",", ".")

    # percent of month elapsed
    mytoday = datetime.date.today()
    thisyear = int(mytoday.strftime("%Y"))
    thismonth = int(mytoday.strftime("%m"))
    thisday = int(mytoday.strftime("%d"))

    lastday = monthrange(thisyear, thismonth)[1]
    percentelapsed = ceil((thisday - 1) / lastday * 100)
    
    headerBals = getHeaderBals(request)

    return render(request, 'alexieui/budget.html',
                  {'accts': accts,
                   'startdate': datetime.datetime.strptime(startdate, "%Y-%m-%d"),
                   'enddate': datetime.datetime.strptime(enddate, "%Y-%m-%d"),
                   'datelabel': getDateLabel(startdate),
                   'spent_total': spent_total,
                   'budget_total': budget_total,
                   'total_percent': total_percent,
                   'total_remaining': total_remaining,
                   'percentelapsed': percentelapsed,
                   'headerBals': headerBals})
