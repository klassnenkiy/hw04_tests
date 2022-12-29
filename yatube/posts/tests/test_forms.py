from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostFormTest(TestCase):
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

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_create_new_db(self):
        """Валидная форма создает запись"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост Тестовый пост',
            'group': self.group.pk,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user)
        self.assertEqual(post.group.pk, form_data['group'])

    def test_post_edit_change_db(self):
        """Происходит изменение поста с post_id в базе данных"""
        self.post = Post.objects.create(
            text='Текст поста для post_edit',
            author=self.user_author,
            group=PostFormTest.group,
        )
        self.another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='test_slug_2',
            description='Всё переплетено, но не предопределено',
        )
        form_data = {
            'text': 'Обновленный пост',
            'group': self.another_group.pk,
        }
        response = self.author_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            )
        )
        post = Post.objects.latest('id')
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.author, self.user_author)
        self.assertEqual(post.group.pk, form_data['group'])
