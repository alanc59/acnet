from django.shortcuts import render

# Create your views here.

from backup.models import Backup

def index(request):
    """View function for home page of site."""

    # Generate counts of some of the main objects
    num_backups = Backup.objects.all().count()

    context = {
        'num_backups': num_backups,
    }

    # Render the HTML template index.html with the data in the context variable
    return render(request, 'backup/index.html', context=context)

from django.views import generic

class BackupListView(generic.ListView):
    model = Backup
 
    dates = Backup.objects.values('date').distinct().order_by('-date') 

    pi190_records = Backup.objects.filter(pi='PI190').order_by('-date')
    pi191_records = Backup.objects.filter(pi='PI191').order_by('-date')
    pi192_records = Backup.objects.filter(pi='PI192').order_by('-date')
    pi193_records = Backup.objects.filter(pi='PI193').order_by('-date')

    def get_context_data(self, **kwargs):
        context = super(BackupListView, self).get_context_data(**kwargs)
        context['pi190_records'] = self.pi190_records
        context['pi191_records'] = self.pi191_records
        context['pi192_records'] = self.pi192_records
        context['pi193_records'] = self.pi193_records
        context['dates'] = self.dates
        return context
    
    
