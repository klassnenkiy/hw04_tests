from http import HTTPStatus

from django.test import TestCase, Client

from posts.models import Group, Post, User


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
            group=cls.group,
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
            with self.subTest(address=address, template=template):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_public_url_exists_at_desired_location_for_anonym(self):
        """публичные адреса доступны неавторизованому клиенту"""
        url_names = (
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user_author}/',
            f'/posts/{self.post.pk}/',
        )
        for address in url_names:
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_private_url_exists_at_desired_location_for_auth(self):
        """закрытые адреса доступны авторизованому клиенту
        (создание поста, редактирование поста созданного этим же юзером)"""
        url_names = (
            '/create/',
            f'/posts/{self.post.pk}/edit/',
        )
        for address in url_names:
            with self.subTest():
                response = self.author_client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_not_author_redirect(self):
        """страница редактирования недоступна не-автору
        и редиректит на просмотр этого же поста"""
        response = self.authorized_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response,
            f'/posts/{self.post.pk}/',
            HTTPStatus.FOUND
        )

    def test_guest_redirect(self):
        """"закрытые" адреса (создание поста, редактирование поста)
        недоступны неавторизованому клиенту
        и вызывают редирект на страницу входа"""
        url_names = {
            f'/posts/{self.post.pk}/edit/':
            f'/auth/login/?next=/posts/{self.post.pk}/edit/',
            '/create/': '/auth/login/?next=/create/',
        }
        for address, redirect in url_names.items():
            with self.subTest(address=address, redirect=redirect):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect, HTTPStatus.FOUND)

    def test_unexisting_page_url_redirect(self):
        """несуществующий адрес недоступен"""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
