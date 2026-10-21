from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Note, Tag
import json

class MainFlowTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client.login(username='testuser', password='password')
        self.dashboard_url = reverse('dashboard')
        self.create_url = reverse('create_note')

    def test_dashboard_access(self):
        response = self.client.get(self.dashboard_url)
        self.assertEqual(response.status_code, 200)

    def test_create_note(self):
        data = {'title': 'New Test Note'}
        response = self.client.post(self.create_url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.first().title, 'New Test Note')

    def test_create_note_form_data(self):
        response = self.client.post(self.create_url, {'title': 'Form Note', 'use_ai_cover': 'false'})
        self.assertEqual(response.status_code, 200)
        note = Note.objects.filter(title='Form Note').first()
        self.assertIsNotNone(note)
        self.assertIsNone(note.image_url)

    def test_save_note(self):
        note = Note.objects.create(user=self.user, title='Draft')
        url = reverse('save_note', args=[note.id])
        data = {'content': '<p>Updated Content</p>'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.content, '<p>Updated Content</p>')

    def test_save_note_title(self):
        note = Note.objects.create(user=self.user, title='Old Title', content='Initial')
        url = reverse('save_note', args=[note.id])
        data = {'title': 'New Title', 'content': 'Changed Content'}
        response = self.client.post(url, json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.title, 'New Title')
        self.assertEqual(note.content, 'Changed Content')

    def test_delete_note(self):
        note = Note.objects.create(user=self.user, title='To Delete')
        url = reverse('delete_note', args=[note.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertTrue(note.is_trash)
        self.assertEqual(Note.objects.filter(is_trash=False).count(), 0)

    def test_editor_view(self):
        note = Note.objects.create(user=self.user, title='Editor Note')
        url = reverse('editor', args=[note.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Editor Note')

    def test_home_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'KnowledgeBin')


class AuthTest(TestCase):
    def test_signup(self):
        url = reverse('signup')
        data = {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'password123',
            'password2': 'password123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_signup_password_mismatch(self):
        url = reverse('signup')
        data = {
            'username': 'baduser',
            'email': 'bad@test.com',
            'password1': 'password123',
            'password2': 'mismatch123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='baduser').exists())

    def test_login(self):
        User.objects.create_user(username='loginuser', password='password123')
        url = reverse('login')
        data = {'username': 'loginuser', 'password': 'password123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(int(self.client.session['_auth_user_id']), User.objects.get(username='loginuser').id)

    def test_logout(self):
        User.objects.create_user(username='loginuser', password='password123')
        self.client.login(username='loginuser', password='password123')
        url = reverse('logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_authenticated_user_redirect_from_login_and_signup(self):
        User.objects.create_user(username='activeuser', password='password123')
        self.client.login(username='activeuser', password='password123')

        res_login = self.client.get(reverse('login'))
        self.assertEqual(res_login.status_code, 302)

        res_signup = self.client.get(reverse('signup'))
        self.assertEqual(res_signup.status_code, 302)


class ValidationAndSecurityTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password')
        self.user2 = User.objects.create_user(username='user2', password='password')
        self.client1 = Client()
        self.client1.login(username='user1', password='password')
        self.client2 = Client()
        self.client2.login(username='user2', password='password')
        self.anon_client = Client()

        self.note1 = Note.objects.create(user=self.user1, title='User1 Note', content='Secret')

    def test_create_note_empty_title_fails(self):
        url = reverse('create_note')
        res = self.client1.post(url, json.dumps({'title': '   '}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_create_note_invalid_json_fails(self):
        url = reverse('create_note')
        res = self.client1.post(url, "invalid-json{", content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_save_note_invalid_json_fails(self):
        url = reverse('save_note', args=[self.note1.id])
        res = self.client1.post(url, "not-a-json", content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_save_note_empty_payload_fails(self):
        url = reverse('save_note', args=[self.note1.id])
        res = self.client1.post(url, json.dumps({}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_user2_cannot_access_user1_editor(self):
        url = reverse('editor', args=[self.note1.id])
        res = self.client2.get(url)
        self.assertEqual(res.status_code, 404)

    def test_user2_cannot_save_user1_note(self):
        url = reverse('save_note', args=[self.note1.id])
        res = self.client2.post(url, json.dumps({'content': 'Hacked'}), content_type='application/json')
        self.assertEqual(res.status_code, 404)
        self.note1.refresh_from_db()
        self.assertEqual(self.note1.content, 'Secret')

    def test_user2_cannot_delete_user1_note(self):
        url = reverse('delete_note', args=[self.note1.id])
        res = self.client2.post(url)
        self.assertEqual(res.status_code, 404)
        self.note1.refresh_from_db()
        self.assertFalse(self.note1.is_trash)

    def test_user2_cannot_update_user1_status(self):
        url = reverse('update_note_status', args=[self.note1.id])
        res = self.client2.post(url, json.dumps({'action': 'trash'}), content_type='application/json')
        self.assertEqual(res.status_code, 404)
        self.note1.refresh_from_db()
        self.assertFalse(self.note1.is_trash)

    def test_unauthenticated_access_redirects(self):
        urls = [
            reverse('dashboard'),
            reverse('editor', args=[self.note1.id]),
        ]
        for u in urls:
            res = self.anon_client.get(u)
            self.assertEqual(res.status_code, 302)

    def test_update_status_invalid_action(self):
        url = reverse('update_note_status', args=[self.note1.id])
        res = self.client1.post(url, json.dumps({'action': 'unknown_action'}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_permanent_delete_on_non_trash_fails(self):
        url = reverse('update_note_status', args=[self.note1.id])
        res = self.client1.post(url, json.dumps({'action': 'delete_permanent'}), content_type='application/json')
        self.assertEqual(res.status_code, 400)
        self.assertTrue(Note.objects.filter(id=self.note1.id).exists())

    def test_pin_unarchives_archived_note(self):
        self.note1.is_archived = True
        self.note1.save()
        url = reverse('update_note_status', args=[self.note1.id])
        res = self.client1.post(url, json.dumps({'action': 'pin'}), content_type='application/json')
        self.assertEqual(res.status_code, 200)
        self.note1.refresh_from_db()
        self.assertTrue(self.note1.is_pinned)
        self.assertFalse(self.note1.is_archived)


class TagOperationsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='taguser', password='password')
        self.client = Client()
        self.client.login(username='taguser', password='password')
        self.note = Note.objects.create(user=self.user, title='Tag Note', content='Tag content')

    def test_add_and_remove_tag(self):
        add_url = reverse('add_tag')
        res = self.client.post(
            add_url,
            json.dumps({'note_id': self.note.id, 'tag_name': '#ideas'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.note.tags.count(), 1)
        tag = self.note.tags.first()
        self.assertEqual(tag.name, 'ideas')

        # Remove tag by tag_id
        remove_url = reverse('remove_tag')
        res = self.client.post(
            remove_url,
            json.dumps({'note_id': self.note.id, 'tag_id': tag.id, 'tag_name': 'ideas'}),
            content_type='application/json'
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.note.tags.count(), 0)

    def test_add_tag_missing_params(self):
        add_url = reverse('add_tag')
        res = self.client.post(add_url, json.dumps({}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_add_tag_invalid_json(self):
        add_url = reverse('add_tag')
        res = self.client.post(add_url, "{broken}", content_type='application/json')
        self.assertEqual(res.status_code, 400)


class AiEndpointsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='aiuser', password='password')
        self.client = Client()
        self.client.login(username='aiuser', password='password')

    def test_ai_completion_validation(self):
        url = reverse('ai_completion')
        # Empty prompt
        res = self.client.post(url, json.dumps({'prompt': ''}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # Invalid JSON
        res = self.client.post(url, "broken-json", content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_ai_summarize_validation(self):
        url = reverse('ai_summarize')
        # Empty content
        res = self.client.post(url, json.dumps({'content': ' '}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # Invalid JSON
        res = self.client.post(url, "broken-json", content_type='application/json')
        self.assertEqual(res.status_code, 400)

    def test_ai_auto_tag_validation(self):
        url = reverse('ai_auto_tag')
        # Empty content
        res = self.client.post(url, json.dumps({'content': ''}), content_type='application/json')
        self.assertEqual(res.status_code, 400)

        # Invalid JSON
        res = self.client.post(url, "broken-json", content_type='application/json')
        self.assertEqual(res.status_code, 400)
