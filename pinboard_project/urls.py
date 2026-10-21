from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from notes import views as note_views
from notes.forms import LoginForm

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 1. Root URL opens the Home Page
    path('', note_views.home, name='home'),
    
    path('signup/', note_views.signup_view, name='signup'),
    
    # Login View
    path('login/', auth_views.LoginView.as_view(
        template_name='login.html',
        authentication_form=LoginForm,
        redirect_authenticated_user=True
    ), name='login'),
    
    # 2. Logout redirects to 'home' (See view logic)
    path('logout/', note_views.logout_view, name='logout'),
    
    # Include the notes app URLs (dashboard, editor, etc.)
    path('notes/', include('notes.urls')),
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)