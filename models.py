from hashlib import md5

from django.db import models
# Create your models here.
from django.utils.text import slugify


def part_directory_path(instance, filename):
    return f"design/{instance.design.slug}/parts/{filename}"

def document_directory_path(instance, filename):
    return f"design/{instance.design.slug}/document/{filename}"

def render_directory_path(instance, filename):
    return f"design/{instance.part.design.slug}/render/{filename}"

def licence_directory_path(instance, filename):
    return f"licence/{instance.name}/{filename}"

class Licence(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, null=True, blank=True, default=None, editable=False)
    url = models.URLField(null=True, blank=True, default=None)
    file = models.FileField(upload_to=licence_directory_path)

    def save(instance, *args, **kwargs):
        if instance.slug is None:
            instance.slug = slugify(instance.name)
        super(Licence, instance).save(*args, **kwargs)

    def __str__(instance):
        return f"{instance.name}"


class Vendor(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, null=True, blank=True, default=None, editable=False)
    url = models.URLField(null=True, blank=True, default=None)
    email = models.EmailField(null=True, blank=True, default=None)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(instance, *args, **kwargs):
        if instance.slug is None:
            instance.slug = slugify(instance.name)
        super(Vendor, instance).save(*args, **kwargs)

    def __str__(instance):
        return f"{instance.name}"

class VendorNotes(models.Model):
    text = models.TextField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    vendor = models.ForeignKey(to=Vendor, on_delete=models.CASCADE, blank=True, null=True, default=None)

    class Meta:
        get_latest_by = "created_at"
        ordering = ['vendor', 'created_at']

        def __str__(instance):
            return f"{instance.vendor.name} - {instance.created_at:%B %d, %Y}"

class Part(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=255, null=True, blank=True, default=None, editable=False)
    design = models.ForeignKey(to='Design',null=False, on_delete=models.CASCADE)
    md5sum = models.CharField(max_length=50, blank=True, null=True, default=None, db_index=True)
    width = models.FloatField(default=None, null=True, blank=True)
    height = models.FloatField(default=None, null=True, blank=True)
    depth = models.FloatField(default=None, null=True, blank=True)
    file = models.FileField(upload_to=part_directory_path)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['md5sum', 'design']]

    def save(instance, *args, **kwargs):
        if instance.md5sum is None:
            hash_md5 = md5()
            for chunk in instance.file.chunks(chunk_size=4096):
                hash_md5.update(chunk)
            instance.md5sum = hash_md5.hexdigest()
        if instance.slug is None:
            instance.slug = slugify(instance.name)
        super(Part, instance).save(*args, **kwargs)

    def __str__(instance):
        return f"{instance.name}"


class Render(models.Model):
    part = models.ForeignKey(to=Part, on_delete=models.CASCADE, null=False)
    style = models.CharField(max_length=100)
    image = models.ImageField(upload_to=render_directory_path)
    camera_yaw = models.IntegerField()
    camera_pitch = models.IntegerField()

    def __str__(instance):
        return f"{instance.image.name}"

class DocumentType(models.Model):
    name = models.CharField(max_length=50)

    def __str__(instance):
        return f"{instance.name}"

class Document(models.Model):
    name = models.CharField(max_length=100)
    design = models.ForeignKey(to='Design',null=False, on_delete=models.CASCADE)
    md5sum = models.CharField(max_length=50, blank=True, null=True, default=None, db_index=True)
    file = models.FileField(upload_to=document_directory_path)
    type = models.ForeignKey(to=DocumentType, blank=True, null=True, default=None, on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(instance, *args, **kwargs):
        if instance.md5sum is None:
            hash_md5 = md5()
            for chunk in instance.file.chunks(chunk_size=4096):
                hash_md5.update(chunk)
            instance.md5sum = hash_md5.hexdigest()
        super(Document, instance).save(*args, **kwargs)

    def __str__(instance):
        return f"{instance.name}"

class Design(models.Model):
    name = models.CharField(max_length=100,)
    slug = models.SlugField(max_length=255, null=True, blank=True, default=None, editable=False)
    vendor = models.ForeignKey(to=Vendor,null=True, blank=True, default=None, on_delete=models.CASCADE)
    source = models.URLField(null=True, blank=True, default=None)
    license = models.ForeignKey(to=Licence, on_delete=models.CASCADE, default=None, blank=True, null=True)
    commercial_use = models.BooleanField(default=False)
    parts = models.ManyToManyField(Part, through='PartsToDesign', related_name='DesignToPart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [['name', 'vendor']]

    def save(instance, *args, **kwargs):
        if instance.slug is None:
            instance.slug = slugify(instance.name)
        super(Design, instance).save(*args, **kwargs)

    def __str__(instance):
        return f"{instance.name}"

class PartsToDesign(models.Model):
    design = models.ForeignKey(Design, on_delete=models.CASCADE)
    part = models.ForeignKey(Part, on_delete=models.CASCADE)
    count = models.IntegerField(default=1)

    def __str__(instance):
        return f"{instance.part.name} ({instance.design.name})"