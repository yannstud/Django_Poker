from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('cards/', include('cards.urls')),
    path('', include('main.urls')),
]
