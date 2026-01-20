"""
Unit tests for the unified version control system

Tests cover:
- ChangeLogService functionality
- UndoRedoService functionality
- Model integrity and validations
- Transaction grouping
- Snapshot management
"""

import uuid
from django.test import TestCase
from django.contrib.auth.models import User
from pages.models import LandingPage, ChangeLog, UndoRedoStack, VersionSnapshot
from pages.services.changelog_service import (
    ChangeLogService,
    ChangeLogServiceError,
    UndoRedoService
)


class ChangeLogServiceTest(TestCase):
    """Tests for ChangeLogService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        self.page = LandingPage.objects.create(
            slug='test-page',
            title='Test Page',
            status='draft'
        )
        
        self.service = ChangeLogService(self.page)
    
    def test_create_single_change(self):
        """Test creating a single change log entry"""
        changelog = self.service.create_change(
            change_type='file_edit',
            content_before='old content',
            content_after='new content',
            target_path='css/style.css',
            user=self.user,
            note='Updated styles'
        )
        
        self.assertEqual(changelog.landing_page, self.page)
        self.assertEqual(changelog.change_type, 'file_edit')
        self.assertEqual(changelog.content_before, 'old content')
        self.assertEqual(changelog.content_after, 'new content')
        self.assertEqual(changelog.target_path, 'css/style.css')
        self.assertEqual(changelog.version, 1)
        self.assertEqual(changelog.created_by, self.user)
        self.assertEqual(changelog.note, 'Updated styles')
        
        # Verify content hash was generated
        self.assertIsNotNone(changelog.content_hash)
        self.assertEqual(len(changelog.content_hash), 64)  # SHA256 hash length
    
    def test_sequential_versions(self):
        """Test that versions are sequential"""
        changelog1 = self.service.create_change(
            change_type='file_edit',
            content_after='content 1'
        )
        
        changelog2 = self.service.create_change(
            change_type='file_edit',
            content_after='content 2'
        )
        
        self.assertEqual(changelog1.version, 1)
        self.assertEqual(changelog2.version, 2)
    
    def test_create_transaction(self):
        """Test creating multiple changes as a transaction"""
        changes = [
            {
                'change_type': 'file_edit',
                'content_before': 'old css',
                'content_after': 'new css',
                'target_path': 'css/style.css'
            },
            {
                'change_type': 'file_edit',
                'content_before': 'old js',
                'content_after': 'new js',
                'target_path': 'js/script.js'
            }
        ]
        
        transaction_id, changelogs = self.service.create_transaction(
            changes=changes,
            user=self.user,
            note='Updated styling and scripts'
        )
        
        self.assertEqual(len(changelogs), 2)
        
        # Verify all changes have the same transaction ID
        self.assertEqual(changelogs[0].transaction_id, transaction_id)
        self.assertEqual(changelogs[1].transaction_id, transaction_id)
        
        # Verify all have the same note
        self.assertEqual(changelogs[0].note, 'Updated styling and scripts')
        self.assertEqual(changelogs[1].note, 'Updated styling and scripts')
    
    def test_content_integrity_verification(self):
        """Test content integrity verification"""
        changelog = self.service.create_change(
            change_type='file_edit',
            content_after='test content'
        )
        
        # Integrity should be valid initially
        self.assertTrue(changelog.verify_integrity())
        
        # Corrupt the content
        changelog.content_after = 'corrupted content'
        
        # Integrity should now fail
        self.assertFalse(changelog.verify_integrity())
    
    def test_get_versions(self):
        """Test retrieving version history"""
        # Create multiple versions
        for i in range(5):
            self.service.create_change(
                change_type='file_edit',
                content_after=f'content {i}'
            )
        
        versions = self.service.get_versions(limit=3)
        
        self.assertEqual(len(versions), 3)
        # Should be in reverse order (newest first)
        self.assertEqual(versions[0].version, 5)
        self.assertEqual(versions[1].version, 4)
        self.assertEqual(versions[2].version, 3)
    
    def test_restore_version(self):
        """Test restoring to a specific version"""
        # Create some versions
        changelog1 = self.service.create_change(
            change_type='file_edit',
            content_after='version 1',
            target_path='test.txt'
        )
        
        changelog2 = self.service.create_change(
            change_type='file_edit',
            content_after='version 2',
            target_path='test.txt'
        )
        
        # Restore to version 1
        result = self.service.restore_version(1, user=self.user)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['content'], 'version 1')
        self.assertEqual(result['restored_from'], 1)
        
        # Verify a new changelog entry was created
        latest = ChangeLog.objects.filter(landing_page=self.page).latest('version')
        self.assertEqual(latest.note, 'Restored from version 1')
        self.assertEqual(latest.content_after, 'version 1')
    
    def test_create_snapshot(self):
        """Test creating a named snapshot"""
        # Create a version first
        self.service.create_change(
            change_type='file_edit',
            content_after='release content'
        )
        
        # Create snapshot
        snapshot = self.service.create_snapshot(
            name='Release 1.0.0',
            snapshot_type='release',
            description='First stable release',
            user=self.user,
            semver=(1, 0, 0, '')
        )
        
        self.assertEqual(snapshot.name, 'Release 1.0.0')
        self.assertEqual(snapshot.snapshot_type, 'release')
        self.assertEqual(snapshot.semver, '1.0.0')
        
        # Verify the changelog was marked as snapshot
        changelog = snapshot.changelog_version
        self.assertTrue(changelog.is_snapshot)
        self.assertEqual(changelog.snapshot_name, 'Release 1.0.0')
    
    def test_cleanup_old_versions(self):
        """Test automatic cleanup of old versions"""
        # Create more than MAX_VERSIONS_PER_PAGE
        for i in range(150):
            self.service.create_change(
                change_type='file_edit',
                content_after=f'content {i}'
            )
        
        # Should only keep MAX_VERSIONS_PER_PAGE (100)
        count = ChangeLog.objects.filter(
            landing_page=self.page,
            is_snapshot=False
        ).count()
        
        self.assertLessEqual(count, 100)
    
    def test_get_transaction_changes(self):
        """Test retrieving all changes in a transaction"""
        changes = [
            {'change_type': 'file_edit', 'content_after': 'css', 'target_path': 'style.css'},
            {'change_type': 'file_edit', 'content_after': 'js', 'target_path': 'script.js'},
        ]
        
        transaction_id, _ = self.service.create_transaction(changes=changes)
        
        transaction_changes = self.service.get_transaction_changes(transaction_id)
        
        self.assertEqual(len(transaction_changes), 2)
        self.assertEqual(transaction_changes[0].target_path, 'style.css')
        self.assertEqual(transaction_changes[1].target_path, 'script.js')


class UndoRedoServiceTest(TestCase):
    """Tests for UndoRedoService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        self.page = LandingPage.objects.create(
            slug='test-page',
            title='Test Page',
            status='draft'
        )
        
        self.changelog_service = ChangeLogService(self.page)
        self.undo_redo_service = UndoRedoService(
            self.page,
            self.user,
            'test-session'
        )
    
    def test_get_or_create_stack(self):
        """Test stack creation"""
        stack = self.undo_redo_service.get_or_create_stack()
        
        self.assertEqual(stack.landing_page, self.page)
        self.assertEqual(stack.user, self.user)
        self.assertEqual(stack.session_key, 'test-session')
        self.assertEqual(stack.undo_stack, [])
        self.assertEqual(stack.redo_stack, [])
    
    def test_push_transaction(self):
        """Test pushing transactions onto stack"""
        transaction_id = uuid.uuid4()
        
        self.undo_redo_service.push_transaction(transaction_id)
        
        stack = self.undo_redo_service.get_or_create_stack()
        
        self.assertEqual(len(stack.undo_stack), 1)
        self.assertEqual(stack.undo_stack[0], str(transaction_id))
        self.assertEqual(stack.redo_stack, [])
    
    def test_undo_operation(self):
        """Test undo operation"""
        # Create a transaction
        changes = [{
            'change_type': 'file_edit',
            'content_before': 'old',
            'content_after': 'new',
            'target_path': 'test.txt'
        }]
        
        transaction_id, changelogs = self.changelog_service.create_transaction(
            changes=changes,
            user=self.user
        )
        
        # Push to stack
        self.undo_redo_service.push_transaction(transaction_id)
        
        # Undo
        result = self.undo_redo_service.undo()
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], str(transaction_id))
        self.assertEqual(len(result['changes']), 1)
        self.assertEqual(result['changes'][0]['content'], 'old')
        
        # Verify stack state
        self.assertFalse(result['can_undo'])  # Nothing left to undo
        self.assertTrue(result['can_redo'])   # Can now redo
    
    def test_redo_operation(self):
        """Test redo operation"""
        # Create and undo a transaction
        changes = [{
            'change_type': 'file_edit',
            'content_before': 'old',
            'content_after': 'new',
            'target_path': 'test.txt'
        }]
        
        transaction_id, _ = self.changelog_service.create_transaction(
            changes=changes,
            user=self.user
        )
        
        self.undo_redo_service.push_transaction(transaction_id)
        self.undo_redo_service.undo()
        
        # Now redo
        result = self.undo_redo_service.redo()
        
        self.assertIsNotNone(result)
        self.assertTrue(result['success'])
        self.assertEqual(result['transaction_id'], str(transaction_id))
        self.assertEqual(len(result['changes']), 1)
        self.assertEqual(result['changes'][0]['content'], 'new')
        
        # Verify stack state
        self.assertTrue(result['can_undo'])   # Can undo again
        self.assertFalse(result['can_redo'])  # Nothing left to redo
    
    def test_multiple_undo_redo(self):
        """Test multiple undo/redo operations"""
        # Create multiple transactions
        for i in range(3):
            changes = [{
                'change_type': 'file_edit',
                'content_before': f'old {i}',
                'content_after': f'new {i}',
                'target_path': 'test.txt'
            }]
            
            transaction_id, _ = self.changelog_service.create_transaction(
                changes=changes,
                user=self.user
            )
            
            self.undo_redo_service.push_transaction(transaction_id)
        
        # Undo twice
        result1 = self.undo_redo_service.undo()
        result2 = self.undo_redo_service.undo()
        
        self.assertEqual(result1['changes'][0]['content'], 'old 2')
        self.assertEqual(result2['changes'][0]['content'], 'old 1')
        
        # Redo once
        result3 = self.undo_redo_service.redo()
        
        self.assertEqual(result3['changes'][0]['content'], 'new 1')
    
    def test_redo_stack_cleared_on_new_action(self):
        """Test that redo stack is cleared when a new action is performed"""
        # Create and undo a transaction
        transaction_id1 = uuid.uuid4()
        self.undo_redo_service.push_transaction(transaction_id1)
        self.undo_redo_service.undo()
        
        stack = self.undo_redo_service.get_or_create_stack()
        self.assertEqual(len(stack.redo_stack), 1)
        
        # Push a new transaction
        transaction_id2 = uuid.uuid4()
        self.undo_redo_service.push_transaction(transaction_id2)
        
        # Redo stack should be cleared
        stack.refresh_from_db()
        self.assertEqual(len(stack.redo_stack), 0)
    
    def test_get_stack_state(self):
        """Test retrieving stack state"""
        # Create a transaction
        transaction_id = uuid.uuid4()
        self.undo_redo_service.push_transaction(transaction_id)
        
        state = self.undo_redo_service.get_stack_state()
        
        self.assertTrue(state['can_undo'])
        self.assertFalse(state['can_redo'])
        self.assertEqual(state['undo_count'], 1)
        self.assertEqual(state['redo_count'], 0)
        self.assertEqual(state['last_action'], 'edit')


