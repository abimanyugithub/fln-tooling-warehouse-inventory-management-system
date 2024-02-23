from django.urls import path, re_path
import InventoryTooling.views
from . import views
from InventoryTooling.views import Template404View, Template403View
#   image upload (1 of 2)
from django.conf import settings
from django.conf.urls.static import static

#   end image upload (1 of 2)

handler404 = Template404View.as_view()
handler403 = Template403View.as_view()

urlpatterns = [

    path('', views.Dashboard.as_view(), name='Dashboard'),
    path('label', views.ViewLabel.as_view(), name='ViewLabel'),
    path('label/result', views.ResultLabel.as_view(), name='ResultLabel'),

    # url u/ registration
    path('register', views.SignupPageView.as_view(), name='SignupPageView'),
    path('login', views.LoginPageView.as_view(), name='LoginPageView'),
    path('logout', views.LogoutPageView.as_view(), name='LogoutPageView'),
    path('user/change-password/<pk>', views.ChangePassPageView.as_view(), name='ChangePassPageView'),
    path('user/reset-password/<pk>', views.ResetPassPageView.as_view(), name='ResetPassPageView'),
    path('user', views.ViewUser.as_view(), name='ViewUser'),
    path('user/edit/<pk>', views.EditUser.as_view(), name='EditUser'),

    # url u/ user tag rfid
    path('user-tag', views.ViewUserUID.as_view(), name='ViewUserUID'),
    path('user-tag/add', views.AddUserUID.as_view(), name='AddUserUID'),
    path('user-tag/edit/<pk>', views.EditUserUID.as_view(), name='EditUserUID'),

    # url u/ location: view, search, add, edit, edit as delete
    path('location', views.ViewLocation.as_view(), name='ViewLocation'),  # lock_login
    # tampilkan datatable dari ajax
    path('location/datatable/', views.ListLocation, name='ListLocation'),
    path('location/add', views.AddLocation.as_view(), name='AddLocation'),  # lock_login
    path('location/add/mass', views.AddLocationMass.as_view(), name='AddLocationMass'),
    # lock_login superuser  # tambah banyak lokasi
    path('location/edit/<pk>', views.EditLocation.as_view(), name='EditLocation'),  # lock_login
    path('location/update/<pk>', views.UpdateStatusLocation.as_view(), name='UpdateStatusLocation'),  # lock_login

    # url u/ product view, search, add, edit, detail
    path('product', views.ViewProduct.as_view(), name='ViewProduct'),  # lock_login
    # tampilkan datatable dari ajax
    path('product/datatable/', views.ListProduct, name='ListProduct'),
    path('product/add', views.AddProduct.as_view(), name='AddProduct'),  # lock_login
    path('product/add/mass', views.AddProductMass.as_view(), name='AddProductMass'),
    # tambah banyak produk
    path('product/edit/<pk>', views.EditProduct.as_view(), name='EditProduct'),  # lock_login
    path('product/detail/<pk>', views.DetailProduct.as_view(), name='DetailProduct'),  # lock_login

    # url u/ adjustment view, search
    path('record/adjust', views.ViewAdjustmentRecord.as_view(), name='ViewAdjustmentRecord'),  # lock_login
    path('record/adjust/result', views.ResultAdjustmentRecord.as_view(), name='ResultAdjustmentRecord'),  # lock_login
    path('record/location', views.ViewLocationProduct.as_view(), name='ViewLocationProduct'),  # lock_login
    path('record/location/result', views.ResultLocationProduct.as_view(), name='ResultLocationProduct'),  # lock_login
    path('record/stock', views.ViewStockProduct.as_view(), name='ViewStockProduct'),  # lock_login
    path('record/stock/result', views.ResultStockProduct.as_view(), name='ResultStockProduct'),  # lock_login

    # url u/ assign location view, search, edit, edit as delete
    path('location-assign', views.ViewNewline.as_view(), name='ViewNewline'),  # lock_login
    path('location-assign/add/mass', views.AddNewlineMass.as_view(), name='AddNewlineMass'),
    path('location-assign/edit/<pk>', views.EditNewline.as_view(), name='EditNewline'),  # lock_login
    path('location-assign/delete/<pk>', views.DeleteNewline.as_view(), name='DeleteNewline'),  # lock_login

    # url u/ transfer view, search, edit
    path('moving-part', views.ViewTransfer.as_view(), name='ViewTransfer'),  # lock_login
    path('moving-part/result', views.ResultTransfer.as_view(), name='ResultTransfer'),  # lock_login
    path('moving-part/edit/<pk>', views.UpdateTransfer.as_view(), name='UpdateTransfer'),  # lock_login

    # url u/ inbound view, search, add, edit
    path('receiving', views.ViewReceiving.as_view(), name='ViewReceiving'),  # lock_login
    path('receiving/result', views.ResultReceiving.as_view(), name='ResultReceiving'),  # lock_login
    path('receiving/add', views.AddReceiving.as_view(), name='AddReceiving'),  # lock_login
    path('receiving/edit/<pk>', views.UpdateReceiving.as_view(), name='UpdateReceiving'),  # lock_login

    # url u/ cart view, delete, update
    path('cart', views.AddToCart.as_view(), name='AddToCart'),
    path('cart/delete/<pk>', views.DeleteFromCart.as_view(), name='DeleteFromCart'),
    path('cart/update', views.UpdatePicking.as_view(), name='UpdatePicking'),

    # url u/ picking view, search, edit
    path('picking', views.ViewPicking.as_view(), name='ViewPicking'),
    path('picking/result', views.ResultPicking.as_view(), name='ResultPicking'),

    # url u/ stock opname view, search, edit,
    path('stock-count', views.ViewStockOpname.as_view(), name='ViewStockOpname'),  # lock_login
    # tampilkan datatable dari ajax
    path('stock-count/datatable/', views.ListLocationStockCount, name='ListLocationStockCount'),
    path('stock-count/result', views.ResultStockOpname.as_view(), name='ResultStockOpname'),  # lock_login
    path('stock-count/update/<pk>', views.UpdateStockOpname.as_view(), name='UpdateStockOpname'),  # lock_login
    path('stock-count/free/<pk>', views.ConfirmStockOpname.as_view(), name='ConfirmStockOpname'),  # lock_login
    path('stock-count/add/<pk>', views.AddRsvStockOpname.as_view(), name='AddRsvStockOpname'),  # lock_login
    path('stock-count/clear', views.RemoveCheckStockOpname.as_view(), name='RemoveCheckStockOpname'),  # lock_login
    path('refresh-page/', views.RefreshPage.as_view(), name='RefreshPage'),
]

