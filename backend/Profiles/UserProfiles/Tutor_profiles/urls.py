from django.urls import path
from .views import update_tutor_profile

urlpatterns = [
    path('update-tutor-profile/<int:pk>/', update_tutor_profile, name='update_tutor_profile'),
]
