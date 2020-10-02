from django.urls import path

from post import views

urlpatterns = [
    path('data', views.PostView.as_view()),
    path('like', views.LikeView.as_view()),
    path('unlike', views.UnlikeView.as_view()),
]
