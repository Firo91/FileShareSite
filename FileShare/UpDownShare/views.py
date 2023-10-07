import os
from django.conf import settings
from django.core.files.storage import default_storage
from django.shortcuts import render, redirect, get_object_or_404
from .forms import FileUploadForm, CustomUserCreationForm, CustomPasswordResetForm, FolderUserRelationshipForm, FolderForm
from .models import File, CustomUser, FileUserRelationship, Folder, FolderUserRelationship
from django.http import FileResponse, HttpResponseNotAllowed, HttpResponse, HttpResponseRedirect, Http404, JsonResponse, HttpResponseBadRequest
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import  login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
import random
import string
from django.contrib import messages
import shutil
import logging

logger = logging.getLogger(__name__)

def home(request):
    return render(request, 'home.html')

@login_required
def file_upload_view(request):
    # Your initializations...
    file = None
    file_user_relationship = None

    # Handling POST request
    if request.method == 'POST':
        form = FileUploadForm(request.POST, request.FILES)
        folder_form = FolderForm(request.POST)

        # Handle file upload
        if form.is_valid():
            uploaded_files = request.FILES.getlist('file')
            folder = form.cleaned_data['folder']
            
            for uploaded_file in uploaded_files:
                # Check for file conflict...
                conflict = File.objects.filter(
                    user=request.user,
                    file=uploaded_file.name,
                    folder=folder
                ).exists()
                
                # If conflict and no resolution action provided, respond with conflict status...
                file_key = f"private/{uploaded_file.name}"  # Build the file key as per your S3 structure
                if file_exists_in_s3(settings.AWS_STORAGE_BUCKET_NAME, file_key) and not request.POST.get('action'):
                    return JsonResponse(
                        {'conflicting_file': uploaded_file.name},
                        status=409  # Conflict
                    )
                
                # Handle conflict resolution action...
                action = request.POST.get('action')
                if conflict and action == 'replace':
                    # Replace the existing file...
                    File.objects.filter(
                        user=request.user,
                        file=uploaded_file.name,
                        folder=folder
                    ).delete()
                    File.objects.create(user=request.user, file=uploaded_file, folder=folder)
                elif conflict and action == 'rename':
                    # Rename the uploaded file using request.POST.get('new_name')
                    new_name = request.POST.get('new_name')
                    if not new_name:
                        return HttpResponseBadRequest("New file name is required for rename action")
                    uploaded_file._name = new_name  # Be careful with modifying private attributes
                    File.objects.create(user=request.user, file=uploaded_file, folder=folder)
                elif not conflict:
                    # Save the uploaded file as is...
                    File.objects.create(user=request.user, file=uploaded_file, folder=folder)
                else:
                    return HttpResponseBadRequest("Invalid action")
            
            return JsonResponse({'message': 'File uploaded successfully.'}, status=200)
        
        # Handle folder creation
        elif folder_form.is_valid():
            name = folder_form.cleaned_data['name']
            parent_folder = folder_form.cleaned_data['parent_folder']
            
            folder = Folder.objects.create(user=request.user, name=name, parent_folder=parent_folder)
            return redirect('file_upload_download')

    # Handling GET request
    else:
        form = FileUploadForm()
        folder_form = FolderForm()

    uploaded_files = File.objects.all()
    folders = Folder.objects.all()
    
    # Only try to access file attributes if file exists
    if file and file.fileuserrelationship_set.filter(user=request.user).exists():
        file_user_relationship = file.fileuserrelationship_set.get(user=request.user)
    
    context = {
        'form': form,
        'folder_form': folder_form,
        'uploaded_files': uploaded_files,
        'folders': folders,
        'file': file,
        'file_user_relationship': file_user_relationship,
        'has_folders': Folder.objects.exists(),
    }

    return render(request, 'file_upload_download.html', context)


