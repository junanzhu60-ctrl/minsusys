from django.contrib import messages
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, redirect, render

from .forms import BookingForm
from .models import Booking, Property


def home(request):
    Booking.release_departed_stays()
    visible_statuses = [Property.Status.AVAILABLE, Property.Status.SOLD_OUT]
    properties = Property.objects.filter(status__in=visible_statuses)
    city = request.GET.get("city", "").strip()
    keyword = request.GET.get("q", "").strip()
    if city:
        properties = properties.filter(city__icontains=city)
    if keyword:
        properties = properties.filter(Q(name__icontains=keyword) | Q(description__icontains=keyword))
    cities = Property.objects.filter(status__in=visible_statuses).values_list("city", flat=True).distinct()
    available_count = properties.filter(status=Property.Status.AVAILABLE).count()
    return render(request, "listings/home.html", {"properties": properties, "cities": cities, "city": city, "keyword": keyword, "available_count": available_count})


@require_POST
def management_entry(request):
    """前台进入管理端时强制退出旧会话，要求重新验证身份。"""
    logout(request)
    return redirect("/admin/login/?next=/admin/")


def property_detail(request, pk):
    Booking.release_departed_stays()
    property = get_object_or_404(
        Property.objects.filter(status__in=[Property.Status.AVAILABLE, Property.Status.SOLD_OUT]),
        pk=pk,
    )
    return render(request, "listings/property_detail.html", {"property": property})


def book_property(request, pk):
    Booking.release_departed_stays()
    property = get_object_or_404(Property, pk=pk, status=Property.Status.AVAILABLE)
    form = BookingForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        booking = form.save(commit=False)
        booking.property = property
        try:
            booking.full_clean()
        except Exception as error:
            form.add_error(None, error)
        else:
            booking.save()
            messages.success(request, "预订申请已提交，我们会尽快与您确认。")
            return redirect("listings:payment", pk=booking.pk, payment_token=booking.payment_token)
    return render(request, "listings/booking_form.html", {"property": property, "form": form})


def payment(request, pk, payment_token):
    booking = get_object_or_404(Booking.objects.select_related("property"), pk=pk, payment_token=payment_token)
    if booking.payment_status == Booking.PaymentStatus.PAID:
        return redirect("listings:booking_success", pk=booking.pk, payment_token=booking.payment_token)
    if booking.status == Booking.Status.CANCELLED:
        messages.error(request, "该订单已取消，无法继续支付。")
        return redirect("listings:home")
    return render(request, "listings/payment.html", {"booking": booking})


@require_POST
def confirm_payment(request, pk, payment_token):
    booking = get_object_or_404(Booking.objects.select_related("property"), pk=pk, payment_token=payment_token)
    try:
        booking.mark_paid()
    except ValidationError as error:
        messages.error(request, error.messages[0])
        return redirect("listings:payment", pk=booking.pk, payment_token=booking.payment_token)
    messages.success(request, "支付已登记，订单已自动确认。")
    return redirect("listings:booking_success", pk=booking.pk, payment_token=booking.payment_token)


def booking_success(request, pk, payment_token):
    booking = get_object_or_404(Booking, pk=pk, payment_token=payment_token)
    if booking.payment_status != Booking.PaymentStatus.PAID:
        return redirect("listings:payment", pk=booking.pk, payment_token=booking.payment_token)
    return render(request, "listings/booking_success.html", {"booking": booking})
