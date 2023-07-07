from django.urls import path
from django.conf import settings
from django.contrib.auth import views as auth_views
from django.conf.urls.static import static
from .views import create_folder, delete_item ,file_upload_download,change_password, file_download, register_user, home, custom_login, custom_logout, reset_password, folder_view, move_file, share_folder, share_file

urlpatterns = [
    path('', home, name='home'),
    path('login/', custom_login, name='custom_login'),
    path('logout/', custom_logout, name='logout'),
    path('files/', file_upload_download, name='file_upload_download'),
    path('file/download/<int:file_id>/', file_download, name='file_download'),
    path('register/', register_user, name='register'),
    path('login/reset_password/', reset_password, name='reset_password'),
    path('folder/<int:folder_id>/', folder_view, name='folder_view'),
    path('files/move/<int:file_id>/', move_file, name='move_file'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('change_password/', change_password, name='change_password'),
    path('delete/<str:item_type>/<int:item_id>/', delete_item, name='delete_item'),
    path('folder/<int:folder_id>/share/', share_folder, name='share_folder'),
    path('file/<int:file_id>/share/', share_file, name='share_file'),
    path('create_folder/', create_folder, name='create_folder'),
    # ...
]  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)