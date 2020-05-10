from django.urls import path
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .views import index

urlpatterns = [
    path('', csrf_exempt(index), name='update'),
]