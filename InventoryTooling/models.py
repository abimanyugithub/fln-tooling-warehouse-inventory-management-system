from django.db import models
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.contrib.auth.models import User
import os

#   crop image
from imagekit.models import ProcessedImageField, ImageSpecField
from imagekit.processors import ResizeToFill, SmartCrop


# Class UpperChar create upper string
class UpperChar(models.CharField):
    def __init__(self, *args, **kwargs):
        super(UpperChar, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).upper()


# Class LowerChar create upper string
class LowerChar(models.CharField):
    def __init__(self, *args, **kwargs):
        super(LowerChar, self).__init__(*args, **kwargs)

    def get_prep_value(self, value):
        return str(value).lower()


#   Filename upload file
def upload_file(instance, filename):
    # get extension
    extension = os.path.splitext(filename)[1]
    return f'images/products/{instance.pk}{extension}'


def random_id():
    random = get_random_string(5, allowed_chars='0123456789')
    random_str = str(random) + str(timezone.now().strftime("%d%m%y"))
    return random_str


# Create your models here
class ModelProduct(models.Model):
    prod_code = UpperChar(max_length=20, primary_key=True)
    prod_desc = UpperChar(max_length=60, null=True)
    unit = UpperChar(max_length=10, null=True)  # uom
    pack_size = models.IntegerField(null=True)  # conversion
    stock_min = models.IntegerField(null=True)
    stock_max = models.IntegerField(null=True)
    supplier = UpperChar(max_length=60, null=True)
    img = ProcessedImageField(upload_to=upload_file, processors=[ResizeToFill(800, 600)], format='JPEG', options={'quality': 100}, null=True, default='images/placeholder.jpg')
    l_time_days = models.IntegerField(null=True)
    is_active = models.BooleanField(default=1, null=True)
    date_created = models.DateTimeField(default=timezone.now, blank=True)
    modified = models.DateTimeField(null=True)

    class Meta:
        db_table = "tb_Product"

    def save(self, *args, **kwargs):
        # On save, update timestamps
        self.modified = timezone.now()
        return super(ModelProduct, self).save(*args, **kwargs)


class ModelLocation(models.Model):
    no_loc = UpperChar(max_length=20, primary_key=True)
    assign = UpperChar(max_length=1, null=True)
    storage = UpperChar(max_length=2, null=True)
    area = UpperChar(max_length=2, null=True)
    status = models.CharField(default='FL', max_length=2, null=True)
    sto_check = models.CharField(max_length=3, null=True)
    date_created = models.DateTimeField(default=timezone.now, blank=True)
    modified = models.DateTimeField()

    class Meta:
        db_table = "tb_Location"

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.modified = timezone.now()
        return super(ModelLocation, self).save(*args, **kwargs)


# Create your models here
class ModelTempProdLoc(models.Model):
    id = models.CharField(max_length=11, default=random_id, editable=False, primary_key=True)
    prod_code = models.ForeignKey(ModelProduct, on_delete=models.CASCADE, null=True)
    no_loc = models.ForeignKey(ModelLocation, on_delete=models.CASCADE, null=True)
    remark = UpperChar(max_length=3, null=True)  # untuk remark pada proses yang berkaitan
    qty = models.IntegerField(default=0, null=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "tb_TempProdLoc"

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        self.modified = timezone.now()
        return super(ModelTempProdLoc, self).save(*args, **kwargs)


class ModelUserUID(models.Model):
    uid = models.CharField(max_length=10, null=True)
    nik = models.IntegerField(null=True)
    nm_krywn = UpperChar(max_length=20, null=True)
    dept = UpperChar(max_length=20, null=True)
    usernm = LowerChar(max_length=10, null=True)
    level = UpperChar(max_length=3, null=True)  # Superuser | sup, Administrator | adm, Standard | std
    status = models.BooleanField(default=1, null=True)
    modified = models.DateTimeField(auto_now=True)
    joined = models.DateTimeField(default=timezone.now, blank=True)

    class Meta:
        db_table = "tb_UserUID"


class ModelTransaction(models.Model):
    id = models.CharField(max_length=11, default=random_id, editable=False, primary_key=True)
    # field u/ ttb
    ttb_stat = models.CharField(max_length=2, null=True)
    no_ttb = models.CharField(max_length=10, null=True)
    vendor = models.TextField(max_length=30, null=True)  # supplier
    ttb_qty = models.IntegerField(null=True)  # qty ttb
    no_pr = models.CharField(max_length=20, null=True)

    no_loc = UpperChar(max_length=20, null=True)
    no_loc_to = UpperChar(max_length=20, null=True)
    trans_type = models.CharField(max_length=3, null=True)
    adj_type = models.CharField(max_length=2, null=True)
    prod_code = models.ForeignKey(ModelProduct, on_delete=models.CASCADE, null=True)
    qty_bfr = models.IntegerField(null=True)  # qty before
    qty_adj = models.IntegerField(null=True)  # qty yang di adjustment
    qty_afr = models.IntegerField(null=True)  # qty after
    date_created = models.DateTimeField(default=timezone.now, blank=True)

    # field u/ picking
    comment = models.CharField(max_length=160, null=True)
    uid = LowerChar(max_length=20, null=True)

    class Meta:
        db_table = "tb_Transaction"


class ModelTempPickCart(models.Model):
    prod_code = models.ForeignKey(ModelProduct, on_delete=models.CASCADE, null=True)
    qty = models.IntegerField(null=True)
    date_created = models.DateTimeField(default=timezone.now, blank=True)
    is_active = models.BooleanField(default=1, null=True)

    class Meta:
        db_table = "tb_Carts"
