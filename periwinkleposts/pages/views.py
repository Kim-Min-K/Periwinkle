from django.shortcuts import render
from accounts.models import Post
import commonmark
from django.utils.safestring import mark_safe


def homeView(request):
    user = request.user
    posts = Post.objects.all().order_by("-published")

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