htmx_urlpatterns = [
    path('check-username/', views.check_username, name='check-username'),  # cek username sign up
    path('check-username-login/', views.check_username_login, name='check-username-login'),  # cek username login
    path('check-password/', views.check_password, name='check-password'),
    path('check-change-password/', views.check_change_password, name='check-change-password'),
    path('check-add-tag/', views.check_user_uid, name='check-add-uid'),
    path('check-receiving/', views.check_qty_update_receiving, name='check-receiving'),
    path('check-add-receiving/', views.check_add_receiving, name='check-add-receiving'),
    path('check-pick-update/', views.check_pick_update, name='check-pick-update'),
    path('check-location/', views.check_location, name='check-location'),
    path('check-any-location/', views.check_any_location, name='check-any-location'),  # check mass location
    path('check-any-product/', views.check_any_product, name='check-any-product'),  # check mass product
    path('check-any-newline/', views.check_any_newline, name='check-any-newline'),  # check mass newline
    path('check-min-max/', views.check_minmax, name='check-min-max'),  # min max stok check
    path('check-product/', views.check_product, name='check-product'),  # check product code exists
    path('check-edit-newline/', views.check_newline, name='check-edit-newline'),  # check product code exists
    path('check-transaction/', views.check_transaction, name='check-transaction'),  # check transaction
    path('check-get-desc/', views.check_get_desc, name='check-get-desc'),  # check product sto
    path('check-adjust-numb/', views.check_adjustment_numb, name='check-adjust-numb'),
    # check no ttb / location / prod_code
    path('check-textarea/', views.check_textarea, name='check-textarea'),
]

urlpatterns += htmx_urlpatterns

#   image upload (2 of 2)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
#   end image upload (2 of 2)
