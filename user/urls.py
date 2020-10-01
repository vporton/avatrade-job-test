from django.urls import path

from user import views

urlpatterns = [
    path('signup', views.SignupView.as_view()),
]
