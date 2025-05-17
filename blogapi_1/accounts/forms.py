from django.contrib.auth.forms import AdminUserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm):
            model = CustomUser
            fields = AdminUserCreationForm.Meta.fields + ("name",)

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
            model = CustomUser
            fields = UserChangeForm.Meta.fields