def move_file(request, file_id):
    file_instance = get_object_or_404(File, id=file_id)

    if request.method == 'POST':
        new_folder_id = request.POST.get('folder_id')  # Assuming you send the desired folder's ID in POST data
        new_folder = get_object_or_404(Folder, id=new_folder_id)

        # You can add any necessary permission checks here. E.g.:
        # - Check if the user has the right to move the file
        # - Check if the user has the right to put files in the destination folder

        file_instance.folder = new_folder  # Update the file's folder reference
        file_instance.save()

        # Redirect to the folder view or wherever you want after a successful move
        return redirect('file_upload_download')

    # If GET request, you can render a page where the user chooses the destination folder.
    folders = Folder.objects.filter(user=request.user)  # Show only folders belonging to the user
    return render(request, 'move_file.html', {'file': file_instance, 'folders': folders})

def folder_hierarchy_path(folder):
    # Recursively traverse the folder hierarchy to determine the path
    if folder.parent_folder:
        parent_path = folder_hierarchy_path(folder.parent_folder)
        return os.path.join(parent_path, folder.name)
    else:
        return folder.name

@login_required
def file_download(request, file_id):
    # Firstly, just get the file without checking the user
    uploaded_file = get_object_or_404(File, id=file_id)
    
    # Check if the file belongs to the current user
    if uploaded_file.user == request.user:
        pass
    # Else, check if the file is inside a shared folder
    elif uploaded_file.folder and FolderUserRelationship.objects.filter(folder=uploaded_file.folder, user=request.user).exists():
        pass
    else:
        # If neither conditions are met, raise a 404
        raise Http404("File not found or you don't have the permission to download it.")

    # Continue the download process
    uploaded_file_file = uploaded_file.file
    file_name = uploaded_file_file.name.split('/')[-1]
    response = FileResponse(uploaded_file_file.open(), as_attachment=True, filename=file_name)
    return response


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
def folder_view(request, folder_id, page=1):
    folder = get_object_or_404(Folder, id=folder_id)
    
    # Permission check
    if folder.user != request.user and not FolderUserRelationship.objects.filter(folder=folder, user=request.user).exists():
        messages.error(request, "You do not have permission to view this folder.")
        return redirect('file_upload_download')
    
    files = folder.file_set.all()

    # Get the FileUserRelationship objects for each file for the current user
    file_relations = {}
    for file in files:
        try:
            relation = file.fileuserrelationship_set.get(user=request.user)
            file_relations[file.id] = relation
        except FileUserRelationship.DoesNotExist:
            file_relations[file.id] = None

    # Breadcrumb
    breadcrumb = get_breadcrumb(folder)

    # Pagination
    files_per_page = 10
    paginator = Paginator(files, files_per_page)
    current_page = paginator.get_page(page)

    context = {
        'folder': folder,
        'breadcrumb': breadcrumb,
        'current_page': current_page,
        'file_relations': file_relations  # Passing the relationships to the template
    }

    return render(request, 'folder_view.html', context)

def get_breadcrumb(folder):
    if not folder.parent:
        return [folder]
    return get_breadcrumb(folder.parent) + [folder]

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

