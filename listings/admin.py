from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Booking, Property


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "name", "city", "price_per_night", "max_guests", "status", "edit_link")
    list_display_links = ("name",)
    list_editable = ("price_per_night", "max_guests", "status")
    list_filter = ("city", "status")
    search_fields = ("name", "city", "address")
    readonly_fields = ("image_preview",)
    exclude = ("image_url",)
    fieldsets = (
        ("房源信息", {"fields": ("name", "city", "address", "description", "status")}),
        ("入住与价格", {"fields": ("price_per_night", "max_guests", "bedrooms", "amenities")}),
        ("本地封面图片", {"fields": ("image", "image_preview"), "description": "点击“选择文件”后，直接从电脑中上传图片。"}),
    )

    @admin.display(description="封面")
    def image_preview(self, obj):
        if obj and obj.image:
            return format_html('<img src="{}" alt="{}" style="width: 72px; height: 48px; object-fit: cover; border-radius: 10px;" />', obj.image.url, obj.name)
        return "—"

    @admin.display(description="操作")
    def edit_link(self, obj):
        url = reverse("admin:listings_property_change", args=(obj.pk,))
        return format_html('<a class="button" href="{}">编辑房型</a>', url)


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("guest_name", "property", "check_in", "check_out", "guests", "total_price", "payment_status", "status")
    list_filter = ("payment_status", "status", "check_in")
    search_fields = ("guest_name", "phone", "property__name")
    readonly_fields = ("total_price", "paid_at", "payment_token", "created_at")
