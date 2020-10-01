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
        post.likes.remove(request.user)  # FIXME: what on removing second time?
        return Response({'code': "OK"})
