from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Expedition, ExpeditionMember
from authentication.models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'is_staff']
    search_fields = ['email', 'name']
    ordering = ['-created_at']

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('name', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2'),
        }),
    )


class ExpeditionMemberInline(admin.TabularInline):
    model = ExpeditionMember
    extra = 0
    readonly_fields = ['invited_at', 'confirmed_at']


@admin.register(Expedition)
class ExpeditionAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'chief', 'capacity', 'start_at', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'chief__email']
    ordering = ['-created_at']
    inlines = [ExpeditionMemberInline]


@admin.register(ExpeditionMember)
class ExpeditionMemberAdmin(admin.ModelAdmin):
    list_display = ['expedition', 'user', 'state', 'invited_at', 'confirmed_at']
    list_filter = ['state', 'invited_at']
    search_fields = ['expedition__title', 'user__email']