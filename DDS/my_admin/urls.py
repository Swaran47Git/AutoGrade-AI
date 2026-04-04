from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.main_home, name="main_home"),
    path('login/', views.my_login, name="my_login"),
    path('register/', views.my_register, name="my_register"),
    path('logout/', views.my_logout, name='my_logout'),

    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('upload-analysis/', views.upload_images, name='upload_images'),
    path('claim-history/', views.claim_history, name='claim_history'),
    path('claim-details/<int:claim_id>/', views.claim_details, name='claim_details'),
    path('edit-claim/<int:claim_id>/', views.user_edit_claim, name='user_edit_claim'),

    path('submit-appeal/<int:claim_id>/', views.submit_appeal, name='submit_appeal'),
    path('admin-complaint/<int:claim_id>/', views.admin_complaint, name='admin_complaint'),

    path('agent-portal/', views.agent_dashboard, name='agent_dashboard'),
    path('review-claim/<int:claim_id>/', views.review_claim, name='review_claim'),
    path('manage-weights/', views.manage_part_weights, name='manage_weights'),

    path('system-admin/', views.admin_panel, name='admin_panel'),
    path('admin-complaints/', views.admin_complaints_view, name='admin_complaints_view'),
    path('user-detail/<int:profile_id>/', views.user_detail_view, name='user_detail'),
    path('grant-agent/<int:user_id>/', views.grant_agent_status, name='grant_agent_status'),

    path('get-vehicle-details/', views.get_vehicle_details, name='get_vehicle_details'),
    path('api_req/', views.api_req, name='api_req'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)