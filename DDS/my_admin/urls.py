from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_home, name="main_home"),
    path('my_login/', views.my_login, name="my_login"),
    path('my_register/', views.my_register, name="my_register"),
    path('admin_dashboard/', views.admin_dashboard, name="admin_dashboard"),
    path('logout/', views.my_logout, name='my_logout'),
    # This path must exist to match the function in views.py
    path('get-vehicle-details/', views.get_vehicle_details, name='get_vehicle_details'),
]