from django.test import TestCase

from posts.models import Group, Post, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост должен быть длиною более 15 символов',
        )

    def test_models_have_correct_object_names(self):
        fields_str = {
            self.post: self.post.text[:15],
            self.group: self.group.title,
        }
        for field, value in fields_str.items():
            with self.subTest(field=field):
                self.assertEqual(str(field), value)

    def test_help_text(self):
        field_help_text = [
            (self.post, 'group', 'Группа, к которой будет относиться пост'),
            (self.group, 'title', 'Заголовок группы'),
        ]
        for model, field, expected_value in field_help_text:
            with self.subTest(model=model):
                self.assertEqual(
                    model._meta.get_field(field).help_text,
                    expected_value
                )

    def test_verbose_name(self):
        field_verbose_name = [
            (self.post, 'group', 'Группа'),
            (self.group, 'title', 'Заголовок'),
        ]
        for model, field, expected_value in field_verbose_name:
            with self.subTest(model=model):
                self.assertEqual(
                    model._meta.get_field(field).verbose_name,
                    expected_value
                )
