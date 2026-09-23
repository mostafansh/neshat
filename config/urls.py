from django.contrib import admin
from django.urls import path

from reading import views

urlpatterns = [
    path("", views.home, name="home"),
    path("m/demo/", views.demo_image, name="demo_image"),
    path("admin/", admin.site.urls),
]
