import os
from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    username = models.CharField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    country = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.username
        
class Folder(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='folders')
    name = models.CharField(max_length=255)
    shared_with = models.ManyToManyField(CustomUser, through='FolderUserRelationship', related_name='shared_folders')
    
    def __str__(self):
        return self.name

    def folder_path(self):
        # Construct the path relative to MEDIA_ROOT
        return self.name
    
class FolderUserRelationship(models.Model):
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.folder} accessible by {self.user}'

class File(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='files')
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE, null=True, blank=True)
    file = models.FileField(upload_to='main/')
    created_at = models.DateField(auto_now_add=True)
    shared_with = models.ManyToManyField(CustomUser, through='FileUserRelationship', related_name='shared_files')

    def __str__(self):
        return self.file.name
    
class FileUserRelationship(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    shared_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return f'{self.file} shared with {self.user}'