class ModelIntegrityTest(TestCase):
    """Tests for model integrity and validations"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        
        self.page = LandingPage.objects.create(
            slug='test-page',
            title='Test Page',
            status='draft'
        )
    
    def test_changelog_unique_version_per_page(self):
        """Test that version numbers are unique per page"""
        ChangeLog.objects.create(
            landing_page=self.page,
            version=1,
            change_type='file_edit',
            content_after='content'
        )
        
        # Should not allow duplicate version
        with self.assertRaises(Exception):  # IntegrityError
            ChangeLog.objects.create(
                landing_page=self.page,
                version=1,
                change_type='file_edit',
                content_after='content'
            )
    
    def test_snapshot_semver_property(self):
        """Test semantic version property"""
        changelog = ChangeLog.objects.create(
            landing_page=self.page,
            version=1,
            change_type='file_edit',
            content_after='content'
        )
        
        # With full semver
        snapshot1 = VersionSnapshot.objects.create(
            landing_page=self.page,
            name='v1.2.3',
            changelog_version=changelog,
            semver_major=1,
            semver_minor=2,
            semver_patch=3
        )
        
        self.assertEqual(snapshot1.semver, '1.2.3')
        
        # With prerelease
        changelog2 = ChangeLog.objects.create(
            landing_page=self.page,
            version=2,
            change_type='file_edit',
            content_after='content'
        )
        
        snapshot2 = VersionSnapshot.objects.create(
            landing_page=self.page,
            name='v2.0.0-beta',
            changelog_version=changelog2,
            semver_major=2,
            semver_minor=0,
            semver_patch=0,
            semver_prerelease='beta'
        )
        
        self.assertEqual(snapshot2.semver, '2.0.0-beta')
        
        # Without semver
        changelog3 = ChangeLog.objects.create(
            landing_page=self.page,
            version=3,
            change_type='file_edit',
            content_after='content'
        )
        
        snapshot3 = VersionSnapshot.objects.create(
            landing_page=self.page,
            name='backup',
            changelog_version=changelog3
        )
        
        self.assertEqual(snapshot3.semver, '')
