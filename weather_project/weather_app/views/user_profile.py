from weather_app.models import Location
from django.contrib.auth import login, authenticate
from .utils import get_location_params, render_user_profile


def user_profile(request):
    if request.method == 'GET':
        return render_user_profile(request)
    elif request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        # Verify user identity
        user = authenticate(username=username, password=password)
        if not user:
            return render_user_profile(
                request,
                error_message='Username and password do not match.')
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        clear_history = request.POST.get('clear_history')
        preserve_favorites = request.POST.get('preserve_favorites')
        delete_account = request.POST.get('delete_account')
        i_am_sure = request.POST.get('i_am_sure')
        if new_password1 or new_password2:
            # Change password
            if password != new_password1 == new_password2:
                user.set_password(new_password1)
                user.save()
                login(request, user)
                return render_user_profile(
                    request,
                    success_message='New password has been set successfully.')
            elif password == new_password1 == new_password2:
                return render_user_profile(
                    request,
                    error_message='New password must be different from the old one.')
            elif new_password1 != new_password2:
                return render_user_profile(
                    request,
                    error_message='New passwords do not match.')
        elif clear_history:
            # Delete location history
            if preserve_favorites:
                Location.objects.filter(
                    user=user,
                    is_favorite=False).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history except favorites has been deleted.')
            else:
                Location.objects.filter(user=user).delete()
                return render_user_profile(
                    request,
                    success_message='Your location history has been deleted completely.')
        elif delete_account and i_am_sure:
            # Delete user account
            user.delete()
            return render_user_profile(
                request,
                success_message='Your user account has been deleted completely.')
        else:
            # Invalid options
            return render_user_profile(
                request,
                error_message='Invalid options.')
