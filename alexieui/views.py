import datetime
from calendar import monthrange
from decimal import Decimal, DivisionByZero
from math import ceil, floor
from collections import OrderedDict
from django.shortcuts import render, redirect
from django.db.models import Q, Sum
from acct.models import AcctType, Acct, Txn, Preset, HeaderBal, MonthlyRecord


def getHeaderBals(request):
    # get all-time header balances

    accts = aggregateAllTxns(request)

    headerBals = OrderedDict()

    # get header bal accts
    for headerBal in HeaderBal.objects.filter(user=request.user):
        headerBals[headerBal.acct.id] = headerBal
        headerBals[headerBal.acct.id].bal = accts[headerBal.acct.id].bal

    loop_method = """
    
    for t in Txn.objects.filter(user=request.user):
        # if t.debit.id in headerAcctIds:
        try:
            dracct = headerBals[t.debit.id]
            dracct.bal += t.amt * dracct.acct.acctType.sign
        except KeyError:
            pass
        
        # if t.credit.id in headerAcctIds:
        try:
            cracct = headerBals[t.credit.id]
            cracct.bal -= t.amt * cracct.acct.acctType.sign
        except KeyError:
            pass
    """

    
    return headerBals


def getAllTimeBal(request, acctid):
    acct = Acct.objects.get(user=request.user, id=acctid)

    loop_method = """
    bal = 0
    for t in Txn.objects.filter(user=request.user):
        if t.debit.id == acctid:
            bal += t.amt * acct.acctType.sign
            
        if t.credit.id == acctid:
            bal -= t.amt * acct.acctType.sign
    """

    agg = aggregateAllTxns(request)
    return agg[acctid].bal

            
def getDateLabel(startdate, enddate):
    if startdate == "2000-01-01":
        return "All time"
    elif startdate[-5:] == "01-01" and enddate[-5:] == "12-31":
        return "Year"
    elif startdate == datetime.date.today().strftime("%Y-%m-01"):
        return "Now"
    else:
        return "Month"


def aggregateAllTxns(request):
    txns = Txn.objects.filter(user=request.user)
    return aggregateTxns(request, txns)


def aggregateTxns(request, txns):
    drs = txns.values('debit').order_by('debit').annotate(total_debits=Sum('amt'))
    crs = txns.values('credit').order_by('credit').annotate(total_credits=Sum('amt'))
    
    accts = OrderedDict()
    signs = {}
    
    for acct in Acct.objects.filter(user=request.user):
        accts[acct.id] = acct
        accts[acct.id].bal = Decimal("0.00")        
        signs[acct.id] = Decimal(acct.acctType.sign)
        
    for dr in drs:
        accts[dr['debit']].bal += dr['total_debits'] * signs[dr['debit']]

    for cr in crs:
        accts[cr['credit']].bal -= cr['total_credits'] * signs[cr['credit']]

    # convert to Decimal
    for acct in accts.values():
        acct.bal = Decimal(acct.bal).quantize(Decimal('1.00'))
    return accts


def aggregateBudget(request, txns):
    drs = txns.values('debit').order_by('debit').annotate(total_debits=Sum('amt'))
    crs = txns.values('credit').order_by('credit').annotate(total_credits=Sum('amt'))
    
    accts = OrderedDict()
    signs = {}
    
    for acct in Acct.objects.filter(user=request.user, budget__gt=0):
        accts[acct.id] = acct
        accts[acct.id].bal = Decimal("0.00")        
        signs[acct.id] = acct.acctType.sign
        
    for dr in drs:
        try:
            accts[dr['debit']].bal += dr['total_debits'] * signs[dr['debit']]
        except KeyError:
            pass

    for cr in crs:
        try:
            accts[cr['credit']].bal -= cr['total_credits'] * signs[cr['credit']]
        except KeyError:
            pass
            
    # convert to Decimal
    for acct in accts.values():
        acct.bal = Decimal(acct.bal).quantize(Decimal('1.00'))
    return accts


def alltxns(request):
    agg = aggregateAllTxns(request)
    return render(request, 'alexieui/alltxns.html',
                  {'agg': agg})


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


    loop_method = """
    
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

    """

    accts = aggregateTxns(request,
                          Txn.objects.filter(user=request.user,
                                             date__gte=startdate,
                                             date__lte=enddate))

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
                   'datelabel': getDateLabel(startdate, enddate),
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


def addfixed(request, debitid, creditid):
    if debitid != 0:
        debitname = Acct.objects.get(user=request.user, id=debitid).name
    else:
        debitname = ""

    if creditid != 0:
        creditname = Acct.objects.get(user=request.user, id=creditid).name
    else:
        creditname = ""

    numtxns = int(request.GET.get('numtxns', 10))
    allAccts = Acct.objects.filter(user=request.user)
    latestTxns = Txn.objects.filter(user=request.user)[:numtxns]

    headerBals = getHeaderBals(request)

    return render(request, 'alexieui/addfixed.html',
                  {'debitid': debitid,
                   'debitname': debitname,
                   'creditid': creditid,
                   'creditname': creditname,
                   'allAccts': allAccts,
                   'headerBals': headerBals,
                   'latestTxns': latestTxns,
                  })


def add(request):
    if request.method == "POST":
        user = request.user

        addform = request.POST['addform']
        fixeddebit = int(request.POST.get('fixeddebit', 0))
        fixedcredit = int(request.POST.get('fixedcredit', 0))
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

        if addform == "fixed":
            return redirect('alexieui:addfixed', fixeddebit, fixedcredit)
        else:
            return redirect('alexieui:addform', addform)
    else:
        return render(request, 'alexieui/redirect.html',
                      {'msg': "Could not process request."})
        

