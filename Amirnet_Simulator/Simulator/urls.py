from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("simulator",views.start_simulator, name="simulator"),
    path("upload",views.upload, name="upload"),
    path("save_test",views.save_test, name="save_test")
    # path("login", views.login, name="login"),
    # path("logout", views.logout_view, name="logout"),
    # path("register", views.register, name="register")
]
