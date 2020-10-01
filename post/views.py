from rest_framework.response import Response
from rest_framework.views import APIView

from post.models import Post


class PostView(APIView):
    """It's a view about a social post, not about POST requests :-)"""

    def post(self, request):
        # TODO: Error on a missing param
        post = Post.objects.create(author=request.user,
                                   title=request.POST['title'],
                                   text=request.POST['text'],
                                   link=request.POST['link'] if 'link' in request.POST['text'] else None)
        return Response({'post_id': post.pk})  # TODO


class LikeView(APIView):
    """Repeated likes are ignored. (TODO: correct behavior?)"""
    def post(self, request):
        post = Post.objects.get(pk=request.POST['post_id'])
        post.likes.add(request.user)
        return Response({})  # TODO

class UnlikeView(APIView):
    """Repeated unlikes are ignored. (TODO: correct behavior?)"""
    def post(self, request):
        post = Post.objects.get(pk=request.POST['post_id'])
        post.likes.remove(request.user)  # FIXME: what on removing second time?
        return Response({})  # TODO
