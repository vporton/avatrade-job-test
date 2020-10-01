from django.urls import path

from socialuser import views

urlpatterns = [
    path('signup', views.SignupView.as_view()),
]
