from django.urls import path

from socialuser import views

urlpatterns = [
    path('data', views.UserView.as_view()),
    path('request-retrieve-data', views.RetrieveUserDataView.as_view()),
]
