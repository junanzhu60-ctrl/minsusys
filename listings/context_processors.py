from .models import Booking


def pending_booking_count(request):
    """为后台顶部的新订单提醒提供待确认订单数。"""
    try:
        Booking.release_departed_stays()
        count = Booking.objects.filter(status=Booking.Status.PENDING).count()
    except Exception:
        # 首次部署或数据库迁移尚未完成时，后台仍可正常打开。
        count = 0
    return {"pending_booking_count": count}
