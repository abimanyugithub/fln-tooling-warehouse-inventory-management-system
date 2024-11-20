from django.urls import path
from . import views

urlpatterns = [
    path('', views.Dashboard.as_view(), name='dashboard'),
    path('vendor/list', views.VendorListView.as_view(), name='vendor_list'),
    path('vendor/register', views.VendorCreateView.as_view(), name='vendor_create'),
    path('vendor/update/<int:pk>', views.VendorUpdateView.as_view(), name='vendor_update'),
]