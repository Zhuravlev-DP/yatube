import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings

from posts.models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test-user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.login_url = '/auth/login/'

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_post_create_form_authorized_client(self):
        """Тестирование создания нового поста"""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'text': 'Тестовый текст поста',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=self.group.pk,
            image='posts/small.gif',
        ).exists())

    def test_post_edit_form(self):
        """Тестирование изменения поста"""
        self.group2 = Group.objects.create(
            title='Тестовая группа2',
            slug='test-slug2',
            description='Тестовое описание2'
        )
        post_for_edit = Post.objects.create(
            author=self.user,
            text='Текст поста до редактирования',
            group=self.group
        )
        posts_count_before_edition = Post.objects.count()
        form_data = {
            'text': 'Текст поста после редактирования',
            'group': self.group2.pk,
        }
        response_post_edit = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_for_edit.pk}
            ),
            data=form_data,
            follow=True
        )
        posts_count_after_edition = Post.objects.count()
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        group_list_context = response_group_list.context['page_obj']
        group_list_paginator_count = group_list_context.paginator.count
        self.assertEqual(group_list_paginator_count, 0)
        self.assertRedirects(
            response_post_edit,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_for_edit.pk}
            )
        )
        self.assertEqual(posts_count_before_edition, posts_count_after_edition)
        self.assertTrue(Post.objects.filter(
            text=form_data['text'],
            group=form_data['group'],
            id=post_for_edit.pk
        ).exists())

    def test_post_create_form_guest_client(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст поста',
            'group': self.group.pk,
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            self.login_url
        )
        self.assertEqual(Post.objects.count(), posts_count)

    def test_add_comment_form_guest_client(self):
        comments_count = Comment.objects.count()
        post_for_comment = Post.objects.create(
            author=self.user,
            text='Текст поста до комментирования',
            group=self.group,
        )
        form_data = {
            'text': 'Комментарий',
            'post': post_for_comment.pk,
            'author': self.user,
        }
        response = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post_for_comment.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertRedirects(
            response,
            self.login_url
        )

    def test_add_comment_form_authorized_client(self):
        comments_count = Comment.objects.count()
        post_for_comment = Post.objects.create(
            author=self.user,
            text='Текст поста до комментирования',
            group=self.group,
        )
        form_data = {
            'text': 'Комментарий',
            'post': post_for_comment.pk,
            'author': self.user,
        }
        response = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post_for_comment.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': post_for_comment.pk}
            )
        )
        self.assertTrue(Comment.objects.filter(
            text=form_data['text'],
            post=form_data['post']
        ).exists())
