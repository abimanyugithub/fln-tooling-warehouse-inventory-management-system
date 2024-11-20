from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, CreateView, UpdateView
from .models import Vendor
from .forms import VendorForm

# Create your views here.
class Dashboard(TemplateView):
    template_name = 'ToolingApp/base/dashboard.html'

class VendorListView(ListView):
    template_name = 'ToolingApp/crud_vendor/list.html'
    model = Vendor
    context_object_name = 'list_vendor'
    ordering = ['nama_vendor', '-is_active']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        for item in context['list_vendor']:
            item.status =  'Available' if item.is_active else 'Unavailable'
        context['fields'] = {'nama_vendor': 'Supplier', 'status': 'Status'}
        return context
    
class VendorCreateView(CreateView):
    template_name = 'ToolingApp/crud_vendor/create_or_update.html'
    model = Vendor
    form_class = VendorForm
    success_url = reverse_lazy('vendor_list')

class VendorUpdateView(UpdateView):
    template_name = 'ToolingApp/crud_vendor/create_or_update.html'
    model = Vendor
    form_class = VendorForm
    success_url = reverse_lazy('vendor_list')
