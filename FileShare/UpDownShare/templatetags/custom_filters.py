from django import template
from UpDownShare.models import FileUserRelationship

register = template.Library()

@register.filter(name='get_file_relationship')
def get_file_relationship(file_id, user_id):
    try:
        return FileUserRelationship.objects.get(file__id=file_id, user__id=user_id)
    except FileUserRelationship.DoesNotExist:
        return None