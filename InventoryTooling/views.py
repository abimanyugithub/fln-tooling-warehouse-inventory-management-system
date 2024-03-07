import math

from django.conf import settings
from django.shortcuts import render, redirect
from django.views.generic import ListView, CreateView, UpdateView, DetailView, TemplateView, DeleteView, FormView
from django.views import View
from .models import ModelProduct, ModelLocation, ModelTempProdLoc, ModelTransaction, ModelUserUID, ModelTempPickCart
from django.urls import reverse, reverse_lazy
from django.db.models import Q, Sum, Count, Case, When, Min, Max, F, ExpressionWrapper, fields
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseNotFound
from django.forms import formset_factory, ModelForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger, InvalidPage
from datetime import datetime, date
from django.utils import timezone
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash, get_user_model
from .forms import CustomUserCreationForm, UpdatePasswordForm, SetPasswordForm
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.forms import SetPasswordForm
import json
import os
import gzip
from django.contrib.staticfiles.storage import staticfiles_storage
from django.contrib.staticfiles.finders import find
from django.http import JsonResponse
from datetime import datetime, timedelta
from django.templatetags.static import static

title = "Tooling - "

# select option
options_assign = {'P': 'PRIMARY', 'R': 'RESERVE'}
options_area = {'BL': 'BLOW', 'IN': 'INJECTION', 'CH': 'CHEMICAL (MTC)', 'CE': 'CONSUMABLE ELECTRICAL',
                'CM': 'CONSUMABLE MECHANICAL', 'VA': 'VACUUM'}
options_storage = {'RK': 'RACK', 'FR': 'FLOOR'}
options_is_active = {True: 'ACTIVE', False: 'BLOCK'}
options_dept = {'IT': 'IT', 'MAINTENANCE': 'MAINTENANCE', }
options_adjustment = {'PCK': 'PICKING', 'STO': 'STOCK COUNT', 'TTB': 'RECEIVING', 'API': 'ADJ. INVENTORY'}
options_stats_loc = {'FL': 'FREE', 'UL': 'USED', 'HU': 'HELD', 'DL': 'DELETED'}
options_lvl_sto = {'S': 'SURPLUS', 'B': 'SAFETY', 'C': 'CRITICAL', 'E': 'EMPTY'}
options_unit = {'BOX': 'BOX', 'CANS': 'CANS', 'KG': 'KG', 'MTR': 'MTR', 'PACK': 'PACK', 'PCS': 'PCS', 'ROLL': 'ROLL',
                'SET': 'SET', 'UNIT': 'UNIT'}
options_adjust = {'AO': 'OUT', 'AI': 'IN'}
options_lvl_uid = {'ADM': 'ADMINISTRATOR', 'STD': 'STANDARD'}
options_trans_type = {'TTB': 'RECEIVING', 'PCK': 'PICKING', 'STO': 'STOCK COUNT', 'API': 'ADJ. INVENTORY',
                      'PM': 'PALLET MOVE'}
options_chk_sto = {'CHK': 'CHECKED', 'PND': 'PENDING'}

# Create your views here.
#   Custom 404-page view
class Template404View(TemplateView):
    template_name = "404.html"
    title = title + 'Not Found'


class Template403View(TemplateView):
    template_name = "403.html"
    title = title + 'Not Found'


# view as superuser
class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser


# view as staff or superuser
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_staff


class PageTitleViewMixin:
    # title = ""

    def get_title(self):
        return self.title

    def get_header(self):
        return self.header

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.get_title()
        context['header'] = self.get_header()
        return context


