from django.urls import path
from .views import update_profile

urlpatterns = [
    path('update-profile/<int:pk>/', update_profile, name='update_profile'),
]
