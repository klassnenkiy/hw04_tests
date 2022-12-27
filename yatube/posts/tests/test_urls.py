from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user_author}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_exists_at_desired_location(self):
        """Проверка доступа к страницам"""
        response_dict = {
            self.guest_client.get('/'): HTTPStatus.OK,
            self.guest_client.get(f'/group/{self.group.slug}/'):
            HTTPStatus.OK,
            self.guest_client.get(f'/profile/{self.user_author}/'):
            HTTPStatus.OK,
            self.guest_client.get(f'/posts/{self.post.pk}/'):
            HTTPStatus.OK,
            self.author_client.get(f'/posts/{self.post.pk}/edit/'):
            HTTPStatus.OK,
            self.guest_client.get(f'/posts/{self.post.pk}/edit/'):
            HTTPStatus.FOUND,
            self.authorized_client.get('/create/'): HTTPStatus.OK,
            self.guest_client.get('/create/'): HTTPStatus.FOUND,
            self.guest_client.get('/unexisting_page/'): HTTPStatus.NOT_FOUND,
        }
        for response, status_code in response_dict.items():
            with self.subTest(response=response):
                self.assertEqual(response.status_code, status_code)
