from django.db import models

# Create your models here.
class Vendor(models.Model):
    nama_vendor = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

class Produk(models.Model):
    kode_produk = models.CharField(max_length=50)
    nama_produk = models.CharField(max_length=255)
    unit = models.CharField(max_length=10, null=True)
    pack_size = models.IntegerField(null=True)  # conversion
    # stock_min = models.IntegerField(null=True)
    # stock_max = models.IntegerField(null=True)
    relasi_vendor = models.ManyToManyField('Vendor', blank=True)  # Related departments (optional)
    # img = ProcessedImageField(upload_to=upload_file, processors=[ResizeToFill(800, 600)], format='JPEG', options={'quality': 100}, null=True, default='images/placeholder.jpg')
    # l_time_days = models.IntegerField(null=True)
    is_active = models.BooleanField(default=True)
    # date_created = models.DateTimeField(default=timezone.now, blank=True)
    # modified = models.DateTimeField(null=True)