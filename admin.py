from django.contrib import admin
from .models import Design, Part, PartsToDesign, Document, Render, VendorNotes, Vendor, Licence
# Register your models here.

@admin.register(Licence)
class LicenceAdmin(admin.ModelAdmin):
    model = Licence

@admin.register(Render)
class RenderAdmin(admin.ModelAdmin):
    model = Render

class RenderInlineAdmin(admin.TabularInline):
    model = Render
    extra = 0

@admin.register(Part)
class PartAdmin(admin.ModelAdmin):
    model = Part
    inlines = [RenderInlineAdmin, ]

class VendorNotesInlineAdmin(admin.TabularInline):
    model = VendorNotes
    extra = 1

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    model = Vendor
    inlines = [VendorNotesInlineAdmin, ]

@admin.register(PartsToDesign)
class PartsToDesignAdmin(admin.ModelAdmin):
    model = PartsToDesign

class PartsToDesignInlineAdmin(admin.TabularInline):
    model = PartsToDesign
    extra = 0

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    model = Document

class DocumentInlineAdmin(admin.TabularInline):
    model = Document
    extra = 0

@admin.register(Design)
class DesignAdmin(admin.ModelAdmin):
    model = Design
    inlines = [PartsToDesignInlineAdmin, DocumentInlineAdmin,]