def delete_item(request, item_type, item_id):
    try:
        if item_type == 'file':
            file = get_object_or_404(File, pk=item_id)
            file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
            if default_storage.exists(file_path):
                default_storage.delete(file_path)
            file.delete()
            messages.success(request, "File deleted successfully.")

        elif item_type == 'folder':
            folder = get_object_or_404(Folder, pk=item_id)

            # Delete the associated files within the folder
            for file in folder.file_set.all():
                file_path = os.path.join(settings.MEDIA_ROOT, file.file.name)
                if default_storage.exists(file_path):
                    default_storage.delete(file_path)
            
            folder.delete()
            messages.success(request, "Folder deleted successfully.")
        else:
            messages.error(request, "Invalid item type provided.")
    except Exception as e:
        logger.error("Error during deletion: %s", str(e))
        messages.error(request, "An error occurred while trying to delete the item.")
        
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def share_folder(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(CustomUser, id=user_id)

        # Check if folder is already shared with this user
        if FolderUserRelationship.objects.filter(folder=folder, user=user).exists():
            messages.warning(request, f"Folder is already shared with {user.username}")
        else:
            relationship = FolderUserRelationship.objects.create(
                folder=folder,
                user=user,
            )
            messages.success(request, f"Folder successfully shared with {user.username}")

        return redirect('share_folder', folder_id=folder_id) # Redirecting to the same view to see the messages

    users = CustomUser.objects.all()

    # Get the list of users the folder is already shared with
    shared_with = [relation.user.username for relation in FolderUserRelationship.objects.filter(folder=folder)]

    context = {
        'folder': folder,
        'users': users,
        'shared_with': shared_with
    }
    return render(request, 'share_folder.html', context)

@login_required
def share_file(request, file_id):
    file = get_object_or_404(File, id=file_id)

    # Security check to ensure the requester is the owner of the file
    if file.user != request.user:
        messages.error(request, "You don't have permission to share this file.")
        return redirect('file_upload_download')  # Redirect to the main page or an appropriate page

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        user = get_object_or_404(CustomUser, id=user_id)

        can_delete = request.POST.get('can_delete') == "true"  # Retrieve the can_delete status from the POST data

        # Check if this file is already shared with this user
        if not FileUserRelationship.objects.filter(file=file, user=user).exists():
            FileUserRelationship.objects.create(file=file, user=user, can_delete=can_delete)  # Pass can_delete here
            messages.success(request, f"File shared with {user.username}.")
        else:
            messages.warning(request, f"File is already shared with {user.username}.")

    users = CustomUser.objects.all()

    # Get the list of users the file is already shared with
    shared_with = file.fileuserrelationship_set.all().values_list('user__username', flat=True)

    context = {
        'file': file,
        'users': users,
        'shared_with': shared_with
    }

    return render(request, 'share_file.html', context)

@login_required
def create_folder(request):
    if request.method == 'POST':
        folder_form = FolderForm(request.POST)
        if folder_form.is_valid():
            folder = folder_form.save(commit=False)
            folder.user = request.user
            folder.save()
            
            # Redirect to the file_upload_download view without folder_id argument
            return redirect('file_upload_download')
    else:
        folder_form = FolderForm()

    return render(request, 'file_upload_download.html', {'folder_form': folder_form})

def manage_shared_link(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)
    
    if request.method == 'POST' and 'user_id_to_remove' in request.POST:
        # If posting a user to remove
        user_id_to_remove = request.POST['user_id_to_remove']
        
        # Check if the folder is actually shared with the user using the intermediary model
        relationship = FolderUserRelationship.objects.filter(folder=folder, user_id=user_id_to_remove)

        if relationship.exists():
            relationship.delete()
            messages.success(request, "Shared link removed successfully!")
        else:
            messages.error(request, f"This folder is not shared with user {user_id_to_remove}!")
    
    return render(request, 'manage_shared_link.html', {'folder': folder})

def remove_my_shared_link(request, folder_id):
    folder = get_object_or_404(Folder, id=folder_id)

    # Check if the folder is actually shared with the user using the intermediary model
    relationship = FolderUserRelationship.objects.filter(folder=folder, user=request.user)
    
    if relationship.exists():
        relationship.delete()
        messages.success(request, "Shared link removed successfully!")
    else:
        messages.error(request, "This folder is not shared with you!")

    return redirect('file_upload_download')

def delete_shared_file(request, file_id):
    file= get_object_or_404(File, id=file_id)
    
    # Check if the user is actually a shared user for this file
    relationship = FileUserRelationship.objects.filter(file=file, user=request.user).first()

    if relationship:
        relationship.delete()  # This will remove only the sharing relationship, not the file itself
        messages.success(request, "Shared file removed successfully from your view.")
    else:
        messages.error(request, "This file is not shared with you!")
    
    return redirect('file_upload_download')
