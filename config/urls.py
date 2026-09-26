from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path

from reading import api, views

urlpatterns = [
    path("", views.home, name="home"),
    # Accounts
    path("accounts/signup/", views.sign_up, name="signup"),
    path("accounts/signin/", auth_views.LoginView.as_view(template_name="accounts/signin.html"), name="signin"),
    path("accounts/signout/", auth_views.LogoutView.as_view(), name="signout"),
    # Studies (pages)
    path("projects/", views.projects, name="projects"),
    path("s/<slug:key>/", views.study_detail, name="study_detail"),
    path("s/<slug:key>/read/", views.read_page, name="study_read"),
    path("s/<slug:key>/done/", views.study_done, name="study_done"),
    # The reading screen's data calls (docs/reading-api.md) and case images
    path("api/s/<slug:key>/current", api.current, name="api_current"),
    path("api/p/<str:alias>/first", api.first_read, name="api_first"),
    path("api/p/<str:alias>/final", api.final_read, name="api_final"),
    path("i/<str:alias>/", api.case_image, name="case_image"),
    path("admin/", admin.site.urls),
]
