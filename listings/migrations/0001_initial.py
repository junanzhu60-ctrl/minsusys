from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Property",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, verbose_name="房源名称")),
                ("city", models.CharField(max_length=50, verbose_name="城市")),
                ("address", models.CharField(max_length=200, verbose_name="详细地址")),
                ("description", models.TextField(verbose_name="房源介绍")),
                ("price_per_night", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="每晚价格")),
                ("max_guests", models.PositiveSmallIntegerField(default=2, verbose_name="最多入住人数")),
                ("bedrooms", models.PositiveSmallIntegerField(default=1, verbose_name="卧室数")),
                ("amenities", models.CharField(blank=True, max_length=300, verbose_name="设施")),
                ("image_url", models.URLField(blank=True, verbose_name="封面图片链接")),
                ("status", models.CharField(choices=[("available", "可预订"), ("maintenance", "维护中"), ("offline", "已下架")], default="available", max_length=20, verbose_name="状态")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
            ],
            options={"verbose_name": "房源", "verbose_name_plural": "房源", "ordering": ["-created_at"]},
        ),
        migrations.CreateModel(
            name="Booking",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("guest_name", models.CharField(max_length=50, verbose_name="住客姓名")),
                ("phone", models.CharField(max_length=30, verbose_name="联系电话")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="邮箱")),
                ("check_in", models.DateField(verbose_name="入住日期")),
                ("check_out", models.DateField(verbose_name="退房日期")),
                ("guests", models.PositiveSmallIntegerField(default=1, verbose_name="入住人数")),
                ("note", models.TextField(blank=True, verbose_name="备注")),
                ("total_price", models.DecimalField(decimal_places=2, editable=False, max_digits=10, verbose_name="订单总额")),
                ("status", models.CharField(choices=[("pending", "待确认"), ("confirmed", "已确认"), ("cancelled", "已取消")], default="pending", max_length=20, verbose_name="订单状态")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="提交时间")),
                ("property", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="bookings", to="listings.property", verbose_name="房源")),
            ],
            options={"verbose_name": "订单", "verbose_name_plural": "订单", "ordering": ["-created_at"]},
        ),
    ]
