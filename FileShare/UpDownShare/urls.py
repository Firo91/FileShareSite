from django.urls import path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from. import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.custom_login, name='custom_login'),
    path('logout/', views.custom_logout, name='logout'),
    path('files/', views.file_upload_view, name='file_upload_download'),
    path('file/download/<int:file_id>/', views.file_download, name='file_download'),
    path('register/', views.register_user, name='register'),
    path('login/reset_password/', views.reset_password, name='reset_password'),
    path('folder/<int:folder_id>/', views.folder_view, name='folder_view'),
    path('files/move/<int:file_id>/', views.move_file, name='move_file'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('change_password/', views.change_password, name='change_password'),
    path('delete/<str:item_type>/<int:item_id>/', views.delete_item, name='delete_item'),
    path('folder/<int:folder_id>/share/', views.share_folder, name='share_folder'),
    path('file/<int:file_id>/share/', views.share_file, name='share_file'),
    path('create_folder/', views.create_folder, name='create_folder'),
    path('manage_shared_link/<int:folder_id>/', views.manage_shared_link, name='manage_shared_link'),
    path('remove_my_shared_link/<int:folder_id>/', views.remove_my_shared_link, name='remove_my_shared_link'),

    # ...
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)