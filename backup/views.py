from django.shortcuts import render

# Create your views here.

from backup.models import Backup

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_backups = Backup.objects.all().count()

    # Number of visits to this view, as counted in the session variable.
    num_visits_bu = request.session.get('num_visits_bu', 0)
    request.session['num_visits_bu'] = num_visits_bu + 1

    context = {
        'num_backups': num_backups,
        'num_visits_bu': num_visits_bu,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'backup/index.html', context=context)

from django.views import generic
from datetime import datetime, date, timedelta

class BackupListView(generic.ListView):
    model = Backup
    dates_list = [] 
    idx = 0
    while idx < 4:
        dates_list.append(date.today() - timedelta(days = idx))
        idx += 1

    pi190_records = []
    pi191_records = []
    pi192_records = []
    pi193_records = []
    idx = 0
    for date_o in dates_list:
        row_qs = Backup.objects.filter(pi='PI190', date=date_o) 
        rows_returned = len(row_qs)
        for row in row_qs:
            pi190_records.append({'pi' : row.pi ,'date' : row.date.strftime('%d-%m-%Y'), 'result' : row.result})
        if rows_returned == 0:
            pi190_records.append({'pi' : 'PI190', 'date' : date_o.strftime('%d-%m-%Y'), 'result' : 'F'})
            
        rows_returned = len(row_qs)
        for row in row_qs:
            pi191_records.append({'pi' : row.pi ,'date' : row.date.strftime('%d-%m-%Y'), 'result' : row.result})
        if rows_returned == 0:
            pi191_records.append({'pi' : 'PI190', 'date' : date_o.strftime('%d-%m-%Y'), 'result' : 'F'})
            
        row_qs = Backup.objects.filter(pi='PI192', date=date_o)
        rows_returned = len(row_qs)
        for row in row_qs:
            pi192_records.append({'pi' : row.pi ,'date' : row.date.strftime('%d-%m-%Y'), 'result' : row.result})
        if rows_returned == 0:
            pi192_records.append({'pi' : 'PI190', 'date' : date_o.strftime('%d-%m-%Y'), 'result' : 'F'})
            
        row_qs = Backup.objects.filter(pi='PI193', date=date_o)
        rows_returned = len(row_qs)
        for row in row_qs:
            pi193_records.append({'pi' : row.pi ,'date' : row.date.strftime('%d-%m-%Y'), 'result' : row.result})
        if rows_returned == 0:
            pi193_records.append({'pi' : 'PI190', 'date' : date_o.strftime('%d-%m-%Y'), 'result' : 'F'})
            
    idx = 0
    num = len(dates_list)
    while idx < num:
        dates_list[idx] = dates_list[idx].strftime('%d-%m-%Y')        
        idx += 1
  
    def get_context_data(self, **kwargs):
        context = super(BackupListView, self).get_context_data(**kwargs)
        context['pi190_records'] = self.pi190_records
        context['pi191_records'] = self.pi191_records
        context['pi192_records'] = self.pi192_records
        context['pi193_records'] = self.pi193_records
        context['dates_list'] = self.dates_list
        return context
