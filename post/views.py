from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from core.misc import MyAPIView
from post.models import Post


class PostView(MyAPIView):
    """It's a view about a social post, not about POST requests :-)"""

    def post(self, request):
        post = Post.objects.create(author=request.user,
                                   title=request.POST['title'],
                                   text=request.POST['text'],
                                   link=request.POST['link'] if 'link' in request.POST else None)
        return Response({'code': "OK", 'data': {'post_id': post.pk}})

class PostReadView(MyAPIView):
    permission_classes = [AllowAny]

    # TODO: Automatic test.
    def get(self, request):
        post = Post.objects.get(pk=request.GET['post_id'])
        data = {field: getattr(post, field) for field in ('author_id', 'title', 'text', 'link')}
        return Response({'code': "OK", 'data': data})


class LikeView(MyAPIView):
    """Repeated likes are ignored."""
    def post(self, request):
        post = Post.objects.get(pk=request.POST['post_id'])
        post.likes.add(request.user)
        return Response({'code': "OK"})


class UnlikeView(MyAPIView):
    """Repeated unlikes are ignored."""
    def post(self, request):
        post = Post.objects.get(pk=request.POST['post_id'])
        post.likes.remove(request.user)
        return Response({'code': "OK"})