def hist(request):
    user = request.user
    date_now = datetime.datetime.now()
    total_inc = 0
    total_exp = 0
    
    months = MonthlyRecord.objects.filter(user=user, month__gte=datetime.datetime(date_now.year, 1, 1))

    for month in months:
        total_inc += month.income
        total_exp += month.expenses

    grand_total = total_inc - total_exp
    
    return render(request, 'alexieui/hist.html',
                  {'months': months,
                   'total_inc': total_inc,
                   'total_exp': total_exp,
                   'grand_total': grand_total
                   })


def acctdetail(request, acctid):
    acct = Acct.objects.get(user=request.user, id=acctid)
    
    startdate = request.GET.get('startdate', '2000-01-01')
    enddate = request.GET.get('enddate', '2100-01-01')
    numtxns = int(request.GET.get('numtxns', 300))

    drtotal = Decimal('0.00')
    crtotal = Decimal('0.00')
    
    drtxns = []
    crtxns = []

    headerBals = getHeaderBals(request)

    query = Q(user=request.user)
    query.add(Q(date__gte=startdate), Q.AND)
    query.add(Q(date__lte=enddate), Q.AND)
    query.add(Q(debit=acctid) | Q(credit=acctid), Q.AND)
    
    txns = Txn.objects.filter(query).order_by('-date', '-id')[:numtxns]

    for txn in txns:
        if txn.debit == acct:
            drtxns.append(txn)
            drtotal += txn.amt

        if txn.credit == acct:
            crtxns.append(txn)
            crtotal += txn.amt

    if drtotal == crtotal:
        currentBal = Decimal('0.00')
    else:
        currentBal = acct.acctType.sign * (drtotal - crtotal)
    currentBal = Decimal(currentBal).quantize(Decimal('1.00'))
    
    return render(request, 'alexieui/acctdetail.html',
                  {'acct': acct,
                   'startdate': datetime.datetime.strptime(startdate, "%Y-%m-%d"),
                   'enddate': datetime.datetime.strptime(enddate, "%Y-%m-%d"),
                   'datelabel': getDateLabel(startdate, enddate),
                   'alltimebal': getAllTimeBal(request, acctid),
                   'headerBals': headerBals,
                   'numtxns': numtxns,
                   'drtotal': drtotal,
                   'crtotal': crtotal,
                   'currentBal': currentBal,
                   'drtxns': drtxns,
                   'crtxns': crtxns})


def adj(request, acctid):
    acct = Acct.objects.get(user=request.user, id=acctid)
        
    # get all-time balance
    loop_method = """
    acct.bal = Decimal('0.00')

    for t in Txn.objects.filter(user=request.user):
        if t.debit.id == acctid:
            acct.bal += t.amt * acct.acctType.sign
            
        if t.credit.id == acctid:
            acct.bal -= t.amt * acct.acctType.sign
    """

    agg = aggregateAllTxns(request)
    acct.bal = agg[acct.id].bal
    
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
    startdate = request.GET.get('startdate', datetime.date.today().strftime("%Y-%m-01"))
    enddate = request.GET.get('enddate', '2100-01-01')
        
    spent_total = 0
    budget_total = 0

    total_remaining = 0
    excess_total = 0

    loop_method = """
    
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
    """

    accts = aggregateBudget(request,
                            Txn.objects.filter(user=request.user,
                                               date__gte=startdate,
                                               date__lte=enddate))
    
    # update spent_total
    for acct in accts.values():
        spent_total += acct.bal

        if acct.budget > 1:
            budget_total += acct.budget
        
        # compute percentages and remaining
        try:
            if acct.budget == 1:
                acct.percent = -1
            else:
                acct.percent = ceil(ceil(acct.bal) / acct.budget * 100)
        except DivisionByZero:
            acct.percent = 0
            
        acct.remaining = floor(acct.budget - acct.bal)
        if acct.remaining < 0:
            excess_total += abs(acct.remaining)
            
            acct.remaining = "({:,})".format(abs(acct.remaining)).replace(",", ".")
        else:
            if acct.budget > 1:
                total_remaining += acct.remaining
            acct.remaining = "{:,}".format(acct.remaining).replace(",", ".")

    try:
        total_percent = ceil(spent_total / budget_total * 100)
    except DivisionByZero:
        total_percent = 0
        
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
                   'datelabel': getDateLabel(startdate, enddate),
                   'spent_total': spent_total,
                   'budget_total': budget_total,
                   'total_percent': total_percent,
                   'total_remaining': total_remaining,
                   'excess_total': excess_total,
                   'bdg_exc': int(budget_total + excess_total),
                   'percentelapsed': percentelapsed,
                   'headerBals': headerBals})


def search(request):
    q = request.GET.get('q', '')
    numtxns = int(request.GET.get('numtxns', 100))
    startdate = request.GET.get('startdate', '2000-01-01')
    enddate = request.GET.get('enddate', '2100-01-01')
    
    if len(q) > 0:
        msg = "Results for {} ({} transactions)".format(q, numtxns)
        txns = Txn.objects.filter(user=request.user,
                                  desc__icontains=q,
                                  date__gte=startdate,
                                  date__lte=enddate)[:numtxns]
    else:
        msg = ""
        txns = []
        
    return render(request, 'alexieui/search.html',
                  {'txns': txns,
                   'q': q,
                   'startdate': startdate,
                   'enddate': enddate,
                   'msg': msg})
