import csv
from datetime import date, timedelta
from decimal import Decimal

from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Booking


def _parse_date(value):
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _paid_bookings(request):
    bookings = Booking.objects.filter(payment_status=Booking.PaymentStatus.PAID).select_related("property")
    start_date = _parse_date(request.GET.get("start"))
    end_date = _parse_date(request.GET.get("end"))
    if start_date:
        bookings = bookings.filter(paid_at__date__gte=start_date)
    if end_date:
        bookings = bookings.filter(paid_at__date__lte=end_date)
    return bookings, start_date, end_date


def _csv_text(value):
    """让 Excel 将 CSV 值按文本显示，避免日期/金额被自动格式化为 ####。"""
    if value is None:
        return ""
    return f"\t{value}"


def finance_report(request):
    paid_bookings, start_date, end_date = _paid_bookings(request)
    paid_summary = paid_bookings.aggregate(revenue=Sum("total_price"), paid_count=Count("id"))
    pending_summary = Booking.objects.filter(
        payment_status=Booking.PaymentStatus.UNPAID,
        status=Booking.Status.PENDING,
    ).aggregate(amount=Sum("total_price"), count=Count("id"))

    paid_count = paid_summary["paid_count"] or 0
    pending_count = pending_summary["count"] or 0
    payment_rate = round(paid_count * 100 / (paid_count + pending_count)) if paid_count + pending_count else 0
    property_rows = list(
        paid_bookings.values("property__name", "property__city")
        .annotate(revenue=Sum("total_price"), orders=Count("id"))
        .order_by("-revenue", "property__name")[:8]
    )

    # 显示最近六个月的真实已支付营收；便于快速判断经营趋势。
    today = timezone.localdate()
    cursor = today.replace(day=1)
    months = []
    for _ in range(6):
        previous_last_day = cursor - timedelta(days=1)
        months.append(cursor)
        cursor = previous_last_day.replace(day=1)
    months.reverse()
    monthly_rows = []
    for month_start in months:
        next_month = (month_start.replace(day=28) + timedelta(days=4)).replace(day=1)
        amount = Booking.objects.filter(
            payment_status=Booking.PaymentStatus.PAID,
            paid_at__date__gte=month_start,
            paid_at__date__lt=next_month,
        ).aggregate(value=Sum("total_price"))["value"] or Decimal("0")
        monthly_rows.append({"label": month_start.strftime("%Y-%m"), "amount": amount})
    max_monthly_revenue = max((row["amount"] for row in monthly_rows), default=Decimal("0"))
    for row in monthly_rows:
        row["percent"] = int(row["amount"] * 100 / max_monthly_revenue) if max_monthly_revenue else 0

    return render(request, "admin/finance_report.html", {
        "total_revenue": paid_summary["revenue"] or Decimal("0"),
        "paid_count": paid_count,
        "pending_amount": pending_summary["amount"] or Decimal("0"),
        "pending_count": pending_count,
        "payment_rate": payment_rate,
        "property_rows": property_rows,
        "monthly_rows": monthly_rows,
        "start_date": start_date.isoformat() if start_date else "",
        "end_date": end_date.isoformat() if end_date else "",
    })


def finance_export(request):
    paid_bookings, _, _ = _paid_bookings(request)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="minsusys_finance_report.csv"'
    response.write("\ufeff")
    # QUOTE_ALL + 制表符前缀：Excel 会保留原始值，不会自行改写日期、金额或订单号。
    writer = csv.writer(response, quoting=csv.QUOTE_ALL, lineterminator="\n")
    writer.writerow(["订单号", "房源", "住客", "入住日期", "退房日期", "支付时间", "收款金额", "订单状态"])
    for booking in paid_bookings.order_by("-paid_at", "-created_at"):
        writer.writerow([
            _csv_text(booking.pk),
            _csv_text(booking.property.name),
            _csv_text(booking.guest_name),
            _csv_text(booking.check_in),
            _csv_text(booking.check_out),
            _csv_text(timezone.localtime(booking.paid_at).strftime("%Y-%m-%d %H:%M") if booking.paid_at else "历史订单"),
            _csv_text(f"¥{booking.total_price:.2f}"),
            _csv_text(booking.get_status_display()),
        ])
    return response
