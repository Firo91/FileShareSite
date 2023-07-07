from django.contrib import admin
from .models import CustomUser, Folder, File, FolderUserRelationship, FileUserRelationship

# Register your models here.

admin.site.register(CustomUser)
admin.site.register(Folder)
admin.site.register(File)
admin.site.register(FolderUserRelationship)
admin.site.register(FileUserRelationship)