from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.home, name="home"),
    path("management-entry/", views.management_entry, name="management_entry"),
    path("houses/<int:pk>/", views.property_detail, name="property_detail"),
    path("houses/<int:pk>/book/", views.book_property, name="book_property"),
    path("booking/<int:pk>/payment/<uuid:payment_token>/", views.payment, name="payment"),
    path("booking/<int:pk>/payment/<uuid:payment_token>/confirm/", views.confirm_payment, name="confirm_payment"),
    path("booking/success/<int:pk>/<uuid:payment_token>/", views.booking_success, name="booking_success"),
]
