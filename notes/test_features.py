from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Note
import json

class FeatureTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.client = Client()
        self.client.login(username='testuser', password='password')
        self.note = Note.objects.create(user=self.user, title="Test Note", content="Content")

    def test_pin_note(self):
        response = self.client.post(
            f'/notes/notebook/{self.note.id}/status/',
            data=json.dumps({'action': 'pin'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_pinned)

    def test_archive_note(self):
        response = self.client.post(
            f'/notes/notebook/{self.note.id}/status/',
            data=json.dumps({'action': 'archive'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_archived)
        # Should be unpinned if archived
        self.assertFalse(self.note.is_pinned)

    def test_soft_delete(self):
        # Using the standard delete endpoint (which we modified to soft delete)
        response = self.client.post(f'/notes/notebook/{self.note.id}/delete/')
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_trash)

    def test_trash_action(self):
        # Using status endpoint
        response = self.client.post(
            f'/notes/notebook/{self.note.id}/status/',
            data=json.dumps({'action': 'trash'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertTrue(self.note.is_trash)

    def test_restore_note(self):
        self.note.is_trash = True
        self.note.save()
        
        response = self.client.post(
            f'/notes/notebook/{self.note.id}/status/',
            data=json.dumps({'action': 'restore'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.note.refresh_from_db()
        self.assertFalse(self.note.is_trash)

    def test_hard_delete(self):
        self.note.is_trash = True
        self.note.save()
        
        response = self.client.post(
            f'/notes/notebook/{self.note.id}/status/',
            data=json.dumps({'action': 'delete_permanent'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Note.objects.filter(id=self.note.id).exists())

    def test_dashboard_filtering(self):
        # Active
        response = self.client.get('/notes/dashboard/?filter=active')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Note")
        
        # Archive (move to archive first)
        self.note.is_archived = True
        self.note.save()
        response = self.client.get('/notes/dashboard/?filter=active')
        self.assertNotContains(response, "Test Note") # Shouldn't see it in active
        
        response = self.client.get('/notes/dashboard/?filter=archive')
        self.assertContains(response, "Test Note")
        
        # Trash
        self.note.is_archived = False
        self.note.is_trash = True
        self.note.save()
        response = self.client.get('/notes/dashboard/?filter=trash')
        self.assertContains(response, "Test Note")

    def test_dashboard_pagination(self):
        # Create 15 more notes to trigger pagination (12 per page)
        for i in range(15):
            Note.objects.create(user=self.user, title=f"Note {i}", content=f"Body {i}")

        response = self.client.get('/notes/dashboard/?page=2')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['page_obj'].has_previous())

    def test_dashboard_invalid_filter_fallback(self):
        response = self.client.get('/notes/dashboard/?filter=random_invalid_filter')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['filter_type'], 'active')
