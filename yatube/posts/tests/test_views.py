import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, User, Comment, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test-user'
        )
        cls.user_2 = User.objects.create_user(
            username='test-user-2'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=cls.uploaded,
        )
        cls.comments = Comment.objects.create(
            author=cls.user,
            text='Тестовый комментарий',
            post=cls.post,
        )
        cls.reverse_urls_templates = {
            'index': {
                'url': reverse('posts:index'),
                'template': 'posts/index.html'
            },
            'group_list': {
                'url': reverse(
                    'posts:group_list',
                    kwargs={'slug': cls.group.slug}
                ),
                'template': 'posts/group_list.html'
            },
            'profile': {
                'url': reverse(
                    'posts:profile',
                    kwargs={'username': cls.user.username}
                ),
                'template': 'posts/profile.html'
            },
            'detail': {
                'url': reverse(
                    'posts:post_detail',
                    kwargs={'post_id': cls.post.pk}
                ),
                'template': 'posts/post_detail.html'
            },
            'create': {
                'url': reverse('posts:post_create'),
                'template': 'posts/create_post.html'
            },
            'edit': {
                'url': reverse(
                    'posts:post_edit',
                    kwargs={'post_id': cls.post.pk}
                ),
                'template': 'posts/create_post.html'
            },
        }
        cls.reverse_urls_templates_for_paginator = {
            'index': {
                'url': reverse('posts:index'),
                'template': 'posts/index.html'
            },
            'group_list': {
                'url': reverse(
                    'posts:group_list',
                    kwargs={'slug': cls.group.slug}
                ),
                'template': 'posts/group_list.html'
            },
            'profile': {
                'url': reverse(
                    'posts:profile',
                    kwargs={'username': cls.user.username}
                ),
                'template': 'posts/profile.html'
            },
        }
        cls.reverse_profile_follow_user = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user.username}
        )
        cls.reverse_profile_follow_user_2 = reverse(
            'posts:profile_follow',
            kwargs={'username': cls.user_2.username}
        )
        cls.reverse_profile_unfollow_user_2 = reverse(
            'posts:profile_unfollow',
            kwargs={'username': cls.user_2.username}
        )
        cls.reverse_follow_index = reverse('posts:follow_index')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_2 = Client()
        self.authorized_client_2.force_login(self.user_2)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for key in self.reverse_urls_templates:
            page_data = self.reverse_urls_templates[key]
            with self.subTest(reverse_name=key):
                response = self.authorized_client.get(page_data['url'])
                self.assertTemplateUsed(response, page_data['template'])

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['index']['url']
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object, self.post)
        self.assertEqual(first_object.image, self.post.image)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['group_list']['url']
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.group, self.post.group)
        self.assertEqual(first_object.image, self.post.image)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['profile']['url']
        )
        first_object = response.context['page_obj'][0]
        self.assertEqual(first_object.author, self.post.author)
        self.assertEqual(first_object.image, self.post.image)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['detail']['url']
        )
        first_object = response.context['author_post'][0]
        first_object_comments = response.context['comments'][0]
        self.assertEqual(first_object.pk, self.post.pk)
        self.assertEqual(response.context['author_post'].count(), 1)
        self.assertEqual(first_object.image, self.post.image)
        self.assertEqual(first_object_comments, self.comments)

    def test_post_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['create']['url']
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            self.reverse_urls_templates['edit']['url']
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_additional_page_show_correct_context(self):
        """Дополнительная проверка при создании поста."""
        self.group = Group.objects.create(
            title='Тестовый заголовок1',
            slug='test-slug1',
            description='Тестовый текст1',
        )
        self.post = Post.objects.create(
            author=self.user,
            text='Тестовый пост1',
            group=self.group,
        )
        response_index = self.authorized_client.get(
            self.reverse_urls_templates['index']['url']
        )
        response_profile = self.authorized_client.get(
            self.reverse_urls_templates['profile']['url']
        )
        response_group_list_new = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        response_group_list_old = self.authorized_client.get(
            self.reverse_urls_templates['group_list']['url']
        )
        index_object = response_index.context['page_obj']
        profile_object = response_profile.context['page_obj']
        group_list_new_object = response_group_list_new.context['page_obj']
        group_list_old_object = response_group_list_old.context['page_obj']
        self.assertIn(self.post, index_object)
        self.assertIn(self.post, profile_object)
        self.assertIn(self.post, group_list_new_object)
        self.assertNotIn(self.post, group_list_old_object)

    def test_page_paginator(self):
        post_count = Post.objects.count()
        paginator_amount = 10
        second_page_amount = post_count + 2
        amount_of_posts = 12
        post_list = [
            (Post(
                author=self.user,
                text=f'Тестовый пост{i}',
                group=self.group
            )
            )
            for i in range(amount_of_posts)
        ]
        Post.objects.bulk_create(post_list)
        page_amount_of_posts = (
            (1, paginator_amount),
            (2, second_page_amount)
        )
        for page, posts in page_amount_of_posts:
            for key in self.reverse_urls_templates_for_paginator:
                page_data = self.reverse_urls_templates_for_paginator[key]
                with self.subTest(reverse_name=key):
                    response = self.authorized_client.get(
                        page_data['url'], {'page': page}
                    )
                    self.assertEqual(len(response.context['page_obj']), posts)

    def test_cache_index(self):
        """Проверка кеша главной страницы."""
        cache.clear()
        response_before_delete_posts = self.authorized_client.get(
            self.reverse_urls_templates['index']['url']
        )
        Post.objects.all().delete
        resporesponse_after_delete_postsse2 = self.authorized_client.get(
            self.reverse_urls_templates['index']['url']
        )
        self.assertEqual(
            response_before_delete_posts.content,
            resporesponse_after_delete_postsse2.content
        )

    def test_following(self):
        """Проверка подписки/отписки на автора."""
        follow_count = Follow.objects.count()
        self.authorized_client.post(self.reverse_profile_follow_user)
        self.assertEqual(Follow.objects.count(), follow_count)
        self.authorized_client.post(self.reverse_profile_follow_user_2)
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.authorized_client.post(self.reverse_profile_unfollow_user_2)
        unfollow_count = Follow.objects.count()
        self.assertEqual(unfollow_count, follow_count)

    def test_new_post_following(self):
        """
        Проверка, что новая запись есть, где подписан,
        и нет, где не подписан.
        """
        self.authorized_client.post(self.reverse_profile_follow_user_2)
        new_post = Post.objects.create(
            text='Новый пост',
            author=self.user_2,
            group=self.group
        )
        response_client_is_signed = self.authorized_client.get(
            self.reverse_follow_index
        )
        self.assertIn(new_post, response_client_is_signed.context['page_obj'])
        response_client_is_not_signed = self.authorized_client_2.get(
            self.reverse_follow_index
        )
        self.assertNotIn(
            new_post,
            response_client_is_not_signed.context['page_obj']
        )
