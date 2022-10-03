from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required

from posts.utils import get_paginator
from posts.models import Post, Group, User, Follow
from posts.forms import PostForm, CommentForm

TITLE_LENGHT = 30


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all()
    page_obj = get_paginator(post_list, request)
    context = {'page_obj': page_obj}
    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_obj = get_paginator(posts, request)
    context = {
        'group': group,
        'title': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=author)
    posts_cnt = posts.count()
    page_obj = get_paginator(posts, request)
    following = (request.user.is_authenticated
                 and Follow.objects.filter(
                     user=request.user,
                     author=author).exists())
    context = {
        'following': following,
        'author': author,
        'posts_cnt': posts_cnt,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    author_post = Post.objects.filter(author=post.author)
    post_count = author_post.count()
    title = post.text[:TITLE_LENGHT]
    context = {
        'post': post,
        'author_post': author_post,
        'post_count': post_count,
        'title': title,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required(redirect_field_name=None)
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)

    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user)

    return render(request, template, {'form': form})


@login_required(redirect_field_name=None)
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)

    if request.user != post.author:
        return redirect('posts:post_detail', post.pk)

    is_edit = True
    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post
    )

    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post.pk)

    template = 'posts/create_post.html'
    return render(request, template, {'form': form,
                  'is_edit': is_edit, 'post': post})


@login_required(redirect_field_name=None)
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required(redirect_field_name=None)
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = get_paginator(post_list, request)
    context = {'page_obj': page_obj}
    return render(request, template, context)


@login_required(redirect_field_name=None)
def profile_follow(request, username):
    if request.user != get_object_or_404(User, username=username):
        author = User.objects.get(username=username)
        if not Follow.objects.filter(
            user=request.user,
            author=author
        ).exists():
            Follow.objects.create(
                user=request.user,
                author=author
            )
    return redirect('posts:profile', username=username)


@login_required(redirect_field_name=None)
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        Follow.objects.filter(user=request.user, author=author).delete()
        return redirect('posts:profile', username=username)
    else:
        return redirect('posts:profile', username=username)
