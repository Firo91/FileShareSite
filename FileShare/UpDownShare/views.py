import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from .forms import FileUploadForm, CustomUserCreationForm, CustomPasswordResetForm, FolderUserRelationshipForm, FolderForm
from .models import File, CustomUser, FileUserRelationship, Folder, FolderUserRelationship
from django.http import FileResponse, HttpResponseNotAllowed, HttpResponse, HttpResponseRedirect
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import  login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.csrf import csrf_exempt
import random
import string
from django.contrib import messages
import shutil
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

@csrf_exempt
@login_required
def file_upload_download(request):
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        folder_form = FolderForm(request.POST)
        
        if form.is_valid():
            uploaded_file = form.cleaned_data['file']
            folder = form.cleaned_data['folder']
            
            file = File.objects.create(user=request.user, file=uploaded_file, folder=folder)
            return redirect('file_upload_download')
        elif folder_form.is_valid():
            name = folder_form.cleaned_data['name']
            parent_folder = folder_form.cleaned_data['parent_folder']
            
            folder = Folder.objects.create(user=request.user, name=name, parent_folder=parent_folder)
            return redirect('file_upload_download')
    else:
        form = FileUploadForm()
        folder_form = FolderForm()

    uploaded_files = File.objects.all()
    folders = Folder.objects.all()

    context = {
        'form': form,
        'folder_form': folder_form,
        'uploaded_files': uploaded_files,
        'folders': folders
    }

    return render(request, 'file_upload_download.html', context)


def move_file(request, file_id):
    file = get_object_or_404(File, pk=file_id)

    if request.method == 'POST':
        folder_id = request.POST.get('folder')
        folder = get_object_or_404(Folder, id=folder_id)

        # Get the current file path
        current_path = file.file.path

        # Get the file name and extension
        file_name = os.path.basename(current_path)

        # Generate the new file path based on the target folder's hierarchy
        new_folder_path = os.path.join(settings.MEDIA_ROOT, folder.folder_path())
        new_path = os.path.join(new_folder_path, file_name)

        # Create the destination folder if it doesn't exist
        os.makedirs(new_folder_path, exist_ok=True)

        # Move the file on the file system
        shutil.move(current_path, new_path)

        # Update the file's folder field in the database
        file.folder = folder
        file.save()

        return redirect('file_upload_download')
    else:
        return HttpResponseNotAllowed(['POST'])

def folder_hierarchy_path(folder):
    # Recursively traverse the folder hierarchy to determine the path
    if folder.parent_folder:
        parent_path = folder_hierarchy_path(folder.parent_folder)
        return os.path.join(parent_path, folder.name)
    else:
        return folder.name

@login_required
def file_download(request, file_id):
    uploaded_file = get_object_or_404(File, id=file_id, user=request.user)
    file_path = uploaded_file.file.path.replace('main', uploaded_file.folder.folder_path(), 1)
    file_name = uploaded_file.file.name.split('/')[-1]

    response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)

    return response

@csrf_exempt
def register_user(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            username = request.POST.get('username')
            name = request.POST.get('name')
            password1 = request.POST.get('password1')
            password2 = request.POST.get('password2')
            country = request.POST.get('country')

            if password1 == password2:
                user = form.save(commit=False)
                user.username = username
                user.name = name
                user.country = country
                user.set_password(password1)
                user.save()
                return redirect('custom_login')  # Redirect to the login page after successful registration
            else:
                # Handle password mismatch error
                return HttpResponse("Passwords do not match")
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

@csrf_exempt
def custom_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Authenticate the user
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # User credentials are correct, log in the user
            login(request, user)
            return redirect('file_upload_download')  # Replace 'equipment_search' with the URL name of your desired page

        else:
            error_message = 'Invalid name or password. Please try again.'

    else:
        error_message = ''

    return render(request, 'login.html', {'error_message': error_message})

def custom_logout(request):
    logout(request)
    return redirect('home')

@csrf_exempt
def reset_password(request):
    if request.method == 'POST':
        form = CustomPasswordResetForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            name = form.cleaned_data['name']
            
            try:
                user = CustomUser.objects.get(name=name, username=username)
            except CustomUser.DoesNotExist:
                user = None
            
            if user:
                # Generate a temporary password
                temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                
                # Update the user's password
                user.set_password(temp_password)
                user.save()
                
                messages.success(request, f'Temporary password: {temp_password}. Please login with this password and change it immediately.')
                return render(request, 'reset_password.html', {'form': form})
            else:
                messages.error(request, 'Invalid username or name.')
    else:
        form = CustomPasswordResetForm()
    
    return render(request, 'reset_password.html', {'form': form})

@login_required
@csrf_exempt
def folder_view(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    files = folder.file_set.all()

    context = {
        'folder': folder,
        'files': files
    }

    return render(request, 'folder_view.html', context)

@csrf_exempt
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(user=request.user, data=request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Update the session to prevent the user from being logged out
            messages.success(request, 'Your password has been successfully changed.')
            return redirect('file_upload_download')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(user=request.user)
    return render(request, 'change_password.html', {'form': form})

@csrf_exempt
def delete_item(request, item_type, item_id):
    if item_type == 'file':
        file = get_object_or_404(File, pk=item_id)


        file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
        if default_storage.exists(file_path):
            default_storage.delete(file_path)
        file.delete()

    if item_type == 'folder':
        folder = get_object_or_404(Folder, pk=item_id)
        folder_path = os.path.join(settings.MEDIA_ROOT, folder.name)

        # Delete the associated files within the folder
        for file in folder.file_set.all():
            file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
            if default_storage.exists(file_path):
                default_storage.delete(file_path)

        # Delete the folder and its contents
        if os.path.exists(folder_path):
            logger.info("Folder Path: %s", folder_path)  # Add this line to log the folder path
            shutil.rmtree(folder_path)

            

        folder.delete()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

@csrf_exempt
def share_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(CustomUser, id=user_id)
        relationship = FolderUserRelationship.objects.create(
            folder=folder,
            user=user,
        )
        # Handle success and redirect

    users = CustomUser.objects.all()
    return render(request, 'share_folder.html', {'folder': folder, 'users': users})

@csrf_exempt
def share_file(request, file_id):
    file = get_object_or_404(File, id=file_id)
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(CustomUser, id=user_id)
        relationship = FileUserRelationship.objects.create(
            file=file,
            user=user,
        )
        # Handle success and redirect

    users = CustomUser.objects.all()
    return render(request, 'share_file.html', {'file': file, 'users': users})

@csrf_exempt
def create_folder(request):
    if request.method == 'POST':
        folder_form = FolderForm(request.POST)
        if folder_form.is_valid():
            folder = folder_form.save(commit=False)
            folder.user = request.user

            # Create the folder on the file system
            folder_path = os.path.join(settings.MEDIA_ROOT, folder.folder_path())
            os.makedirs(folder_path, exist_ok=True)

            folder.save()

            return redirect('folder_view', folder_id=folder.id)
    else:
        folder_form = FolderForm()

    return render(request, 'file_upload_download.html', {'folder_form': folder_form})
