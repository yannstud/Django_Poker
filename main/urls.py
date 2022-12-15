from django.urls import path
from . import views

app_name = "main"   


urlpatterns = [
    path("", views.login_request, name="homepage"),
    path("register", views.register_request, name="register"),
    path("logout", views.logout_request, name= "logout"),
]