from django.urls import path
from . import views

app_name = 'cards'
urlpatterns = [
    path('', views.index, name='game'),
    path("<str:room_name>/", views.room, name="room"),
]