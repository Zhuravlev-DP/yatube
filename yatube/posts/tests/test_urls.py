from http import HTTPStatus

from django.test import TestCase, Client

from posts.models import Post, Group, User


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(
            username='test-user'
        )
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test-slug',
            description='Тестовый текст',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.public_urls_templates = [
            ('/', 'posts/index.html'),
            ('/group/test-slug/', 'posts/group_list.html'),
            ('/profile/test-user/', 'posts/profile.html'),
            (f'/posts/{cls.post.pk}/', 'posts/post_detail.html'),
        ]
        cls.private_urls_templates = [
            ('/create/', 'posts/create_post.html'),
            (f'/posts/{cls.post.pk}/edit/', 'posts/create_post.html'),
        ]
        cls.unexisting_url = '/unexisting_page/'
        cls.unexisting_template = 'core/404.html'
        cls.login_url = '/auth/login/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_public_urls_exists_at_desired_locatione(self):
        for url, _ in self.public_urls_templates:
            with self.subTest(url=url):
                response_guest_client = self.guest_client.get(url)
                response_authorized_client = self.authorized_client.get(url)
                self.assertEqual(
                    response_guest_client.status_code,
                    HTTPStatus.OK.value
                )
                self.assertEqual(
                    response_authorized_client.status_code,
                    HTTPStatus.OK.value
                )

    def test_private_urls_exists_at_desired_location_authorized(self):
        for url, _ in self.private_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK.value)

    def test_private_urls_redirect_anonymous_on_login(self):
        for url, _ in self.private_urls_templates:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertRedirects(response, self.login_url)

    def test_public_urls_uses_correct_template(self):
        for url, template in self.public_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        for url, template in self.private_urls_templates:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page_works_correctly(self):
        response = self.guest_client.get(self.unexisting_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, self.unexisting_template)