# register & login logout sign up
class SignupPageView(SuperuserRequiredMixin, PageTitleViewMixin, CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("ViewUser")
    template_name = "registration/signup_view.html"
    title = title + 'Register'
    header = 'Create an Account'

    def form_valid(self, form):
        messages.success(self.request, "Account added successfully.")
        return super().form_valid(form)


# cek username exists htmx
def check_username(request):
    user_check = request.POST.get('username')

    if user_check:
        if get_user_model().objects.filter(username=user_check).exists():
            return HttpResponse(
                '<div class="text-danger ml-1 px-5">This username has been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        else:
            return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
    else:
        return HttpResponse()


# cek password validation
DEFAULT_PASSWORD_LIST_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'common-passwords.txt')
with open(DEFAULT_PASSWORD_LIST_PATH, 'r') as f:
    common_passwords_lines = f.readlines()
list_passwords = {p.strip() for p in common_passwords_lines}


# cek password htmx
def check_password(request):
    password = request.POST.get('password1')
    confirm_password = request.POST.get('password2')
    if password and confirm_password:
        if password != confirm_password:
            return HttpResponse(
                '<div class="text-danger h6 small px-5">Please make sure your passwords match.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        elif len(password) < 8:  # must contain at least 8 characters
            return HttpResponse(
                '<div class="text-danger h6 small px-5">Your password must contain at least 8 characters.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        elif password.isdigit():  # password can't be entirely numeric.
            return HttpResponse(
                "<div class='text-danger h6 small px-5'>Your password can't be entirely numeric.</div><script>$('#btnSave').attr('disabled', 'disabled')</script>")
        elif password.lower().strip() in list_passwords:  # Your password can't be a commonly used password.
            return HttpResponse(
                "<div class='text-danger h6 small px-5'>Your password can't be a commonly used password.</div><script>$('#btnSave').attr('disabled', 'disabled')</script>")
        else:
            return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


# cek username login exists htmx
def check_username_login(request):
    user_check = request.POST.get('username')
    password = request.POST.get('password1')
    user = authenticate(username=user_check, password=password)

    if user_check and password:
        if user is not None:
            if user.is_active:
                return HttpResponse(
                    '<div class="text-success ml-1 small px-4">You are authorized, please click login.</div><script>$("#btnSave").removeAttr("disabled")</script>')
            else:
                return HttpResponse(
                    '<div class="text-danger ml-1 small px-4">Inactive user.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        else:
            return HttpResponse(
                '<div class="text-danger ml-1 small px-4">Invalid username or password.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    else:
        return HttpResponse()


# proses sudah di handle di check_username_login
class LoginPageView(PageTitleViewMixin, LoginView):
    template_name = 'registration/signin_view.html'
    title = title + 'Login'
    header = 'Sign In'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            username = request.POST.get('username')
            password = request.POST.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return redirect(self.request.META.get('HTTP_REFERER'))
                else:
                    return HttpResponseRedirect(reverse('LoginPageView'))
            else:
                return HttpResponseRedirect(reverse('LoginPageView'))

        return redirect('Dashboard')


class LogoutPageView(LogoutView):
    def get(self, request):
        logout(request)
        return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)


# htmx check change password
def check_change_password(request):
    if request.method == 'POST':
        form = UpdatePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            return HttpResponse(
                '<div class="text-success ml-1 small px-4">Congratulations! Please click change.</div><script>$("#btnSave").removeAttr("disabled")</script>')
        else:
            return HttpResponse(
                '<div class="text-danger ml-1 small px-4">Password change failed.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    else:
        form = UpdatePasswordForm(user=request.user, data=request.POST)


class ChangePassPageView(StaffRequiredMixin, PageTitleViewMixin, FormView):
    form_class = UpdatePasswordForm
    title = title + 'Change Password'
    header = 'Change Password'
    template_name = 'registration/pass_change.html'
    model = User

    def get_form_kwargs(self):
        kwargs = super(ChangePassPageView, self).get_form_kwargs()
        kwargs['user'] = self.request.user
        if self.request.method == 'POST':
            kwargs['data'] = self.request.POST
        return kwargs

    def form_valid(self, form):
        form.save()
        update_session_auth_hash(self.request, form.user)
        messages.success(self.request, "Your password was successfully updated!.")
        return HttpResponseRedirect(settings.LOGOUT_REDIRECT_URL)


class ResetPassPageView(SuperuserRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'registration/pass_reset.html'
    title = title + 'Account'
    header = 'Reset Password'
    context_object_name = 'user_account'
    model = User
    fields = ['username']

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            username = request.POST.get('username')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password1')
            if password1 == password2:
                this_user = User.objects.get(username=username)
                this_user.set_password(password2)
                this_user.save()
                messages.success(self.request,
                                 f"The password for Account <strong>{this_user.first_name}</strong> <br> was successfully updated!.")

                return HttpResponseRedirect(reverse('ViewUser'))
            else:
                return redirect(self.request.META.get('HTTP_REFERER'))
        else:
            return redirect(self.request.META.get('HTTP_REFERER'))


class ViewUser(SuperuserRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'registration/user_list.html'
    title = title + 'User'
    header = title + ' / ' + 'Accounts List'
    context_object_name = 'user_account'
    model = User

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = User.objects.all()
        active = total.filter(is_active=True)
        blocked = total.filter(is_active=False)

        if total:
            context['total'] = total.count()
            context['active_percentage'] = 100 * active.count() / total.count()
            context['active'] = active.count()
            context['blocked_percentage'] = 100 * blocked.count() / total.count()
            context['blocked'] = blocked.count()
            context['options_is_active'] = options_is_active
        return context


class EditUser(SuperuserRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'registration/user_edit.html'
    title = title + 'Account'
    header = title + ' / ' + 'Update'
    model = User
    fields = ['is_superuser', 'is_staff', 'is_active']
    context_object_name = 'user_account'
    success_url = reverse_lazy('ViewUser')

    def form_valid(self, form):

        if form.has_changed():
            messages.success(self.request,
                             f"Account <strong>{self.object.first_name}</strong> <br> updated successfully.")
        else:
            # jika tidak ada yang dirubah
            return redirect(self.request.META.get('HTTP_REFERER'))
        return super().form_valid(form)


# sampai sini ya view user account & registration

# rfid uid
class ViewUserUID(SuperuserRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'registration/user_uid/uid_user_list.html'
    title = title + 'User'
    header = title + ' / ' + 'RFID Tags List'
    context_object_name = 'uid_list'
    model = ModelUserUID

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = ModelUserUID.objects.filter(usernm__isnull=False)
        active = ModelUserUID.objects.filter(status=True)
        blocked = ModelUserUID.objects.filter(status=False)
        if total:
            context['total'] = total.count()
            context['active'] = active.count()
            context['active_percentage'] = 100 * active.count() / total.count()
            context['blocked'] = blocked.count()
            context['blocked_percentage'] = 100 * blocked.count() / total.count()
            context['options_lvl_uid'] = options_lvl_uid
            context['options_is_active'] = options_is_active
        return context


def check_user_uid(request):
    uid = request.POST.get('uid')
    username = request.POST.get('usernm')

    # error jika uid and username sudah ada & status aktif
    if ModelUserUID.objects.filter(uid=uid, usernm=username, status=True).exists():
        return HttpResponse(
            '<div class="text-danger ml-1">Already exist.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    # error jika uid status aktif
    elif ModelUserUID.objects.filter(uid=uid, status=True).exists():
        return HttpResponse(
            '<div class="text-danger ml-1">UID exist.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    # error jika username status aktif
    elif ModelUserUID.objects.filter(usernm=username, status=True).exists():
        return HttpResponse(
            '<div class="text-danger ml-1">Username exist.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class AddUserUID(SuperuserRequiredMixin, PageTitleViewMixin, CreateView):
    template_name = 'registration/user_uid/uid_user_add.html'
    title = title + 'PICC User'
    header = title + ' / ' + 'Create PICC User'
    model = ModelUserUID
    context_object_name = 'data'
    fields = ['uid', 'nik', 'nm_krywn', 'usernm', 'dept', 'level']
    success_url = reverse_lazy('ViewUserUID')

    def form_valid(self, form):
        messages.success(self.request, "User added successfully.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_dept'] = options_dept
        context['options_lvl_uid'] = options_lvl_uid
        return context


class EditUserUID(SuperuserRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'registration/user_uid/uid_user_edit.html'
    title = title + 'PICC User'
    header = title + ' / ' + 'Update RFID User'
    model = ModelUserUID
    fields = ['dept', 'status', 'level']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_dept'] = options_dept
        context['options_lvl_uid'] = options_lvl_uid
        context['options_is_active'] = options_is_active
        return context

    def form_valid(self, form):
        if form.has_changed():
            messages.add_message(self.request, messages.SUCCESS,
                                 f"User <strong>{self.object.nm_krywn}</strong> <br> updated successfully.")
        else:
            # jika tidak ada yang dirubah
            return redirect(self.request.META.get('HTTP_REFERER'))
        return super().form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy("ViewUserUID")


class ViewNavbar(TemplateView):
    template_name = 'includes/navbar.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Display primary / reserve location
        total_location = ModelLocation.objects.exclude(status='DL')
        context['total_location'] = total_location.count()
        return context


class RefreshPage(View):
    template_name = 'dashboard.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, {'data': data})


class Dashboard(PageTitleViewMixin, TemplateView):
    template_name = 'dashboard.html'
    title = title + 'Dashboard'
    header = title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ini variable
        # Display primary / reserve location
        total_location = ModelLocation.objects.exclude(status='DL')
        total_primary = total_location.filter(assign='P').exclude(status='DL')
        total_reserve = total_location.filter(assign='R').exclude(status='DL')
        #   qty location
        context['total_location'] = total_location.count()
        context['total_primary'] = total_primary.count()
        context['total_reserve'] = total_reserve.count()
        #   percentage location
        context['total_primary_used'] = total_primary.filter(status='UL').count()
        context['total_primary_free'] = total_primary.filter(status='FL').count()
        context['total_reserve_used'] = total_reserve.filter(Q(status='UL') | Q(status='HU')).count()
        context['total_reserve_free'] = total_reserve.filter(status='FL').count()

        if total_location.exists():
            try:
                # primary percent free & used
                context['percent_total_primary_used'] = 100 * total_primary.filter(
                    status='UL').count() / total_primary.count()
                context['percent_total_primary_free'] = 100 * total_primary.filter(
                    status='FL').count() / total_primary.count()
                # reserve percent free & used
                context['percent_total_reserve_used'] = 100 * total_reserve.filter(
                    status='UL').count() / total_reserve.count()
                context['percent_total_reserve_free'] = 100 * total_reserve.filter(
                    status='FL').count() / total_reserve.count()
            except ZeroDivisionError:
                pass

        #   qty product
        total_product = ModelProduct.objects.all()
        total_active = total_product.filter(is_active=True)
        total_block = total_product.filter(is_active=False)
        context['total_product'] = total_product.count()
        context['total_active'] = total_active.count()
        context['total_block'] = total_block.count()

        # produk dengan / tdk dgn reserve
        total_with_reserve = ModelTempProdLoc.objects.values('prod_code').annotate(htg=Count('prod_code')).filter(
            htg__gte=2)
        total_not_reserve = ModelTempProdLoc.objects.values('prod_code').annotate(htg=Count('prod_code')).filter(
            no_loc_id__isnull=False, htg=1)
        context['total_with_reserve'] = total_with_reserve.count()
        context['total_not_reserve'] = total_not_reserve.count()

        if total_product.exists():
            try:
                # active product
                context['percent_total_active'] = 100 * ModelProduct.objects.filter(
                    is_active=True).count() / total_product.count()
                # block product
                context['percent_total_block'] = 100 * ModelProduct.objects.filter(
                    is_active=False).count() / total_product.count()
                # within reserve
                context['percent_total_with_reserve'] = 100 * total_with_reserve.count() / (
                        total_with_reserve.count() + total_not_reserve.count())
                # without reserve
                context['percent_total_not_reserve'] = 100 * total_not_reserve.count() / (
                        total_with_reserve.count() + total_not_reserve.count())

            except ZeroDivisionError:
                pass

        # cart masih pending
        cart_pending = ModelTempPickCart.objects.filter(prod_code__isnull=False)
        context['cart_pending'] = cart_pending.count()

        # received & picked in current month
        today = datetime.now()
        incoming = ModelTransaction.objects.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"), trans_type="TTB",
                                                   date_created__year=today.year, date_created__month=today.month)
        incoming1 = ModelTransaction.objects.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"), trans_type="TTB",
                                                    date_created__year=today.year,
                                                    date_created__month=today.month).aggregate(my_sum=Sum('qty_adj'))
        sum_in = incoming1['my_sum'] if incoming1['my_sum'] is not None else 0
        context['incoming1'] = sum_in

        outgoing = ModelTransaction.objects.filter(trans_type="PCK", date_created__year=today.year,
                                                   date_created__month=today.month)
        outgoing1 = ModelTransaction.objects.filter(trans_type="PCK", date_created__year=today.year,
                                                    date_created__month=today.month).aggregate(
            my_sum=ExpressionWrapper(Sum('qty_adj'), output_field=fields.FloatField()))
        sum_out = int(abs(outgoing1['my_sum'])) if outgoing1['my_sum'] is not None else 0
        context['outgoing1'] = sum_out

        # display level stock product
        surplus = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_max'))
        safety = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_min'), total__lte=F('prod_code__stock_max'))
        # stok sama dengan / dibawah min (kecuali stock qty 0)
        critical = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=0, total__lte=F('prod_code__stock_min'))
        # empty stock
        empty = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total=0)

        context['surplus'] = surplus.count()
        context['safety'] = safety.count()
        context['critical'] = critical.count()
        context['empty'] = empty.count()

        # sto checked location
        #   last STO Date
        context['last_sto'] = ModelLocation.objects.filter(sto_check='CHK').order_by('-date_created').first()
        check_none = ModelLocation.objects.filter(sto_check__isnull=True)
        checked_ok = ModelLocation.objects.filter(sto_check='CHK')
        checked = ModelLocation.objects.filter(sto_check__isnull=False)
        checked_pending = ModelLocation.objects.filter(sto_check='PND')  # check pending
        # checked
        context['checked'] = checked.count()

        #   stock count location
        if checked.exists():
            # check ok
            context['percent_checked_ok'] = 100 * checked_ok.count() / total_location.count()
            # check pending
            context['percent_checked_pending'] = 100 * checked_pending.count() / total_location.count()
            # none
            context['percent_check_none'] = 100 * check_none.count() / total_location.count()
            # sto progress
            context['percent_sto'] = (100 * (
                    checked_ok.count() + checked_pending.count())) / total_location.count()  # jumlah semua lokasi kecuali lokasi yang di delete

        try:
            # percent incoming by qty
            context['percent_incoming'] = 100 * sum_in / (sum_in + sum_out)
            # percent outgoing by qty
            context['percent_outgoing'] = 100 * sum_out / (sum_in + sum_out)
            context['msg_traffic'] = '* Percentage above threshold based on quantities.'
            # Display last picked
            last_picked = ModelTransaction.objects.filter(trans_type='PCK', adj_type='AO').order_by('-date_created')[:3]
            context['last_picked'] = last_picked

            # Display demand (pengambilan part) by PCK AO sort by this month
            demand_times = ModelTransaction.objects.values('prod_code_id').annotate(
                num_item=Count('prod_code_id')).filter(
                trans_type="PCK", adj_type="AO", date_created__year=today.year,
                date_created__month=today.month).order_by('-num_item')[:3]
            context['demand_times'] = demand_times

            demand_qty = ModelTransaction.objects.values('prod_code_id').annotate(qty_sum=Sum('qty_adj')).filter(
                trans_type="PCK", adj_type="AO", date_created__year=today.year,
                date_created__month=today.month).order_by('qty_sum')[:3]
            context['demand_qty'] = demand_qty
            return context
        except ZeroDivisionError:
            return context

        except Exception as e:
            return context

        return context


class ViewLabel(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'report/label_view.html'
    title = title + 'Report'
    header = title + ' / ' + 'Create Label Location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        return context


class ResultLabel(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'report/label_result.html'
    title = title + 'Report'
    header = title + ' / ' + 'Create Label Location'
    model = ModelLocation
    context_object_name = 'location'

    def get_queryset(self):
        location1 = self.request.GET.get('no_loc1')
        location2 = self.request.GET.get('no_loc2')
        assign = self.request.GET.get('assign')

        if assign:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2, assign=assign).exclude(
                status="DL")
        else:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2).exclude(status="DL")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['tb_temp'] = ModelTempProdLoc.objects.filter(no_loc_id__isnull=False)
        return context


# sampai sini ya view label

# (HTMX) cek location exists
def check_location(request):
    location = request.POST.get('no_loc')

    if ModelLocation.objects.filter(no_loc=location).exists():
        return HttpResponse(
            '<div class="text-danger ml-1">Location has been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class ViewLocation(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'inventory/location/loc_list.html'
    title = title + 'Location'
    header = title + ' / ' + 'Locations List'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = ModelLocation.objects.exclude(status="DL").count()
        free = ModelLocation.objects.filter(status="FL").count()
        used = ModelLocation.objects.filter(status="UL").count()
        held = ModelLocation.objects.filter(status="HU").count()

        if total:
            context['free'] = free
            context['free_percentage'] = 100 * free / total
            context['used'] = used
            context['used_percentage'] = 100 * used / total
            context['held'] = held
            context['held_percentage'] = 100 * held / total
            context['options_assign'] = options_assign
            context['options_storage'] = options_storage
            context['options_area'] = options_area
            context['options_stats_loc'] = options_stats_loc
        return context


# pagination datatable ajax
def ListLocation(request):
    # Get parameters from DataTables request
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    draw = int(request.GET.get('draw', 1))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')

    # Map column index to model field names
    columns_map = {
        0: 'no_loc',
        1: 'part_number',   # bug sort part_number
        2: 'part_desc',  # bug sort part_desc
        3: 'assign',
        4: 'storage',
        5: 'area',
        6: 'status',
        # Add mappings for other columns as needed
    }

    # Determine the field to order by
    order_field = columns_map.get(order_column_index, 'no_loc')  # Default order column is sto_check

    # Apply sorting direction
    if order_direction == 'desc':
        order_field = '-' + order_field  # Prepend '-' for descending order

    queryset = ModelLocation.objects.order_by(order_field, 'no_loc')
    part_location_dict = {part.no_loc_id: (part.prod_code_id, part.prod_code.prod_desc) for part in ModelTempProdLoc.objects.all()}

    # Reverse the key-value pairs
    reversed_options_assign = {value: key for key, value in options_assign.items()}
    reversed_options_area = {value: key for key, value in options_area.items()}
    reversed_options_storage = {value: key for key, value in options_storage.items()}
    reversed_options_stats_loc = {value: key for key, value in options_stats_loc.items()}

    # Merge the reversed dictionaries into a single mapping dictionary
    mapping = {}
    mapping.update(reversed_options_assign)
    mapping.update(reversed_options_area)
    mapping.update(reversed_options_storage)
    mapping.update(reversed_options_stats_loc)

    # Function for case-insensitive replacement
    def replace_mapped_terms(term):
        for key, value in mapping.items():
            term = term.replace(key, value)
            term = term.replace(key.capitalize(), value)  # Replace capitalized version
            term = term.replace(key.upper(), value)  # Replace uppercase version
            term = term.replace(key.lower(), value)  # Replace lowercase version
        return term

    # Replace mapped terms in the search value
    search_value = replace_mapped_terms(search_value)

    # Filtering based on search value
    if search_value:
        queryset = queryset.filter(Q(no_loc__icontains=search_value) | Q(assign=search_value) | Q(
            sto_check=search_value) | Q(storage=search_value) | Q(
            area=search_value) | Q(status=search_value))

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)

    # Serialize paginated data
    data = [
        {'noloc': obj.no_loc,
         'assgn': obj.assign,
         'stor': obj.storage,
         'area': obj.area,
         'stats': obj.status,
         'part_number': part_location_dict.get(obj.no_loc, ('', 0))[0],
         'part_desc': part_location_dict.get(obj.no_loc, ('', 0))[1],
         } for i, obj in enumerate(page_obj)]

    return JsonResponse({
        'data': data,
        'length': length,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


class AddLocation(StaffRequiredMixin, PageTitleViewMixin, CreateView):
    template_name = 'inventory/location/loc_add.html'
    title = title + 'Location'
    header = title + ' / ' + 'Add Single Location'
    model = ModelLocation
    fields = ['no_loc', 'assign', 'storage', 'area']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last_add_location = ModelLocation.objects.order_by('-date_created').first()
        total = ModelLocation.objects.exclude(status="DL").count()
        primary = ModelLocation.objects.filter(assign="P").exclude(status="DL").count()
        reserve = ModelLocation.objects.filter(assign="R").exclude(status="DL").count()
        context['options_assign'] = options_assign
        context['options_area'] = options_area
        context['options_storage'] = options_storage

        if total:
            context['last_add_location'] = last_add_location
            context['primary'] = primary
            context['primary_percentage'] = 100 * primary / total
            context['reserve'] = reserve
            context['reserve_percentage'] = 100 * reserve / total
        return context

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request,
                         f"Location <strong>{self.object.no_loc.upper()}</strong> <br> added successfully.")
        return redirect(self.request.META.get('HTTP_REFERER'))


def check_any_location(request):
    locations = request.POST.getlist('no_loc')
    assignments = request.POST.getlist('assign')
    storages = request.POST.getlist('storage')
    areas = request.POST.getlist('area')

    assign = ['P', 'R', 'p', 'r']
    storage = ['FR', 'RK']
    area = ['BL', 'IN', 'CH', 'CE', 'CM', 'VA']

    #   duplicate exists
    if len(locations) != len(set(locations)):
        return HttpResponse(
            '<div class="text-danger ml-1">Duplicates location found.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    #   jika assign tidak ada di db
    elif not any(value in assign for value in assignments):
        return HttpResponse(
            '<div class="text-danger ml-1">Assign location not allowed.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    #   jika storage tidak ada di db
    elif not any(value in storage for value in storages):
        return HttpResponse(
            '<div class="text-danger ml-1">Storage area not allowed.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    #   jika area tidak ada di db
    elif not any(value in area for value in areas):
        return HttpResponse(
            '<div class="text-danger ml-1">Tooling part area not allowed.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    #   jika location ada di db
    elif any(ModelLocation.objects.filter(no_loc=location).exists() for location in locations):
        return HttpResponse(
            '<div class="text-danger ml-1">One or more locations have been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


# tambah banyak lokasi
class FormLocation(ModelForm):
    class Meta:
        model = ModelLocation
        fields = ['no_loc', 'assign', 'storage', 'area']


class AddLocationMass(SuperuserRequiredMixin, PageTitleViewMixin, CreateView):
    template_name = 'inventory/location/loc_mass_add.html'
    title = title + 'Location'
    header = title + ' / ' + 'Add Multiple Locations'
    model = ModelLocation
    form_class = FormLocation

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['options_storage'] = options_storage
        context['options_area'] = options_area

        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            a = request.POST.getlist('no_loc')
            b = request.POST.getlist('assign')
            c = request.POST.getlist('storage')
            d = request.POST.getlist('area')

            combine = min([len(a), len(b), len(c), len(d)])
            for i in range(combine):
                formset = self.form_class({
                    'no_loc': a[i],
                    'assign': b[i],
                    'storage': c[i],
                    'area': d[i],
                })
                # check whether it's valid:
                if formset.is_valid():
                    formset.save()
                    # notif nya jadi banyak mengikuti looping
                messages.success(self.request, f'{a[i]}:{b[i]}')
        return redirect("AddLocationMass")


class EditLocation(StaffRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'inventory/location/loc_edit.html'
    title = title + 'Location'
    header = title + ' / ' + 'Edit Location'
    model = ModelLocation
    fields = ['assign', 'storage', 'area']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['options_area'] = options_area
        context['options_storage'] = options_storage
        return context

    def form_valid(self, form):
        if form.is_valid():
            # cek jika ada field yang di rubah
            if form.has_changed():
                form.save()
                messages.success(self.request,
                                 f"Location <strong>{self.object.no_loc}</strong> <br> updated successfully.")
            else:
                # jika tidak ada yang dirubah
                return redirect(self.request.META.get('HTTP_REFERER'))
        return redirect(self.request.META.get('HTTP_REFERER'))


class UpdateStatusLocation(StaffRequiredMixin, UpdateView):
    model = ModelLocation
    fields = ['status']

    def form_valid(self, form):
        free_location = ModelLocation.objects.filter(no_loc=self.object.no_loc, status="FL")
        delete_location = ModelLocation.objects.filter(no_loc=self.object.no_loc, status="DL")
        held_location = ModelLocation.objects.filter(no_loc=self.object.no_loc, status="HU")
        used_location = ModelLocation.objects.filter(no_loc=self.object.no_loc, status="UL")
        if free_location:
            self.object = form.save()
            messages.success(self.request, f"Location <strong>{self.object.no_loc}</strong> <br> successfully deleted.")
        elif delete_location:
            self.object = form.save()
            messages.success(self.request,
                             f"Location <strong>{self.object.no_loc}</strong> <br> successfully restored.")
        elif held_location:
            self.object = form.save()
            messages.success(self.request, f"Location <strong>{self.object.no_loc}</strong> <br> successfully used.")
        elif used_location:
            self.object = form.save()
            messages.success(self.request, f"Location <strong>{self.object.no_loc}</strong> <br> successfully held.")
        return redirect(self.request.META.get('HTTP_REFERER'))


# sampai sini location view

# product
class ViewProduct(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'inventory/product/prod_list.html'
    title = title + 'Part'
    header = title + ' / ' + 'Parts List'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = ModelProduct.objects.all().count()
        active = ModelProduct.objects.filter(is_active=True).count()
        block = ModelProduct.objects.filter(is_active=0).count()
        if total:
            context['total'] = total
            context['active'] = active
            context['active_percentage'] = 100 * active / total
            context['block'] = block
            context['block_percentage'] = 100 * block / total
            context['options_is_active'] = options_is_active
            context['options_unit'] = options_unit
        return context


# pagination datatable ajax
def ListProduct(request):
    # Get parameters from DataTables request
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    draw = int(request.GET.get('draw', 1))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')

    # Map column index to model field names
    columns_map = {
        0: 'prod_code_id',
        1: 'prod_code__prod_desc',
        2: 'prod_code__unit',
        3: 'prod_code__pack_size',
        4: 'total',
        5: 'prod_code__is_active',
        # Add mappings for other columns as needed
    }

    # Determine the field to order by
    order_field = columns_map.get(order_column_index, 'prod_code')  # Default order column is sto_check

    # Apply sorting direction
    if order_direction == 'desc':
        order_field = '-' + order_field  # Prepend '-' for descending order

    queryset = ModelTempProdLoc.objects.filter(Q(no_loc__assign='P') | Q(no_loc__isnull=True)).order_by(order_field, 'prod_code')
    summary = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty'))

    # Filtering based on search value
    if search_value:
        queryset = queryset.filter(Q(prod_code__prod_code__icontains=search_value) | Q(prod_code__prod_desc__icontains=search_value) | Q(
            prod_code__unit=search_value) | Q(prod_code__pack_size__icontains=search_value) | Q(prod_code__is_active__icontains=search_value))

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)

    # Serialize paginated data
    data = [
        {'prod': obj.prod_code_id,
         'desc': obj.prod_code.prod_desc,
         'unt': obj.prod_code.unit,
         'pack': obj.prod_code.pack_size,
         'stats': obj.prod_code.is_active,
         'total': next((item['total'] for item in summary if item['prod_code'] == obj.prod_code_id), 0)  # Get total_qty from summary
         } for i, obj in enumerate(page_obj)
    ]

    return JsonResponse({
        'data': data,
        'length': length,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


# (HTMX) cek location exists
def check_product(request):
    product = request.POST.get('prod_code')
    min = request.POST.get('stock_min')
    max = request.POST.get('stock_max')

    if ModelProduct.objects.filter(prod_code=product).exists():
        return HttpResponse(
            '<div class="text-danger ml-1">Part number has been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    if int(min) > int(max):
        return HttpResponse(
            '<div class="text-danger ml-1">Min. stock value cannot be more than max. stock value.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    elif int(min) < int(max) or int(min) == int(max):
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class FormCreateProduct(ModelForm):
    class Meta:
        model = ModelProduct
        fields = ['prod_code', 'prod_desc', 'unit', 'supplier', 'pack_size', 'stock_min', 'stock_max', 'l_time_days', 'img']


class AddProduct(StaffRequiredMixin, PageTitleViewMixin, CreateView):
    template_name = 'inventory/product/prod_add.html'
    title = title + 'Part'
    header = title + ' / ' + 'Add Single Part'
    model = ModelProduct
    form_class = FormCreateProduct

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_unit'] = options_unit
        return context

    def get_success_url(self, **kwargs):
        # beri value 'new' pada remark bahwa produk harus new line
        ModelTempProdLoc.objects.create(prod_code_id=self.object.prod_code, remark="NEW")
        messages.add_message(self.request, messages.SUCCESS,
                             f"Part No. <strong>{self.object.prod_code.upper()}</strong> <br> added successfully.")
        return reverse('DetailProduct', kwargs={'pk': self.object.pk})


def check_any_product(request):
    products = request.POST.getlist('prod_code')
    mins = request.POST.getlist('stock_min')
    maxs = request.POST.getlist('stock_max')

    #  duplicate exists
    if len(products) != len(set(products)):
        return HttpResponse(
            '<div class="text-danger ml-1">Duplicates part found.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    #   jika product ada di db
    elif any(ModelProduct.objects.filter(prod_code=product).exists() for product in products):
        return HttpResponse(
            '<div class="text-danger ml-1">One or more parts have been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    #   jika stock min lebih besar dari stock max
    elif any(int(min) > int(max) for min, max in zip(mins, maxs)):
        return HttpResponse(
            '<div class="text-danger ml-1">Min. stock value cannot be more than max. stock value.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class FormProduct(ModelForm):
    class Meta:
        model = ModelProduct
        fields = ['prod_code', 'prod_desc', 'pack_size', 'supplier', 'stock_min', 'stock_max', 'l_time_days', 'unit']


class AddProductMass(SuperuserRequiredMixin, PageTitleViewMixin, CreateView):
    template_name = 'inventory/product/prod_mass_add.html'
    title = title + 'Part'
    header = title + ' / ' + 'Add Multiple Parts'
    model = ModelProduct
    form_class = FormProduct

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            a = request.POST.getlist('prod_code')
            b = request.POST.getlist('prod_desc')
            c = request.POST.getlist('pack_size')
            d = request.POST.getlist('supplier')
            e = request.POST.getlist('stock_min')
            f = request.POST.getlist('stock_max')
            g = request.POST.getlist('l_time_days')
            h = request.POST.getlist('uom')

            combine = min([len(a), len(b), len(c), len(d), len(e), len(f), len(g), len(h)])
            for i in range(combine):
                formset = self.form_class({
                    'prod_code': a[i],
                    'prod_desc': b[i],
                    'pack_size': c[i],
                    'supplier': d[i],
                    'stock_min': e[i],
                    'stock_max': f[i],
                    'l_time_days': g[i],
                    'unit': h[i],
                })
                # check whether it's valid:
                if formset.is_valid():
                    formset.save()
                    ModelTempProdLoc.objects.create(prod_code_id=a[i], remark="NEW")
                    # notif nya jadi banyak mengikuti jumlah input
                messages.success(self.request, f'{a[i]}:{b[i]}')
        return redirect("AddProductMass")


# (HTMX) cek min max form product edit
def check_minmax(request):
    min = request.POST.get('stock_min')
    max = request.POST.get('stock_max')

    if int(min) > int(max):
        return HttpResponse('<div class="text-danger ml-1">Min. stock value cannot be more than max. stock value.</div>'
                            '<script>$("#btnSave").attr("disabled", "disabled")</script>')
    elif int(min) < int(max) or int(min) == int(max):
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class EditProduct(StaffRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'inventory/product/prod_edit.html'
    title = title + 'Part'
    header = title + ' / ' + 'Edit Part'
    model = ModelProduct
    fields = ['prod_desc', 'supplier', 'pack_size', 'stock_min', 'stock_max', 'l_time_days', 'is_active', 'unit', 'img']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_is_active'] = options_is_active
        # jika produk tidak memiliki lokasi bisa di block, begitupun sebaliknya
        context['no_location'] = ModelTempProdLoc.objects.filter(prod_code_id=self.object.pk, no_loc_id__isnull=True)
        context['options_unit'] = options_unit
        return context

    def form_valid(self, form):
        if form.has_changed():
            instance = form.save(commit=False)
            new_image = form.cleaned_data['img']
            instance.img = new_image
            instance.save()
            messages.success(self.request,
                             f"Part No. <strong>{self.object.prod_code}</strong> <br> updated successfully.")
        else:
            # jika tidak ada yang dirubah
            return redirect(self.request.META.get('HTTP_REFERER'))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('DetailProduct', kwargs={'pk': self.object.pk})


class DetailProduct(StaffRequiredMixin, PageTitleViewMixin, DetailView):
    template_name = 'inventory/product/prod_detail.html'
    title = title + 'Part'
    header = title + ' / ' + 'Detail'
    model = ModelProduct
    context_object_name = 'data'


# sampai sini ya product view

# assignment location (newline)
class ViewNewline(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'inventory/newline/newline_list.html'
    title = title + 'Assign Location'
    header = title
    model = ModelTempProdLoc
    context_object_name = 'newline'

    def get_queryset(self):
        return ModelTempProdLoc.objects.filter(Q(no_loc_id__assign="P") | Q(no_loc_id__isnull=True),
                                               prod_code__is_active=True, qty=0).order_by('prod_code_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # produk tanpa lokasi
        non_loc = ModelTempProdLoc.objects.filter(no_loc_id__isnull=True, prod_code__is_active=True).count()
        # produk dengan lokasi primary
        wth_loc = ModelTempProdLoc.objects.filter(no_loc_id__assign="P", no_loc_id__isnull=False,
                                                  prod_code__is_active=True).count()
        mysum = ModelTempProdLoc.objects.values('prod_code').annotate(total_qty=Sum('qty')).filter(total_qty=0,
                                                                                                   prod_code__is_active=True)

        if non_loc or wth_loc:
            context['total'] = int(non_loc) + int(wth_loc)
            context['non_loc'] = non_loc
            context['non_loc_percentage'] = 100 * non_loc / (int(non_loc) + int(wth_loc))
            context['wth_loc'] = wth_loc
            context['wth_loc_percentage'] = 100 * wth_loc / (int(non_loc) + int(wth_loc))
            context['mysum'] = mysum
        return context


def check_any_newline(request):
    locations = request.POST.getlist('no_loc')
    products = request.POST.getlist('prod_code')
    c = request.POST.getlist('qty')

    combined_values = locations + products
    used_location = any(
        ModelLocation.objects.filter(no_loc=location, assign="P").exclude(status="FL").exists() for location in
        locations)
    exists_product = all(ModelTempProdLoc.objects.filter(prod_code=product, prod_code__is_active=True, remark="NEW",
                                                         no_loc__isnull=True).exists() for product in products)

    #   duplicate locations & products exists
    if len(combined_values) != len(set(combined_values)):
        return HttpResponse(
            '<div class="text-danger ml-1">Duplicates found.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    # jika lokasi not found
    elif not all(ModelLocation.objects.filter(no_loc=location).exists() for location in locations):
        return HttpResponse(
            '<div class="text-danger ml-1">One or more locations not found.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    #   jika lokasi primary status not free
    elif not all(
            ModelLocation.objects.filter(no_loc=location, assign="P", status="FL").exists() for location in locations):
        return HttpResponse(
            '<div class="text-danger ml-1">One or more locations have been used in other parts.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    #   cek jika product tidak memenuhi syarat input di tb temp (product, new, loc = null)
    elif not exists_product:
        return HttpResponse(
            '<div class="text-danger ml-1">One or more parts already exists in assigned location.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class FormNewline(ModelForm):
    class Meta:
        model = ModelTempProdLoc
        fields = ['no_loc', 'prod_code', 'qty']


class AddNewlineMass(SuperuserRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'inventory/newline/newline_mass_add.html'
    title = title + 'Assign Location'
    header = title + ' / ' + 'Add Multiple Assign Locations'
    form_class = FormProduct

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # https://stackoverflow.com/questions/50313153/how-to-save-multiple-html-inputs-with-the-same-name-in-django
            a = request.POST.getlist('no_loc')
            b = request.POST.getlist('prod_code')
            c = request.POST.getlist('qty')
            auth = request.POST.get('uid')

            combine = min([len(a), len(b), len(c)])
            for i in range(combine):
                # filter by remark as new, dengan product code, lokasi empty di tb temp prod loc
                tb_temp = ModelTempProdLoc.objects.filter(remark="NEW", prod_code=b[i], no_loc__isnull=True)

                # filter dengan lokasi yang assign primary dan free
                location = ModelLocation.objects.filter(no_loc=a[i], assign="P", status="FL")  # lokasi primary, free

                if tb_temp and location:
                    if int(c[i]) > 0:
                        ModelTransaction.objects.create(
                            no_loc=a[i],
                            # adjustment physical inventory diluar sto / ttb / picking
                            trans_type="API",
                            adj_type="AI",
                            prod_code_id=b[i],
                            qty_bfr=0,
                            qty_adj=c[i],
                            qty_afr=c[i],
                            uid=auth
                        )
                        # update
                    tb_temp.update(no_loc=a[i], qty=c[i], remark="LOC")
                    # beri value 'UL' bahwa status lokasi sudah digunakan
                    ModelLocation.objects.filter(no_loc=a[i]).update(status="UL")
                messages.success(self.request, f'{a[i]}:{b[i]}|{c[i]}')
            return redirect("AddNewlineMass")


# (HTMX) Check Newline
def check_newline(request):
    location = request.POST.get('no_loc')

    if location:
        # jika lokasi sudah ada di tabel temporary ( lokasi sudah digunakan )
        if ModelTempProdLoc.objects.filter(no_loc=location).exists():
            return HttpResponse(
                '<div class="text-danger ml-1">Location is already in use.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        # jika lokasi tidak ada di tabel lokasi
        elif not ModelLocation.objects.filter(no_loc=location).exists():
            return HttpResponse(
                '<div class="text-danger ml-1">Location not available.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        # error jika ini lokasi reserve
        elif ModelLocation.objects.filter(no_loc=location, assign="R"):
            return HttpResponse(
                '<div class="text-danger ml-1">Reserve location cannot be used.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        # error jika ini lokasi status delete
        elif ModelLocation.objects.filter(no_loc=location, status="DL"):
            return HttpResponse(
                '<div class="text-danger ml-1">Location cannot be used.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        else:
            return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class EditNewline(StaffRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'inventory/newline/newline_add.html'
    title = title + 'Assign Location'
    header = title + ' / ' + 'Add Assignment'
    model = ModelTempProdLoc
    fields = ['no_loc']
    context_object_name = 'data'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['free_list'] = ModelLocation.objects.filter(assign="P", status="FL")
        context['options_assign'] = options_assign
        context['options_storage'] = options_storage
        context['options_area'] = options_area
        context['options_stats_loc'] = options_stats_loc
        return context

    def form_valid(self, form):
        if form.is_valid():
            form.save()
            # beri value 'LOC' pada remark bahwa produk sudah memiliki lokasi
            ModelTempProdLoc.objects.filter(no_loc_id=self.object.no_loc_id).update(remark="LOC")
            # beri value 'UL' bahwa status lokasi sudah digunakan
            ModelLocation.objects.filter(no_loc=self.object.no_loc_id).update(status="UL")
            messages.success(self.request,
                             f"Location <strong>{self.object.no_loc_id}</strong> <br> added for Part No. <strong>{self.object.prod_code_id}</strong>.")
        return redirect(self.request.META.get('HTTP_REFERER'))


class DeleteNewline(StaffRequiredMixin, UpdateView):
    model = ModelTempProdLoc
    fields = ['remark']
    success_url = reverse_lazy('ViewNewline')

    def form_valid(self, form):
        if form.is_valid():
            form.save()
            # hapus lokasi dari produk
            ModelTempProdLoc.objects.filter(id=self.object.pk).update(no_loc_id=None)
            # update status sebagai FL di tabel lokasi
            ModelLocation.objects.filter(no_loc=self.object.no_loc_id).update(status="FL")
            messages.success(self.request,
                             f"Assignment Location <strong>{self.object.no_loc_id}</strong> <br> has been removed from Part No. <strong>{self.object.prod_code_id}</strong>.")
        return redirect(self.request.META.get('HTTP_REFERER'))


# sampai sini ya New Line view

# transfer / stock move
class ViewTransfer(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'inventory/transfer/tf_view.html'
    title = title + 'Moving Part'
    header = title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        duplicate = ModelTempProdLoc.objects.values('prod_code').annotate(total_prod_code=Count('prod_code'),
                                                                          my_sum=Sum('qty')).filter(
            total_prod_code__gt=1, prod_code__is_active=True)
        duplicate_code = [item['prod_code'] for item in duplicate]
        context['letdown'] = ModelTempProdLoc.objects.filter(prod_code__in=duplicate_code, no_loc__assign="P",
                                                             qty__lte=F('prod_code__stock_min'))
        return context


class ResultTransfer(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'inventory/transfer/tf_view.html'
    title = title + 'Moving Part'
    header = title
    model = ModelTempProdLoc
    context_object_name = 'transfer'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['options_stats_loc'] = options_stats_loc
        return context

    def get_queryset(self):  # http://shopnilsazal.github.io/django-pagination-with-basic-search/
        a = self.request.GET.get('prod_code')
        b = self.request.GET.get('prod_desc')
        c = self.request.GET.get('no_loc')

        if a:
            transfer = ModelTempProdLoc.objects.filter(Q(prod_code__prod_code=a), remark="LOC").order_by(
                'no_loc__assign', 'no_loc')
        elif b:
            transfer = ModelTempProdLoc.objects.filter(Q(prod_code__prod_desc__icontains=b), remark="LOC").order_by(
                'no_loc__assign', 'no_loc')
        elif c:
            transfer = ModelTempProdLoc.objects.filter(Q(no_loc__no_loc__icontains=c), remark="LOC").order_by(
                'no_loc__assign', 'no_loc')
        else:
            transfer = ""
        return transfer


# (HTMX) Cek validasi transfer
def check_transaction(request):
    id = request.POST.get('id')
    product_code = request.POST.get('prod_code')
    qty2 = request.POST.get('qty2')
    location1 = request.POST.get('no_loc')
    location2 = request.POST.get('no_loc2')

    # variable
    primary1 = ModelLocation.objects.filter(no_loc=location1, assign="P")  # status lokasi1 primary
    primary2 = ModelLocation.objects.filter(no_loc=location2, assign="P")  # status lokasi2 primary
    reserve1 = ModelLocation.objects.filter(no_loc=location1, assign="R")  # status lokasi1 reserve
    reserve2 = ModelLocation.objects.filter(no_loc=location2, assign="R")  # status lokasi2 reserve
    edit_tabel = ModelTempProdLoc.objects.filter(id=id)

    # reserve dengan lokasi dan produk yang sudah ada di db
    matching = ModelTempProdLoc.objects.filter(no_loc=location2, prod_code=product_code)

    for data in edit_tabel:
        #   error qty to location lebih besar dari qty from location
        if int(data.qty) < int(qty2):
            return HttpResponse(
                '<div class="text-danger ml-1">Avoid negative values.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

        # lokasi primary vs primary (fixed)
        elif primary1 and primary2:
            # jika lokasi primary bukan status free
            if not primary2.filter(status="FL"):
                return HttpResponse(
                    '<div class="text-danger ml-1">Selected location status not free.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
            # jika qty from location tidak sama dengan qty to location
            elif not int(data.qty) == int(qty2):
                return HttpResponse(
                    '<div class="text-danger ml-1">Transfer quantity must match.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
            else:
                return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')

        # lokasi primary vs reserve (fixed)
        elif primary1 and reserve2:
            #   error location reserve deleted atau held
            if reserve2.filter(Q(status="DL") | Q(status="HU")):
                return HttpResponse(
                    '<div class="text-danger ml-1">Selected location cannot be used.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

            #   error from location reserve 1 dan to location reserve 2 tidak matching by prod code nya
            elif reserve2.filter(status="UL") and not matching:
                return HttpResponse(
                    '<div class="text-danger ml-1">The specified location does not match the part number.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
            else:
                return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')

        # lokasi reserve vs reserve (fixed)
        elif reserve1 and reserve2:
            #   error location reserve deleted atau held
            if reserve2.filter(Q(status="DL") | Q(status="HU")):
                return HttpResponse(
                    '<div class="text-danger ml-1">Selected location cannot be used.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

            #   error from location reserve 1 dan to location reserve 2 tidak matching by prod code nya
            elif reserve2.filter(status="UL") and not matching:
                return HttpResponse(
                    '<div class="text-danger ml-1">The specified location does not match the part number.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
            else:
                return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')

        # lokasi reserve vs primary
        elif reserve1 and primary2:
            #   error location primary deleted
            if primary2.filter(Q(status="DL") | Q(status="FL")):
                return HttpResponse(
                    '<div class="text-danger ml-1">Selected location cannot be used.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

            #   error from location reserve 1 dan to location primary 2 tidak matching by prod code nya
            elif primary2.filter(status="UL") and not matching:  # jika lokasi primary used
                return HttpResponse(
                    '<div class="text-danger ml-1">The specified location does not match the part number.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
            else:
                return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
        elif not ModelLocation.objects.filter(no_loc=location2).exists():  # jika lokasi tidak ada di tabel lokasi
            return HttpResponse(
                '<div class="text-danger ml-1">Location not available.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
        else:
            return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class UpdateTransfer(StaffRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'inventory/transfer/tf_update.html'
    title = title + 'Moving Part'
    header = title + ' / ' + 'Transfer'
    model = ModelTempProdLoc
    fields = ['remark', 'qty', 'no_loc', 'prod_code']
    context_object_name = 'data_transfer'
    success_url = reverse_lazy('ViewTransfer')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if ModelTempProdLoc.objects.filter(prod_code=self.object.prod_code):
            # filter relevant location
            relevant = ModelTempProdLoc.objects.filter(prod_code=self.object.prod_code).exclude(
                prod_code=self.object.prod_code, no_loc=self.object.no_loc).order_by('no_loc__assign')
        context['selection'] = relevant
        context['options_assign'] = options_assign
        context['options_storage'] = options_storage
        context['options_area'] = options_area
        context['options_stats_loc'] = options_stats_loc
        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            id = request.POST.get('id')
            product_code = request.POST.get('prod_code')
            location1 = request.POST.get('no_loc')
            location2 = request.POST.get('no_loc2')
            qty2 = request.POST.get('qty2')
            auth = request.POST.get('uid')

            # variable
            primary1 = ModelLocation.objects.filter(no_loc=location1, assign="P")  # status lokasi primary
            primary2 = ModelLocation.objects.filter(no_loc=location2, assign="P")  # status lokasi primary
            reserve1 = ModelLocation.objects.filter(no_loc=location1, assign="R")  # status lokasi2 reserve
            reserve2 = ModelLocation.objects.filter(no_loc=location2, assign="R")  # status lokasi2 reserve
            edit_tabel = ModelTempProdLoc.objects.filter(id=id)

            # reserve dengan lokasi dan produk yang sudah ada di db
            matching = ModelTempProdLoc.objects.filter(no_loc_id=location2, prod_code_id=product_code)

            # primary vs primary
            if primary1 and primary2:
                for data in edit_tabel:
                    # update lokasi lama menjadi lokasi baru lokasi 1
                    edit_tabel.update(no_loc=location2, modified=str(timezone.now()))
                    # update status lokasi 1 menjadi free
                    ModelLocation.objects.filter(no_loc=location1).update(status="FL")
                    # update status lokasi 2 menjadi used
                    ModelLocation.objects.filter(no_loc=location2).update(status="UL")

                    # create di model transaksi lokasi lama
                    ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                    adj_type="AO", prod_code_id=product_code, uid=auth,
                                                    qty_bfr=data.qty, qty_adj=qty2,
                                                    qty_afr=int(data.qty) - int(qty2))

                    # create di model transaksi lokasi baru
                    ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                    prod_code_id=product_code, uid=auth,
                                                    qty_bfr=int(data.qty) - int(qty2), qty_adj=qty2,
                                                    qty_afr=data.qty)
                messages.success(self.request,
                                 f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

            # primary vs reserve
            elif primary1 and reserve2:
                for data in edit_tabel:
                    total = int(data.qty) - int(qty2)
                    # reserve free
                    if reserve2.filter(status="FL"):
                        # update qty lama menjadi qty baru lokasi 1
                        edit_tabel.update(qty=int(total), modified=str(timezone.now()))
                        # update status lokasi 2 menjadi used
                        ModelLocation.objects.filter(no_loc=location2).update(status="UL")
                        ModelTempProdLoc.objects.create(
                            remark="LOC",
                            qty=int(qty2),
                            no_loc_id=location2,
                            prod_code_id=data.prod_code_id
                        )

                        # create di model transaksi lokasi lama
                        ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                        adj_type="AO", prod_code_id=product_code, uid=auth,
                                                        qty_bfr=data.qty, qty_adj=qty2,
                                                        qty_afr=total)

                        # create di model transaksi lokasi baru
                        ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                        prod_code_id=product_code, uid=auth, qty_bfr=0, qty_adj=qty2,
                                                        qty_afr=int(data.qty) - total)

                        messages.success(self.request,
                                         f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")
                        # reserve used same product
                    elif reserve2.filter(status="UL") and matching:
                        for data_match in matching:
                            # update qty lama menjadi qty baru lokasi 1
                            edit_tabel.update(qty=int(total), modified=str(timezone.now()))
                            # update qty lama menjadi qty baru lokasi 2
                            matching.update(qty=int(data_match.qty) + int(qty2))

                            # create di model transaksi lokasi lama
                            ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                            adj_type="AO", prod_code_id=product_code, uid=auth,
                                                            qty_bfr=data.qty, qty_adj=qty2,
                                                            qty_afr=int(data.qty) - int(qty2))

                            # create di model transaksi lokasi baru
                            ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                            prod_code_id=product_code, uid=auth, qty_bfr=data_match.qty,
                                                            qty_adj=qty2,
                                                            qty_afr=int(data_match.qty) + int(qty2))
                        messages.success(self.request,
                                         f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

            # reserve vs reserve
            elif reserve1 and reserve2:
                for data in edit_tabel:
                    total = int(data.qty) - int(qty2)
                    # reserve free
                    if reserve2.filter(status="FL"):
                        # update status lokasi 2 menjadi used
                        ModelLocation.objects.filter(no_loc=location2).update(status="UL")
                        ModelTempProdLoc.objects.create(
                            remark="LOC",
                            qty=int(qty2),
                            no_loc_id=location2,
                            prod_code_id=data.prod_code_id
                        )

                        # create di model transaksi lokasi lama
                        ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                        adj_type="AO", prod_code_id=product_code, uid=auth,
                                                        qty_bfr=data.qty, qty_adj=qty2,
                                                        qty_afr=int(data.qty) - int(qty2))

                        # create di model transaksi lokasi baru
                        ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                        prod_code_id=product_code, uid=auth, qty_bfr=0, qty_adj=qty2,
                                                        qty_afr=int(data.qty) - total)

                        # jika pengurangan menghasilkan nol
                        if total == 0:

                            # update status lokasi 1 menjadi free
                            ModelLocation.objects.filter(no_loc=location1).update(status="FL")
                            messages.success(self.request,
                                             f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

                            # langsung delete reserve lama (alternative kodingan)
                            edit_tabel.delete()

                            return HttpResponseRedirect(self.success_url)
                        else:
                            # update qty lama menjadi qty baru lokasi 1
                            edit_tabel.update(qty=int(total), modified=str(timezone.now()))
                            messages.success(self.request,
                                             f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

                    elif reserve2.filter(status="UL") and matching:  # reserve used same product
                        for data_match in matching:
                            # create di model transaksi lokasi lama
                            ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                            adj_type="AO", prod_code_id=product_code, uid=auth,
                                                            qty_bfr=data.qty, qty_adj=qty2,
                                                            qty_afr=int(data.qty) - int(qty2))

                            # create di model transaksi lokasi baru
                            ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                            prod_code_id=product_code, uid=auth, qty_bfr=data_match.qty,
                                                            qty_adj=qty2,
                                                            qty_afr=int(data_match.qty) + int(qty2))
                            # jika pengurangan menghasilkan nol
                            if total == 0:
                                # langsung delete reserve lama (alternative kodingan)
                                edit_tabel.delete()
                                # update qty lama menjadi qty baru di lokasi 2
                                matching.update(qty=int(data_match.qty) + int(qty2))
                                # update status lokasi 1 menjadi free
                                ModelLocation.objects.filter(no_loc=location1).update(status="FL")
                                messages.success(self.request,
                                                 f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")
                                return HttpResponseRedirect(self.success_url)
                            else:
                                edit_tabel.update(qty=int(total), modified=str(timezone.now()))
                                # update qty lama menjadi qty baru di lokasi 2
                                matching.update(qty=int(data_match.qty) + int(qty2))
                                messages.success(self.request,
                                                 f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

            # reserve vs primary
            elif reserve1 and primary2:
                for data in edit_tabel:
                    total = int(data.qty) - int(qty2)
                    if primary2.filter(status="UL") and matching:
                        for data_match in matching:
                            # create di model transaksi lokasi lama
                            ModelTransaction.objects.create(no_loc=location1, no_loc_to=location2, trans_type="PM",
                                                            adj_type="AO", prod_code_id=product_code, uid=auth,
                                                            qty_bfr=data.qty, qty_adj=qty2,
                                                            qty_afr=int(data.qty) - int(qty2))

                            # create di model transaksi lokasi baru
                            ModelTransaction.objects.create(no_loc=location2, trans_type="PM", adj_type="AI",
                                                            prod_code_id=product_code, uid=auth, qty_bfr=data_match.qty,
                                                            qty_adj=qty2,
                                                            qty_afr=int(data_match.qty) + int(qty2))

                            # jika pengurangan menghasilkan nol
                            if total == 0:
                                # langsung delete reserve lama (alternative kodingan)
                                edit_tabel.delete()
                                # update qty lama menjadi qty baru lokasi 2
                                matching.update(qty=int(data_match.qty) + int(qty2))
                                # update status lokasi 1 menjadi free
                                ModelLocation.objects.filter(no_loc=location1).update(status="FL")
                                messages.success(self.request,
                                                 f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")
                                return HttpResponseRedirect(self.success_url)
                            else:
                                edit_tabel.update(qty=int(total))
                                # update qty lama menjadi qty baru lokasi 2
                                matching.update(qty=int(data_match.qty) + int(qty2), modified=str(timezone.now()))
                                messages.success(self.request,
                                                 f"Transfer from Location <strong>{location1}</strong> to <br> Location <strong>{location2}</strong> successful.")

            return redirect(self.request.META.get('HTTP_REFERER'))


# sampai sini ya transfer view
# proses-proses adjustment

# TTB adjustment
class ViewReceiving(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'inbound/receive_list.html'
    title = title + 'Inbound'
    header = title + ' / ' + 'Parts Receipts'
    model = ModelTransaction
    context_object_name = 'receipt'

    def get_queryset(self):
        today = datetime.now()
        # filter receiving current month
        return ModelTransaction.objects.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"), date_created__year=today.year,
                                               date_created__month=today.month).order_by('-date_created')


class ResultReceiving(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'inbound/receive_list.html'
    title = title + 'Inbound'
    header = title + ' / ' + 'Parts Receipts'
    model = ModelTransaction
    context_object_name = 'receipt'

    def get_queryset(self):
        ttb_no = self.request.GET.get('no_ttb')
        product_code = self.request.GET.get('prod_code')

        if ttb_no:
            return ModelTransaction.objects.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"), no_ttb=ttb_no).order_by(
                '-date_created')
        elif product_code:
            return ModelTransaction.objects.filter(Q(ttb_stat="OR") | Q(ttb_stat="RE"),
                                                   prod_code__prod_code__icontains=product_code).order_by(
                '-date_created')


class FormTransaction(ModelForm):
    class Meta:
        model = ModelTransaction
        fields = ['uid', 'no_ttb', 'ttb_stat', 'ttb_qty', 'no_loc', 'trans_type', 'adj_type', 'prod_code', 'qty_bfr',
                  'qty_adj', 'qty_afr', 'vendor', 'no_pr']


# cek add receiving (htmx)
def check_add_receiving(request):
    ttb_numb_list = request.POST.getlist('no_ttb')
    product_code_list = request.POST.getlist('prod_code')
    quantity = request.POST.getlist('qty')

    # cek jika ada no ttb dan no prod exists
    exists = any(
        ModelTransaction.objects.filter(no_ttb=ttb_numb, prod_code=product_code).exists() for ttb_numb, product_code in
        zip(ttb_numb_list, product_code_list))

    # cek jika ada no prod tidak memiliki lokasi primary
    no_primary = any(
        ModelTempProdLoc.objects.filter(prod_code=product_code, no_loc__isnull=True).exists() for product_code in
        product_code_list)

    # cek part number terdaftar di database
    product_exists = any(
        ModelProduct.objects.filter(prod_code=product_code, is_active=True).exists() for product_code in
        product_code_list)

    if exists:
        return HttpResponse(
            '<div class="text-danger ml-1">No. TTB with part has been registered.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    elif no_primary:
        return HttpResponse(
            '<div class="text-danger ml-1">One or more parts do not have assign locations.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    elif not product_exists:
        return HttpResponse(
            '<div class="text-danger ml-1">Part does not exists.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')

    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class AddReceiving(StaffRequiredMixin, PageTitleViewMixin, CreateView):
    # fungsi self.form_valid(...)  adalah save
    template_name = 'inbound/receive_add.html'
    title = title + 'Inbound'
    header = title + ' / ' + 'Parts Receipts'
    model = ModelTransaction
    form_class = FormTransaction

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # https://stackoverflow.com/questions/50313153/how-to-save-multiple-html-inputs-with-the-same-name-in-django
            a = request.POST.getlist('no_ttb')
            b = request.POST.getlist('prod_code')
            c = request.POST.getlist('qty')
            d = request.POST.getlist('vendor')
            f = request.POST.getlist('no_pr')
            g = self.request.POST.get('uid')
            combine = min([len(a), len(b), len(c), len(d), len(f)])
            for i in range(combine):

                # filter by produk yang memiliki lokasi primary
                get = ModelTempProdLoc.objects.filter(prod_code_id=b[i], no_loc__assign="P")

                if get.filter(remark="LOC"):
                    for e in get:
                        uom = int(c[i]) * e.prod_code.pack_size
                        formset = self.form_class({
                            'no_ttb': a[i],
                            'ttb_stat': 'OR',  # Status "OR" -- Input receipt sebagai original input
                            'ttb_qty': c[i],
                            'no_loc': e.no_loc_id,
                            'trans_type': 'TTB',
                            'adj_type': 'AI',
                            'prod_code': b[i],
                            'qty_bfr': e.qty,
                            'qty_adj': uom,
                            'qty_afr': int(e.qty) + uom,
                            'vendor': d[i],
                            'no_pr': f[i],
                            'uid': g,
                        })

                        # check whether it's valid:
                        if formset.is_valid():
                            #   save formset
                            formset.save()

                            # update qty tb_temp
                            get.update(qty=int(e.qty) + uom, modified=str(timezone.now()))

                            #   produk.filter(prod_code=b[i]).update(supplier=v[i]) # update nama vendor
                        messages.success(self.request, f'{a[i]}:{b[i]}')

                else:
                    messages.add_message(self.request, messages.ERROR, "Product doesn't exist.")
            return redirect(self.request.META.get('HTTP_REFERER'))


class FormUpdateTransaction(ModelForm):
    class Meta:
        model = ModelTransaction
        fields = ['ttb_stat', 'no_ttb', 'vendor', 'ttb_qty', 'no_pr', 'no_loc', 'trans_type', 'adj_type', 'qty_bfr',
                  'qty_adj', 'qty_afr', 'uid', 'prod_code', 'date_created']


# cek receiving value qty update validation
def check_qty_update_receiving(request):
    ttb_qty = request.POST.get('ttb_qty')
    qty = request.POST.get('qty')
    select = request.POST.get('adjust')

    if select == 'AO' and int(ttb_qty) < int(qty):
        return HttpResponse(
            '<div class="text-danger ml-1">Avoid negative values.</div><script>$("#btnSave").attr("disabled", "disabled")</script>')
    elif select == 'AI':
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')
    else:
        return HttpResponse('<script>$("#btnSave").removeAttr("disabled")</script>')


class UpdateReceiving(StaffRequiredMixin, PageTitleViewMixin, UpdateView):
    template_name = 'inbound/receive_update.html'
    title = title + 'Inbound'
    header = title + ' / ' + 'Update'
    model = ModelTransaction
    form_class = FormUpdateTransaction
    context_object_name = 'receipt'
    success_url = reverse_lazy('ViewReceiving')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = ModelTransaction.objects.filter(id=self.object.pk)
        context['options_adjust'] = options_adjust
        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            id = self.request.POST.get('id')
            ttb_no = self.request.POST.get('no_ttb')
            qty_ttb = self.request.POST.get('ttb_qty')  # qty ttb
            product_code = self.request.POST.get('prod_code')
            loc_id = self.request.POST.get('no_loc')
            date = self.request.POST.get('date')
            quantity = self.request.POST.get('qty')
            vendor = self.request.POST.get('vendor')
            pr_numb = self.request.POST.get('no_pr')
            opsi = self.request.POST.get('adjust')
            auth = self.request.POST.get('uid')

            # ambil qty dari status lokasi primary
            get = ModelTempProdLoc.objects.filter(prod_code_id=product_code, no_loc__assign="P")

            for e in get:
                uom = int(quantity) * e.prod_code.pack_size
                if opsi == 'AO':  # adjust. out
                    # jika qty ttb. lebih kecil dari qty adjustment out
                    if int(qty_ttb) < int(quantity):
                        # set a message
                        messages.error(self.request, "Avoid negative values.")
                        return redirect(request.META.get('HTTP_REFERER'))
                    else:
                        formset = self.form_class({
                            'ttb_stat': 'RE',  # status re (revisi) karena sudah di edit
                            'no_ttb': ttb_no,
                            'vendor': vendor,
                            'ttb_qty': int(qty_ttb) - int(quantity),
                            'no_pr': pr_numb,
                            'no_loc': loc_id,  # pakai lokasi terima barang
                            'trans_type': 'TTB',
                            'adj_type': 'AI',  # di buat tetap sebagai AI yang membedakan adalah ttb_stat RE
                            'qty_bfr': e.qty,
                            'qty_adj': str("-") + str(uom),
                            'qty_afr': int(e.qty) - uom,
                            'uid': auth,
                            'prod_code': product_code,
                        })
                        # check whether it's valid:
                        if formset.is_valid():
                            # save formset
                            formset.save()

                            # update qty tb_temp
                            get.update(qty=int(e.qty) - uom, modified=str(timezone.now()))

                            # ganti tanggal id (baru)
                            ModelTransaction.objects.filter(ttb_stat="RE", no_ttb=ttb_no,
                                                            prod_code=product_code).update(date_created=date)

                            # delete id (lama)
                            self.object = self.get_object()
                            self.object.delete()
                            messages.success(self.request,
                                             f"Stock Part No. <strong>{product_code}</strong> <br> has been successfully changed.")

                elif opsi == 'AI':  # adjust. in
                    formset = self.form_class(
                        {
                            'ttb_stat': 'RE',
                            'no_ttb': ttb_no,
                            'vendor': vendor,
                            'ttb_qty': int(qty_ttb) + int(quantity),
                            'no_pr': pr_numb,
                            'no_loc': loc_id,  # pakai lokasi terima barang
                            'trans_type': 'TTB',
                            'adj_type': 'AI',
                            'qty_bfr': e.qty,
                            'qty_adj': uom,
                            'qty_afr': int(e.qty) + uom,
                            'date_created': date,  # pakai tanggal sesuai terima barang
                            'uid': auth,
                            'prod_code': product_code,
                        })
                    # check whether it's valid:
                    if formset.is_valid():
                        # save formset
                        formset.save()

                        # update qty tb_temp
                        get.update(qty=int(e.qty) + uom, modified=str(timezone.now()))

                        # ganti tanggal id (baru)
                        ModelTransaction.objects.filter(ttb_stat="RE", no_ttb=ttb_no, prod_code=product_code).update(
                            date_created=date)

                        # delete id (lama)
                        self.object = self.get_object()
                        self.object.delete()
                        messages.success(self.request,
                                         f"Stock Part No. <strong>{product_code}</strong> <br> has been successfully changed.")
            return HttpResponseRedirect(self.success_url)


# sampai sini ya view receiving

# pick adjustment
class ViewPicking(PageTitleViewMixin, ListView):
    template_name = 'picking/pick_list.html'
    title = title + 'Picking'
    header = title + ' / ' + 'Pick Order'
    model = ModelTempPickCart
    context_object_name = 'carts'
    ordering = ['-date_created']

    # produk yang dlm cart
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['temp_list'] = ModelTempProdLoc.objects.filter(no_loc__assign="P")
        context['options_storage'] = options_storage
        context['options_area'] = options_area
        return context


# insert to cart
class AddToCart(CreateView):
    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            a = self.request.POST.get('prod_code')
            b = self.request.POST.get('qty')
            if ModelTempPickCart.objects.filter(prod_code_id=a, is_active=True):
                messages.error(request, f'Part No. <strong>{a}</strong> <br> already in cart.')
            else:
                ModelTempPickCart.objects.create(prod_code_id=a, qty=b)
                messages.success(request, f"Part No. <strong>{a}</strong> <br> successfully added to cart.")
        return redirect('ViewPicking')


class DeleteFromCart(DeleteView):
    model = ModelTempPickCart

    def get_success_url(self, **kwargs):
        messages.success(self.request,
                         f"Part No. <strong>{self.object.prod_code_id}</strong> <br> successfully deleted from cart.")
        return self.request.META.get('HTTP_REFERER')


class ResultPicking(PageTitleViewMixin, ListView):
    template_name = 'picking/pick_list.html'
    title = title + 'Picking'
    header = title + ' / ' + 'Pick Order'
    model = ModelTempProdLoc
    context_object_name = 'data_list'

    def get_queryset(self):
        product_code = self.request.GET.get('prod_code')
        description = self.request.GET.get('prod_desc')
        location1 = self.request.GET.get('no_loc')

        if product_code:
            # return ModelTempProdLoc.objects.filter(Q(prod_code__prod_code__icontains=product_code), remark="LOC", no_loc__assign="P", no_loc__status="UL", qty__gt=0)
            # request nya qty 0 ditampilkan
            return ModelTempProdLoc.objects.filter(Q(prod_code__prod_code__icontains=product_code), remark="LOC", no_loc__assign="P", no_loc__status="UL")
        elif description:
            # return ModelTempProdLoc.objects.filter(Q(prod_code__prod_desc__icontains=description), remark="LOC", no_loc__assign="P", no_loc__status="UL", qty__gt=0)
            # request nya qty 0 ditampilkan
            return ModelTempProdLoc.objects.filter(Q(prod_code__prod_desc__icontains=description), remark="LOC", no_loc__assign="P", no_loc__status="UL")
        elif location1:
            # return ModelTempProdLoc.objects.filter(Q(no_loc__no_loc__icontains=location1), remark="LOC", no_loc__assign="P", no_loc__status="UL", qty__gt=0)
            # request nya qty 0 ditampilkan
            return ModelTempProdLoc.objects.filter(Q(no_loc__no_loc__icontains=location1), remark="LOC", no_loc__assign="P", no_loc__status="UL", qty__gt=0)

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if queryset.count() == 0:
            messages.error(request, '<strong>Sorry!</strong><br>Your search not found')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_storage'] = options_storage
        context['options_area'] = options_area
        return context


# (HTMX) check pick update (bug jika qty2 dihapus jadi blank / qty 0)
def check_textarea(request):
    text = request.POST.get('comment', '')
    if text.strip():
        return HttpResponse('<script>$("#btnSave").removeClass("disabled")</script>')
    else:
        return HttpResponse(
            '<div class="text-danger ml-1">Fill the form to be submitted.</div><script>$("#btnSave").addClass("disabled")</script>')


def check_pick_update(request):
    if request.method == 'POST':
        qty1_values = request.POST.getlist('qty_avail')
        qty2_values = request.POST.getlist('qty')

        # parameter nilai pengurangan qty 2 - qty 1 hasilnya negatif,
        # "int(qty1)-1" karna kalau hasilnya 0 error Avoid negative values
        all_negative = all(int(qty2) - int(qty1) - 1 < 0 for qty1, qty2 in zip(qty1_values, qty2_values))

        if not all_negative:
            return HttpResponse(
                '<div class="text-danger ml-1">Avoid negative values.</div><script>$("#btnSave").addClass("disabled")</script>')
        elif all_negative:
            return HttpResponse('<script>$("#btnSave").removeClass("disabled")</script>')


class UpdatePicking(PageTitleViewMixin, ListView):
    template_name = 'picking/pick_update.html'
    title = title + 'Picking'
    header = title + ' / ' + 'Picking Cart'
    model = ModelTempPickCart
    context_object_name = 'object_list'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['temp_list'] = ModelTempProdLoc.objects.filter(no_loc__assign="P")
        context['options_storage'] = options_storage
        context['options_area'] = options_area
        return context

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            # https://stackoverflow.com/questions/50313153/how-to-save-multiple-html-inputs-with-the-same-name-in-django
            a = self.request.POST.getlist('prod_code')
            b = self.request.POST.getlist('qty')
            c = self.request.POST.getlist('adjust')
            d = self.request.POST.get('comment')
            auth = self.request.POST.get('uid')

            combine = min([len(a), len(b), len(c)])
            uid_list = ModelUserUID.objects.filter(Q(level="ADM") | Q(level="STD"), uid=auth, status=True)
            if uid_list.exists():
                for u in uid_list:
                    for i in range(combine):
                        get = ModelTempProdLoc.objects.filter(prod_code_id=a[i], no_loc__assign="P")
                        for e in get:
                            if c[i] == 'AO':
                                if int(b[i]) > int(e.qty):
                                    messages.error(request, "Avoid negative values.")
                                    return redirect(request.META.get('HTTP_REFERER'))
                                else:
                                    final = int(e.qty) - int(b[i])
                                    # update qty tb_temp prod loc
                                    get.update(qty=final, modified=str(timezone.now()))
                                    # create record di tabel transaksi
                                    ModelTransaction.objects.create(
                                        no_loc=e.no_loc_id,
                                        trans_type="PCK",
                                        adj_type=str(c[i]),
                                        prod_code=e.prod_code,
                                        qty_bfr=int(e.qty),
                                        qty_adj=str("-") + str(int(b[i])),
                                        qty_afr=final,
                                        comment=str(d),
                                        uid=u.usernm
                                    )
                                    # remove all the data in table cart
                                    ModelTempPickCart.objects.all().delete()
                                    messages.success(request, "Parts successfully picked.")
                    return redirect('Dashboard')
            else:
                messages.add_message(self.request, messages.ERROR, "Invalid credentials.")
            return redirect(self.request.META.get('HTTP_REFERER'))


# sampai sini ya view picking

# stock opname adjustment

class ViewStockOpname(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'inventory/stockopname/sto_list.html'
    title = title + 'Stock Count'
    header = title

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # all check lokasi kecuali status delete (kalo mau rubah, perhatikan juga variable sto di dashboard)
        total = ModelLocation.objects.exclude(status="DL")
        uncheck = total.filter(sto_check__isnull=True).count()
        checked = total.filter(sto_check="CHK").count()
        pending = total.filter(sto_check="PND").count()

        if total:
            context['total'] = total.count()
            context['uncheck'] = uncheck
            context['uncheck_percentage'] = 100 * uncheck / total.count()
            context['checked'] = checked
            context['checked_percentage'] = 100 * checked / total.count()
            context['pending'] = pending
            context['pending_percentage'] = 100 * pending / total.count()
            context['options_assign'] = options_assign
            context['options_storage'] = options_storage
            context['options_area'] = options_area
            context['options_stats_loc'] = options_stats_loc
        return context


# pagination datatable ajax
def ListLocationStockCount(request):
    # Get parameters from DataTables request
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    draw = int(request.GET.get('draw', 1))
    search_value = request.GET.get('search[value]', '')
    order_column_index = int(request.GET.get('order[0][column]', 0))
    order_direction = request.GET.get('order[0][dir]', 'asc')

    # Map column index to model field names
    columns_map = {
        0: 'no_loc',
        1: 'sto_check',
        2: 'part_number',   # bug sort part_number
        3: 'part_desc',  # bug sort part_desc
        4: 'assign',
        5: 'storage',
        6: 'area',
        7: 'status',
        # Add mappings for other columns as needed
    }

    # Determine the field to order by
    order_field = columns_map.get(order_column_index, 'no_loc')  # Default order column is sto_check

    # Apply sorting direction
    if order_direction == 'desc':
        order_field = '-' + order_field  # Prepend '-' for descending order

    queryset = ModelLocation.objects.exclude(status="DL").order_by(order_field, 'no_loc')
    part_location_dict = {part.no_loc_id: (part.prod_code_id, part.prod_code.prod_desc) for part in ModelTempProdLoc.objects.all()}

    # Reverse the key-value pairs
    reversed_options_assign = {value: key for key, value in options_assign.items()}
    reversed_options_area = {value: key for key, value in options_area.items()}
    reversed_options_storage = {value: key for key, value in options_storage.items()}
    reversed_options_stats_loc = {value: key for key, value in options_stats_loc.items()}
    reversed_options_chk_sto = {value: key for key, value in options_chk_sto.items()}

    # Merge the reversed dictionaries into a single mapping dictionary
    mapping = {}
    mapping.update(reversed_options_assign)
    mapping.update(reversed_options_area)
    mapping.update(reversed_options_storage)
    mapping.update(reversed_options_stats_loc)
    mapping.update(reversed_options_chk_sto)

    # Function for case-insensitive replacement
    def replace_mapped_terms(term):
        for key, value in mapping.items():
            term = term.replace(key, value)
            term = term.replace(key.capitalize(), value)  # Replace capitalized version
            term = term.replace(key.upper(), value)  # Replace uppercase version
            term = term.replace(key.lower(), value)  # Replace lowercase version
        return term

    # Replace mapped terms in the search value
    search_value = replace_mapped_terms(search_value)

    # Filtering based on search value
    if search_value:
        queryset = queryset.filter(Q(no_loc__icontains=search_value) | Q(assign=search_value) | Q(
            sto_check=search_value) | Q(storage=search_value) | Q(
            area=search_value) | Q(status=search_value))

    paginator = Paginator(queryset, length)
    page_number = (start // length) + 1
    page_obj = paginator.get_page(page_number)

    # Serialize paginated data
    data = [
        {'cek': obj.sto_check,
         'noloc': obj.no_loc,
         'assgn': obj.assign,
         'stor': obj.storage,
         'area': obj.area,
         'stats': obj.status,
         'part_number': part_location_dict.get(obj.no_loc, ('', 0))[0],
         'part_desc': part_location_dict.get(obj.no_loc, ('', 0))[1],} for i, obj in enumerate(page_obj)]

    return JsonResponse({
        'data': data,
        'length': length,
        'draw': draw,
        'recordsTotal': paginator.count,
        'recordsFiltered': paginator.count,
    })


class ResultStockOpname(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'inventory/stockopname/sto_update.html'
    title = title + 'Stock Count'
    header = title + ' / ' + 'Adjustment'
    model = ModelTempProdLoc
    context_object_name = 'sto_locations'
    query = None

    def get_queryset(self):
        self.query = self.request.GET.get('q')
        return ModelTempProdLoc.objects.filter(no_loc_id=self.query)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        last = ModelLocation.objects.exclude(status="DL").filter(sto_check__isnull=True).order_by('no_loc')[0]
        context['no_product'] = ModelLocation.objects.filter(no_loc=self.query)
        context['last'] = last
        context['options_assign'] = options_assign
        context['options_area'] = options_area
        context['options_storage'] = options_storage
        context['options_stats_loc'] = options_stats_loc
        return context


class UpdateStockOpname(StaffRequiredMixin, UpdateView):
    model = ModelTempProdLoc
    fields = ['qty']
    success_url = reverse_lazy('ViewStockOpname')

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            id = self.request.POST.get('id')
            quantity = self.request.POST.get('qty')
            location = self.request.POST.get('no_loc')
            edit_tabel = ModelTempProdLoc.objects.filter(id=id)
            reserve = ModelLocation.objects.filter(no_loc=location, assign="R")
            author = self.request.POST.get('uid')
            for data in edit_tabel:
                # jika lokasinya reserve dan qty adj 0
                if reserve and int(quantity) == 0:
                    qty_adjust = int(data.qty) - int(quantity)
                    qty_after = int(data.qty) - int(qty_adjust)
                    # update status & sto_check lokasi
                    ModelLocation.objects.filter(no_loc=location).update(sto_check="CHK", status="FL")
                    ModelTransaction.objects.create(
                        no_loc=data.no_loc_id,
                        trans_type="STO",
                        adj_type="AO",
                        prod_code=data.prod_code,
                        qty_bfr=int(data.qty),
                        qty_adj=str("-") + str(qty_adjust),
                        qty_afr=qty_after,
                        uid=author
                    )
                    edit_tabel.delete()  # langsung delete (alternative kodingan)
                    messages.success(self.request,
                                     f"Location <strong>{location}</strong> has been <br> successfully adjusted (out).")
                    return HttpResponseRedirect(self.success_url)

                # jika qty before lebih besar dari adjust qty
                elif int(data.qty) > int(quantity):
                    qty_adjust = int(data.qty) - int(quantity)
                    qty_after = int(data.qty) - int(qty_adjust)
                    edit_tabel.update(qty=qty_after, modified=str(timezone.now()))
                    # update status sto_check chk untuk lokasi sudah di sto
                    ModelLocation.objects.filter(no_loc=data.no_loc_id).update(sto_check="CHK")
                    ModelTransaction.objects.create(
                        no_loc=data.no_loc_id,
                        trans_type="STO",
                        adj_type="AO",
                        prod_code=data.prod_code,
                        qty_bfr=int(data.qty),
                        qty_adj=str("-") + str(qty_adjust),
                        qty_afr=qty_after,
                        uid=author
                    )
                    messages.success(self.request,
                                     f"Location <strong>{location}</strong> has been <br> successfully adjusted (out).")

                # jika qty before lebih kecil dari adjustment
                elif int(data.qty) < int(quantity):
                    qty_adjust = int(quantity) - int(data.qty)
                    qty_after = int(data.qty) + int(qty_adjust)
                    edit_tabel.update(qty=qty_after, modified=str(timezone.now()))
                    # update status sto_check chk untuk lokasi sudah di sto
                    ModelLocation.objects.filter(no_loc=data.no_loc_id).update(sto_check="CHK")
                    ModelTransaction.objects.create(
                        no_loc=data.no_loc_id,
                        trans_type="STO",
                        adj_type="AI",
                        prod_code=data.prod_code,
                        qty_bfr=int(data.qty),
                        qty_adj=qty_adjust,
                        qty_afr=qty_after,
                        uid=author
                    )
                    messages.success(self.request,
                                     f"Location <strong>{location}</strong> has been <br> successfully adjusted (in).")

                elif int(data.qty) == int(quantity):  # jika nilai adj sama dengan qty before
                    qty_adjust = int(quantity) - int(data.qty)
                    qty_after = int(data.qty) + int(qty_adjust)
                    edit_tabel.update(qty=qty_after, modified=str(timezone.now()))
                    # update status sto_check chk untuk lokasi sudah di sto
                    ModelLocation.objects.filter(no_loc=data.no_loc_id).update(sto_check="CHK")
                    ModelTransaction.objects.create(
                        no_loc=data.no_loc_id,
                        trans_type="STO",
                        adj_type="AI",
                        prod_code=data.prod_code,
                        qty_bfr=int(data.qty),
                        qty_adj=qty_adjust,
                        qty_afr=qty_after,
                        uid=author
                    )
                    messages.success(self.request,
                                     f"Location <strong>{location}</strong> has been <br> successfully adjusted (in).")

                return redirect(request.META.get('HTTP_REFERER'))


# "chk" u/ sudah dicek (checked), "pnd" u/ sudah dicek tapi pending
class ConfirmStockOpname(StaffRequiredMixin, UpdateView):
    model = ModelLocation
    fields = ['sto_check']

    def get_success_url(self):
        messages.info(self.request, "Status has been changed.")
        return reverse('ViewStockOpname')


# (HTMX) Get description from prod_code
def check_get_desc(request):
    if request.method == 'POST':
        product_code = request.POST.get('prod_code')

        if product_code:
            # sort prod code dengan memiliki primary location dan produk aktif
            description = ModelTempProdLoc.objects.filter(prod_code=product_code, no_loc__assign="P",
                                                          prod_code__is_active=True)

            if description:
                for data in description:
                    return HttpResponse(
                        '<textarea class="form-control border-bottom" disabled >' + data.prod_code.prod_desc + '</textarea ><script>$("#msg-error").text(""); $("#btnSave").removeAttr("disabled"); </script>')
            else:
                return HttpResponse(
                    '<textarea class="form-control border-bottom" disabled ></textarea ><script>$("#msg-error").text("Part does not have a primary location or part not found.").addClass("text-danger"); $("#btnSave").attr("disabled", "disabled");</script>')
        else:
            return HttpResponse(
                '<textarea class="form-control border-bottom" disabled ></textarea ><script>$("#msg-error").text(""); $("#btnSave").removeAttr("disabled"); </script>')


class AddRsvStockOpname(StaffRequiredMixin, PageTitleViewMixin, UpdateView):  # menambah stok di reserve
    template_name = 'inventory/stockopname/sto_rsv_add.html'
    title = title + 'Stock Count'
    header = title + ' / ' + 'Adjustment'
    model = ModelLocation
    fields = ['status', 'sto_check']
    context_object_name = 'data'
    success_url = reverse_lazy('ViewStockOpname')

    def post(self, request, *args, **kwargs):
        if request.method == 'POST':
            product_code = self.request.POST.get('prod_code')
            no_location = self.request.POST.get('no_loc')
            quantity = self.request.POST.get('qty')
            author = self.request.POST.get('uid')

            # create value tabel temp
            ModelTempProdLoc.objects.create(prod_code_id=product_code, no_loc_id=no_location, qty=quantity,
                                            remark="LOC")
            # update value tabel location
            ModelLocation.objects.filter(no_loc=no_location).update(sto_check="CHK", status="UL")  # status chk & used
            # create value tabel transaksi
            ModelTransaction.objects.create(
                no_loc=no_location,
                trans_type="STO",
                adj_type="AI",
                prod_code_id=product_code,
                qty_bfr=0,
                qty_adj=quantity,
                qty_afr=quantity,
                uid=author
            )
            messages.success(self.request,
                             f"Location <strong>{no_location}</strong> <br> has been successfully adjusted (in).")
        return HttpResponseRedirect(self.success_url)


# menghapus marking yang sudah di cek tabel sto
class RemoveCheckStockOpname(StaffRequiredMixin, UpdateView):
    def post(self, request, *args, **kwargs):
        if "clear" in request.POST:
            ModelLocation.objects.update(sto_check=None)
            messages.success(self.request, "The mark for checking has been deleted.")
        return HttpResponseRedirect(reverse('ViewStockOpname'))


# sampai sini ya view stock opname


# record - record
class ViewAdjustmentRecord(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'report/record_adj.html'
    title = title + 'Report'
    header = title + ' / ' + 'Movement'
    model = ModelTransaction
    context_object_name = 'adjustment'

    def get_queryset(self):
        today = datetime.now()
        return ModelTransaction.objects.filter(date_created__year=today.year, date_created__month=today.month).order_by(
            '-date_created')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_adjustment'] = options_adjustment
        context['options_adjust'] = options_adjust
        context['options_trans_type'] = options_trans_type
        return context


def check_adjustment_numb(request):
    numb_check = request.POST.get('numb')
    check = ModelTransaction.objects.filter(Q(no_loc=numb_check) | Q(prod_code=numb_check) | Q(no_ttb=numb_check))

    if numb_check:
        if not check.exists():
            return HttpResponse(
                '<script>$("#msg-error").text("Data not found.").addClass("text-danger"); $("#btnSave").attr("disabled", "disabled"); </script>')
        else:
            return HttpResponse('<script>$("#msg-error").text(""); $("#btnSave").removeAttr("disabled"); </script>')
    else:
        return HttpResponse('<script>$("#msg-error").text(""); $("#btnSave").removeAttr("disabled"); </script>')


class ResultAdjustmentRecord(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'report/record_adj.html'
    title = title + 'Report'
    header = title + ' / ' + 'Movement'
    model = ModelTransaction
    context_object_name = 'adjustment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_adjustment'] = options_adjustment
        context['options_adjust'] = options_adjust
        context['options_trans_type'] = options_trans_type
        return context

    def get_queryset(self):
        numb = self.request.GET.get('numb')
        transaction_type = self.request.GET.get('trans_type')
        date_from = self.request.GET.get('date_bfr')
        date_to = self.request.GET.get('date_afr')

        # gte ≥ 'greater than or equal', lte ≤ 'lower than or equal'
        # pakai datetimepicker jquery
        gte = datetime.strptime(date_from, '%Y/%m/%d %H:%M')
        lte = datetime.strptime(date_to, '%Y/%m/%d %H:%M')

        # with numb & transaction_type
        if numb and transaction_type:
            return ModelTransaction.objects.filter(Q(no_loc=numb) | Q(prod_code=numb) | Q(no_ttb=numb),
                                                   trans_type=transaction_type, date_created__gte=gte,
                                                   date_created__lte=lte)
        # with numb
        elif numb:
            return ModelTransaction.objects.filter(Q(no_loc=numb) | Q(prod_code=numb) | Q(no_ttb=numb),
                                                   date_created__gte=gte, date_created__lte=lte)
        # with transaction_type
        elif transaction_type:
            return ModelTransaction.objects.filter(trans_type=transaction_type, date_created__gte=gte,
                                                   date_created__lte=lte)
        # without numb & transaction_type
        else:
            return ModelTransaction.objects.filter(date_created__gte=gte, date_created__lte=lte)


class ViewLocationProduct(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'report/record_loc.html'
    title = title + 'Report'
    header = title + ' / ' + 'Stock Parts (Location)'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['options_stats_loc'] = options_stats_loc
        context['tb_temp'] = ModelTempProdLoc.objects.filter(no_loc_id__isnull=False, prod_code__is_active=True)
        return context


class ResultLocationProduct(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'report/record_loc.html'
    title = title + 'Report'
    header = title + ' / ' + 'Stock Parts (Location)'
    model = ModelLocation
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['options_assign'] = options_assign
        context['options_stats_loc'] = options_stats_loc
        context['tb_temp'] = ModelTempProdLoc.objects.filter(no_loc_id__isnull=False)
        return context

    def get_queryset(self):
        location1 = self.request.GET.get('no_loc1')
        location2 = self.request.GET.get('no_loc2')
        assign_loc = self.request.GET.get('assign')
        status_loc = self.request.GET.get('status')

        if assign_loc and status_loc:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2, assign=assign_loc,
                                                status=status_loc).exclude(status="DL")
        elif status_loc:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2, status=status_loc)
        elif assign_loc:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2, assign=assign_loc)
        else:
            return ModelLocation.objects.filter(no_loc__gte=location1, no_loc__lte=location2).exclude(status="DL")

class ViewStockProduct(StaffRequiredMixin, PageTitleViewMixin, TemplateView):
    template_name = 'report/record_stock.html'
    title = title + 'Report'
    header = title + ' / ' + 'Stock Parts'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # display level stock product
        surplus = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_max')).count()
        safety = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_min'),
            total__lte=F('prod_code__stock_max')).count()
        # stok sama dengan / dibawah min (kecuali stock qty 0)
        critical = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=0, total__lte=F('prod_code__stock_min')).count()
        # empty stock
        empty = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total=0).count()

        context['surplus'] = surplus
        context['percentage_surplus'] = 100 * surplus / (surplus + safety + critical + empty)
        context['safety'] = safety
        context['percentage_safety'] = 100 * safety / (surplus + safety + critical + empty)
        context['critical'] = critical
        context['percentage_critical'] = 100 * critical / (surplus + safety + critical + empty)
        context['empty'] = empty
        context['percentage_empty'] = 100 * empty / (surplus + safety + critical + empty)
        context['options_lvl_sto'] = options_lvl_sto
        return context


class ResultStockProduct(StaffRequiredMixin, PageTitleViewMixin, ListView):
    template_name = 'report/record_stock.html'
    title = title + 'Report'
    header = title + ' / ' + 'Stock Parts'
    model = ModelTempProdLoc
    context_object_name = 'product'

    def get_queryset(self):
        numb_desc = self.request.GET.get('numb')
        level = self.request.GET.get('level')

        # with product , with empty condition
        if numb_desc and level == "E":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                Q(prod_code__prod_desc__icontains=numb_desc) | Q(prod_code=numb_desc), prod_code__is_active=True,
                my_sum=0).order_by('prod_code')
        # with product, with surplus condition
        elif numb_desc and level == "S":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                Q(prod_code__prod_desc__icontains=numb_desc) | Q(prod_code=numb_desc), prod_code__is_active=True,
                my_sum__gt=F('prod_code__stock_max')).order_by('prod_code')
        # with product, with safety condition
        elif numb_desc and level == "B":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                Q(prod_code__prod_desc__icontains=numb_desc) | Q(prod_code=numb_desc), prod_code__is_active=True,
                my_sum__gt=F('prod_code__stock_min'), my_sum__lte=F('prod_code__stock_max')).order_by(
                'prod_code')
        # with product, with critical condition
        elif numb_desc and level == "C":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                Q(prod_code__prod_desc__icontains=numb_desc) | Q(prod_code=numb_desc), prod_code__is_active=True,
                my_sum__gt=0, my_sum__lte=F('prod_code__stock_min')).order_by('prod_code')
        # with product, without level
        elif numb_desc:
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                Q(prod_code__prod_desc__icontains=numb_desc) | Q(prod_code=numb_desc),
                prod_code__is_active=True).order_by('prod_code')
        # without product, with empty level
        elif level == "E":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                prod_code__is_active=True, my_sum=0).order_by('prod_code')
        # without product, with surplus level
        elif level == "S":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                prod_code__is_active=True, my_sum__gt=F('prod_code__stock_max')).order_by('prod_code')
        # without product, with safety level
        elif level == "B":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                prod_code__is_active=True, my_sum__gt=F('prod_code__stock_min'),
                my_sum__lte=F('prod_code__stock_max')).order_by('prod_code')
        # without product, with critical level
        elif level == "C":
            return ModelTempProdLoc.objects.values('prod_code', 'prod_code__prod_desc', 'prod_code__stock_min',
                                                   'prod_code__stock_max', 'prod_code__pack_size').annotate(
                my_sum=Sum('qty')).filter(
                prod_code__is_active=True, my_sum__gt=0, my_sum__lte=F('prod_code__stock_min')).order_by('prod_code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # display level stock product
        surplus = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_max')).count()
        safety = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=F('prod_code__stock_min'),
            total__lte=F('prod_code__stock_max')).count()
        # stok sama dengan / dibawah min (kecuali stock qty 0)
        critical = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total__gt=0, total__lte=F('prod_code__stock_min')).count()
        # empty stock
        empty = ModelTempProdLoc.objects.values('prod_code').annotate(total=Sum('qty')).filter(
            prod_code__is_active=True, total=0).count()

        context['surplus'] = surplus
        context['percentage_surplus'] = 100 * surplus / (surplus + safety + critical + empty)
        context['safety'] = safety
        context['percentage_safety'] = 100 * safety / (surplus + safety + critical + empty)
        context['critical'] = critical
        context['percentage_critical'] = 100 * critical / (surplus + safety + critical + empty)
        context['empty'] = empty
        context['percentage_empty'] = 100 * empty / (surplus + safety + critical + empty)
        context['options_lvl_sto'] = options_lvl_sto
        return context
