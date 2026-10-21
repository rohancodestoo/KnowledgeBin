from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json

from .models import Note, Tag
from .forms import SignUpForm
from .utils import generate_image_description, generate_image, generate_completion, generate_summary, generate_tags
from django.core.paginator import Paginator


def home(request):
    return render(request, 'home.html')


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def dashboard(request):
    filter_type = request.GET.get('filter', 'active')
    if filter_type not in ('active', 'archive', 'trash'):
        filter_type = 'active'

    base_query = Note.objects.filter(user=request.user)

    if filter_type == 'trash':
        notes_list = base_query.filter(is_trash=True).order_by('-updated')
    elif filter_type == 'archive':
        notes_list = base_query.filter(is_archived=True, is_trash=False).order_by('-updated')
    else:
        notes_list = base_query.filter(is_trash=False, is_archived=False).order_by('-is_pinned', '-created')

    paginator = Paginator(notes_list, 12)  # 12 notes per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard.html', {
        'page_obj': page_obj,
        'filter_type': filter_type
    })


@login_required
@require_POST
def create_note_view(request):
    title = None
    use_ai_cover = False

    # Check if request is JSON
    content_type = request.content_type.lower() if request.content_type else ''
    if 'application/json' in content_type:
        try:
            data = json.loads(request.body)
            if isinstance(data, dict):
                title = data.get('title')
                use_ai_cover = bool(data.get('use_ai_cover'))
            else:
                return JsonResponse({'error': 'Invalid JSON format'}, status=400)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
    else:
        title = request.POST.get('title')
        use_ai_cover = request.POST.get('use_ai_cover') == 'true'

    cover_image = request.FILES.get('cover_image')

    if not title or not str(title).strip():
        return JsonResponse({'error': 'Title is required'}, status=400)

    title = str(title).strip()[:255]

    image_url = None
    if cover_image:
        # User explicitly uploaded a file
        pass
    elif use_ai_cover:
        try:
            description = generate_image_description(title)
            image_url = generate_image(description)
        except Exception as e:
            print(f"AI Image Gen Error: {e}")
            image_url = None

    note = Note.objects.create(
        user=request.user,
        title=title,
        image_url=image_url,
        cover_image=cover_image
    )

    return JsonResponse({'id': note.id, 'url': f'/notes/notebook/{note.id}/'})


@login_required
def editor_view(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    tags_data = [{'id': tag.id, 'name': tag.name} for tag in note.tags.all()]
    return render(request, 'editor.html', {
        'note': note,
        'tags_data': tags_data
    })


@login_required
@require_POST
def save_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    content = data.get('content')
    title = data.get('title')
    changed = False

    if content is not None:
        note.content = content
        changed = True

    if title is not None and str(title).strip():
        note.title = str(title).strip()[:255]
        changed = True

    if changed:
        note.save()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'No content or title provided'}, status=400)


@login_required
@require_POST
def delete_note(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    note.is_trash = True
    note.is_pinned = False
    note.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def update_note_status(request, pk):
    note = get_object_or_404(Note, pk=pk, user=request.user)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    action = str(data.get('action', '')).strip()

    allowed_actions = ('pin', 'unpin', 'archive', 'unarchive', 'trash', 'restore', 'delete_permanent')
    if action not in allowed_actions:
        return JsonResponse({'error': f'Invalid action: {action}'}, status=400)

    if action == 'pin':
        note.is_pinned = True
        if note.is_archived:
            note.is_archived = False
    elif action == 'unpin':
        note.is_pinned = False
    elif action == 'archive':
        note.is_archived = True
        note.is_pinned = False
    elif action == 'unarchive':
        note.is_archived = False
    elif action == 'trash':
        note.is_trash = True
        note.is_pinned = False
    elif action == 'restore':
        note.is_trash = False
        note.is_archived = False
    elif action == 'delete_permanent':
        if not note.is_trash:
            return JsonResponse({'error': 'Only notes in trash can be permanently deleted'}, status=400)
        note.delete()
        return JsonResponse({'success': True})

    note.save()
    return JsonResponse({'success': True})


@login_required
@require_POST
def ai_completion(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    prompt = data.get('prompt')
    if not prompt or not str(prompt).strip():
        return JsonResponse({'error': 'Prompt required'}, status=400)

    completion = generate_completion(str(prompt).strip())
    return JsonResponse({'completion': completion})


@login_required
@require_POST
def ai_summarize(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    content = data.get('content')
    if not content or not str(content).strip():
        return JsonResponse({'error': 'Content required'}, status=400)

    summary = generate_summary(str(content).strip())
    return JsonResponse({'summary': summary})


@login_required
@require_POST
def ai_auto_tag(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    content = data.get('content')
    if not content or not str(content).strip():
        return JsonResponse({'error': 'Content required'}, status=400)

    tags_list = generate_tags(str(content).strip())
    return JsonResponse({'tags': tags_list})


@login_required
@require_POST
def add_tag(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    note_id = data.get('note_id')
    tag_name = data.get('tag_name')

    if not note_id or not tag_name or not str(tag_name).strip():
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    note = get_object_or_404(Note, pk=note_id, user=request.user)

    cleaned_tag_name = str(tag_name).strip().lstrip('#').strip()[:50]
    if not cleaned_tag_name:
        return JsonResponse({'error': 'Invalid tag name'}, status=400)

    tag, _ = Tag.objects.get_or_create(user=request.user, name=cleaned_tag_name)
    note.tags.add(tag)

    return JsonResponse({'success': True, 'tag': {'name': tag.name, 'id': tag.id}})


@login_required
@require_POST
def remove_tag(request):
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({'error': 'Invalid JSON structure'}, status=400)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON payload'}, status=400)

    note_id = data.get('note_id')
    tag_name = data.get('tag_name')
    tag_id = data.get('tag_id')

    if not note_id or (not tag_name and not tag_id):
        return JsonResponse({'error': 'Missing parameters'}, status=400)

    note = get_object_or_404(Note, pk=note_id, user=request.user)

    if tag_id:
        try:
            tag = Tag.objects.get(user=request.user, pk=tag_id)
            note.tags.remove(tag)
            return JsonResponse({'success': True})
        except Tag.DoesNotExist:
            pass

    if tag_name:
        cleaned_tag_name = str(tag_name).strip().lstrip('#').strip()
        try:
            tag = Tag.objects.get(user=request.user, name=cleaned_tag_name)
            note.tags.remove(tag)
        except Tag.DoesNotExist:
            pass

    return JsonResponse({'success': True})