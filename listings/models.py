from builtins import property as builtin_property
import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone


class StoredImage(models.Model):
    """免费托管环境的持久化图片，不依赖临时本地文件系统。"""

    name = models.CharField(max_length=255, primary_key=True)
    content = models.BinaryField()
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


class Property(models.Model):
    class Status(models.TextChoices):
        AVAILABLE = "available", "可预订"
        SOLD_OUT = "sold_out", "已售罄"
        MAINTENANCE = "maintenance", "维护中"
        OFFLINE = "offline", "已下架"

    name = models.CharField("房源名称", max_length=100)
    city = models.CharField("城市", max_length=50)
    address = models.CharField("详细地址", max_length=200)
    description = models.TextField("房源介绍")
    price_per_night = models.DecimalField("每晚价格", max_digits=10, decimal_places=2)
    max_guests = models.PositiveSmallIntegerField("最多入住人数", default=2)
    bedrooms = models.PositiveSmallIntegerField("卧室数", default=1)
    amenities = models.CharField("设施", max_length=300, blank=True, help_text="用中文逗号分隔，例如：WiFi，空调，厨房")
    image = models.ImageField("封面图片", upload_to="properties/", blank=True)
    # 保留旧字段，确保此前已录入的网络图片仍可在前台正常展示。
    image_url = models.URLField("历史图片链接", blank=True)
    status = models.CharField("状态", max_length=20, choices=Status.choices, default=Status.AVAILABLE)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)

    class Meta:
        verbose_name = "房源"
        verbose_name_plural = "房源"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.city} · {self.name}"


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "待确认"
        CONFIRMED = "confirmed", "已确认"
        CANCELLED = "cancelled", "已取消"

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", "待支付"
        PAID = "paid", "已支付"

    property = models.ForeignKey(Property, verbose_name="房源", on_delete=models.PROTECT, related_name="bookings")
    guest_name = models.CharField("住客姓名", max_length=50)
    phone = models.CharField("联系电话", max_length=30)
    email = models.EmailField("邮箱", blank=True)
    check_in = models.DateField("入住日期")
    check_out = models.DateField("退房日期")
    guests = models.PositiveSmallIntegerField("入住人数", default=1)
    note = models.TextField("备注", blank=True)
    total_price = models.DecimalField("订单总额", max_digits=10, decimal_places=2, editable=False)
    status = models.CharField("订单状态", max_length=20, choices=Status.choices, default=Status.PENDING)
    payment_status = models.CharField("支付状态", max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID)
    paid_at = models.DateTimeField("支付时间", blank=True, null=True)
    payment_token = models.UUIDField("支付链接令牌", default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField("提交时间", auto_now_add=True)

    class Meta:
        verbose_name = "订单"
        verbose_name_plural = "订单"
        ordering = ["-created_at"]

    @builtin_property
    def nights(self):
        return (self.check_out - self.check_in).days

    def clean(self):
        if self.check_in and self.check_out and self.check_out <= self.check_in:
            raise ValidationError("退房日期必须晚于入住日期。")
        if self.property_id and self.guests > self.property.max_guests:
            raise ValidationError(f"该房源最多入住 {self.property.max_guests} 人。")
        if self.status == self.Status.CONFIRMED and self.payment_status != self.PaymentStatus.PAID:
            raise ValidationError("订单必须在标记为已支付后才能确认。")
        if self.property_id and self.check_in and self.check_out and self.status != self.Status.CANCELLED:
            clashes = Booking.objects.filter(
                property=self.property,
                status=Booking.Status.CONFIRMED,
                check_in__lt=self.check_out,
                check_out__gt=self.check_in,
            )
            if self.pk:
                clashes = clashes.exclude(pk=self.pk)
            if clashes.exists():
                raise ValidationError("该日期已有已确认订单，请选择其他日期。")

    def save(self, *args, **kwargs):
        previous = None
        if self.pk:
            previous = Booking.objects.filter(pk=self.pk).values("property_id", "status", "payment_status").first()

        if self.check_in and self.check_out and self.property_id:
            self.total_price = self.nights * self.property.price_per_night
        with transaction.atomic():
            super().save(*args, **kwargs)
            is_paid_and_confirmed = (
                self.status == self.Status.CONFIRMED
                and self.payment_status == self.PaymentStatus.PAID
            )
            if is_paid_and_confirmed:
                Property.objects.filter(pk=self.property_id).update(status=Property.Status.SOLD_OUT)

            # 已支付且已确认的订单取消、改为未支付，或改到其他房源时，恢复原房源状态。
            if previous and previous["status"] == self.Status.CONFIRMED and previous["payment_status"] == self.PaymentStatus.PAID:
                if previous["property_id"] != self.property_id or not is_paid_and_confirmed:
                    self._restore_property_if_available(previous["property_id"])

    @staticmethod
    def _restore_property_if_available(property_id):
        has_confirmed_booking = Booking.objects.filter(
            property_id=property_id,
            status=Booking.Status.CONFIRMED,
            payment_status=Booking.PaymentStatus.PAID,
        ).exists()
        if not has_confirmed_booking:
            Property.objects.filter(pk=property_id, status=Property.Status.SOLD_OUT).update(
                status=Property.Status.AVAILABLE
            )

    @classmethod
    def release_departed_stays(cls, today=None):
        """退房日到达后，自动释放没有其他有效已支付订单的房源。"""
        today = today or timezone.localdate()
        paid_confirmed = cls.objects.filter(
            status=cls.Status.CONFIRMED,
            payment_status=cls.PaymentStatus.PAID,
        )
        departed_property_ids = paid_confirmed.filter(check_out__lte=today).values_list(
            "property_id", flat=True
        ).distinct()
        still_occupied_property_ids = paid_confirmed.filter(check_out__gt=today).values_list(
            "property_id", flat=True
        ).distinct()
        return Property.objects.filter(
            pk__in=departed_property_ids,
            status=Property.Status.SOLD_OUT,
        ).exclude(pk__in=still_occupied_property_ids).update(status=Property.Status.AVAILABLE)

    def delete(self, *args, **kwargs):
        property_id = self.property_id
        was_confirmed = self.status == self.Status.CONFIRMED and self.payment_status == self.PaymentStatus.PAID
        with transaction.atomic():
            result = super().delete(*args, **kwargs)
            if was_confirmed:
                self._restore_property_if_available(property_id)
        return result

    def mark_paid(self):
        """客户确认扫码完成后，将支付和订单状态同步更新。"""
        if self.status == self.Status.CANCELLED:
            raise ValidationError("已取消的订单不能确认支付。")
        if self.payment_status == self.PaymentStatus.PAID:
            return
        if not Property.objects.filter(pk=self.property_id, status=Property.Status.AVAILABLE).exists():
            raise ValidationError("该房源当前不可预订，请联系主理人。")
        self.full_clean()
        self.payment_status = self.PaymentStatus.PAID
        self.paid_at = timezone.now()
        self.status = self.Status.CONFIRMED
        self.save()

    def __str__(self):
        return f"{self.guest_name} · {self.property.name} · {self.check_in}"
