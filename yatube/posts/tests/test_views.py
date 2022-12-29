from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post, User
from yatube.settings import COUNT_POSTS


class PostViewTest(TestCase):
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
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.author_client = Client()
        self.author_client.force_login(self.user_author)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.post.author}):
            'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.guest_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        self.assertEqual(len(response.context['page_obj'].object_list), 1)
        first_post = response.context['page_obj'][0]
        self.assertEqual(first_post, self.post)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)
        self.assertEqual(first_post.group, self.group)

    def test_group_show_correct_context(self):
        """Шаблон group сформирован с правильным контекстом."""
        response = self.guest_client.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})
        )
        group_object = response.context['group']
        self.assertIn('page_obj', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(group_object, self.group)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.author, self.post.author)

    def test_profile_show_correct_context(self):
        """Страница profile формируется с корректным контекстом."""
        response = self.guest_client.get(
            reverse('posts:profile', kwargs={'username': self.post.author})
        )
        author_object = response.context['author']
        self.assertIn('page_obj', response.context)
        first_post = response.context['page_obj'][0]
        self.assertEqual(author_object, self.user)
        self.assertEqual(first_post.text, self.post.text)
        self.assertEqual(first_post.group, self.post.group)
        self.assertEqual(first_post.pk, self.post.pk)

    def test_post_detail_show_correct_context(self):
        """Страница post_detail формируется с корректным контекстом."""
        response = self.guest_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk})
        )
        post_object = response.context['post']
        self.assertEqual(post_object, self.post)
        self.assertEqual(post_object.author, self.post.author)
        self.assertEqual(post_object.group, self.post.group)
        self.assertEqual(post_object.pk, self.post.pk)

    def test_post_edit_show_correct_context(self):
        """Страница post_edit формируется с корректным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)
        self.assertIn('form', response.context)
        post_object = response.context['post']
        self.assertEqual(post_object, self.post)
        self.assertTrue(response.context.get('is_edit'))

    # если проверять post и is_edit что-то не сообразил,
    # как объединить проверку post_edit c create в цикл, не слишком усложняя
    def test_create_post_show_correct_context(self):
        """Страница post_edit формируется с корректным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_in_group_on_pages(self):
        """Новый пост группы на главной, группе, профайле"""
        new_post = Post.objects.create(
            author=self.post.author,
            text='Новый пост группы',
            group=self.group
        )
        urls = [
            reverse('posts:index'),
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            )
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.author_client.get(url)
                last_post = response.context.get('page_obj')[0]
                self.assertEqual(last_post, new_post)

    def test_new_post_not_in_group_list(self):
        """Новый пост не попал в группу, для которой не был предназначен"""
        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='test_slug_2',
            description='С Наступающим Новым Годом!',
        )
        response = self.author_client.get(
            reverse(
                'posts:group', kwargs={'slug': another_group.slug}
            )
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        NUMBER_POSTS = 13
        cls.user = User.objects.create_user(username='auth')
        cls.user_author = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        for i in range(NUMBER_POSTS):
            cls.post = Post.objects.create(
                text=f'Тестовый пост номер {i}',
                author=cls.user,
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10"""
        urls = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ),
        )
        for url in urls:
            response = self.guest_client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, COUNT_POSTS)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста"""
        NUMBER_POSTS_ON_2ND_PAGE = 3
        urls = (
            reverse(
                'posts:index'
            ) + '?page=2',
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}
            ) + '?page=2',
            reverse(
                'posts:profile', kwargs={'username': self.post.author}
            ) + '?page=2',
        )
        for url in urls:
            response = self.guest_client.get(url)
            amount_posts = len(response.context.get('page_obj').object_list)
            self.assertEqual(amount_posts, NUMBER_POSTS_ON_2ND_PAGE)
