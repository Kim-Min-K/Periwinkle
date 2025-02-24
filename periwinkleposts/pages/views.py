from django.shortcuts import render
from accounts.models import Post
import commonmark
from django.utils.safestring import mark_safe
from django.db.models import Q


def homeView(request):
    user = request.user
    
    # Get all posts that match visibility criteria
    posts = Post.objects.filter(is_deleted=False).order_by("-published")

    posts = posts.filter(
        Q(visibility="PUBLIC") |
        Q(visibility="UNLISTED") |
        Q(visibility="FRIENDS")
    )

    #convert content in posts where contentType == "text/markdown"
    for post in posts:
        if post.contentType == "text/markdown":
            post.content = markdown_to_html(post.content)

    context = {
        "username": user.username,
        "github_username": user.github_username,
        "posts": posts,
    }

    return render(request, "home.html", context)

def markdown_to_html(md_text):
    #use CommonMark functions to convert markdown to html
    parser = commonmark.Parser()
    renderer = commonmark.HtmlRenderer()
    return mark_safe(renderer.render(parser.parse(md_text)))
