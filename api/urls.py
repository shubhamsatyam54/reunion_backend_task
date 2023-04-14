from django.urls import path

from .views import *

urlpatterns = [
    path("authenticate/", authenticate),
    path("follow/<pk>", follow),
    path("unfollow/<pk>", follow),
    path("user/", user_det),
    path("posts/", new_post),
    path("posts/<pk>", post),
    path("like/<pk>", like),
    path("unlike/<pk>", unlike),
    path("comment/<pk>", comment),
    path("all_posts/", all_post),
]
