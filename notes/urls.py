from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create/', views.create_note_view, name='create_note'),
    path('notebook/<int:pk>/', views.editor_view, name='editor'),
    path('notebook/<int:pk>/save/', views.save_note, name='save_note'),
    path('notebook/<int:pk>/delete/', views.delete_note, name='delete_note'),
    path('notebook/<int:pk>/status/', views.update_note_status, name='update_note_status'),
    path('api/completion/', views.ai_completion, name='ai_completion'),
    path('api/summarize/', views.ai_summarize, name='ai_summarize'),
    path('api/auto_tag/', views.ai_auto_tag, name='ai_auto_tag'),
    path('api/add_tag/', views.add_tag, name='add_tag'),
    path('api/remove_tag/', views.remove_tag, name='remove_tag'),
]