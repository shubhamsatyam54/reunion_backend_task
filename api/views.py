from datetime import datetime, timedelta

import jwt
from django.contrib.auth import authenticate
from django.db.utils import *
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import *

# Create your views here.



def jwt_required(view_func):
    def wrapper(request, *args, **kwargs):

        try:
            authorization_header = request.META.get('HTTP_AUTHORIZATION')
        except:
            return JsonResponse({'error': 'Authorization Header not found'}, status=401)

        try:
            token = authorization_header.split(' ')[1]
        except:
            return JsonResponse({'error': 'Missing token'}, status=401)

        try:
            user_details = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return JsonResponse({'error': 'Token has expired'}, status=401)
        except:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        user_id = user_details.get('user_id')
        if not user_id:
            return JsonResponse({'error': 'Invalid token'}, status=401)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=401)

        request.user = user
        return view_func(request, *args, **kwargs)

    return wrapper


@csrf_exempt
def api_authenticate(request):
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            if not username or not password:
                return JsonResponse({"error": "Invalid Input"}, status=406)
            user = authenticate(request, username=username, password=password)

            if user is not None:
                token = jwt.encode({
                    "user_id": user.id,
                    "exp": datetime.utcnow() + timedelta(hours=24),
                }, settings.SECRET_KEY, algorithm="HS256")

                response = JsonResponse({
                    "jwt_token": token
                }, status=202)

                return response

            return JsonResponse({"error": "invalid credentials"}, status=401)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def user_det(request):
    if request.method == "GET":
        user = request.user
        following = Followers.objects.filter(source=user).count()
        followers = Followers.objects.filter(target=user).count()
        data = {
            "username": user.username,
            "following": following,
            "followers": followers
        }

        return JsonResponse(data, status=200)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def new_post(request):
    if request.method == "POST":
        try:
            user = request.user
            title = request.POST.get('title')
            desc = request.POST.get('description')

            if not title or not desc:
                return JsonResponse({"error": "Invalid Input"}, status=400)

            post = Post.objects.create(title=title, description=desc, user=user)
            post.save()

            data = {
                "Post-ID": post.id,
                "Title": post.title,
                "Description": post.description,
                "Created At": post.created_at
            }

            return JsonResponse(data, status=201)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def post(request, pk):
    if request.method == "GET":
        try:
            post = Post.objects.get(pk=pk)
            num_likes = Like.objects.filter(post=post).count()
            num_comments = Comment.objects.filter(post=post).count()

            data = {
                "Post-ID": post.id,
                "Title": post.title,
                "Description": post.description,
                "Created At": post.created_at,
                "Created By": post.user.username,
                "Likes": num_likes,
                "Comments": num_comments
            }

            return JsonResponse(data, status=201)

        except Post.DoesNotExist:
            return JsonResponse({"Failed": f"Post with id : {pk} , does not exist"}, staus=404)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    if request.method == "DELETE":
        try:
            user = request.user
            post = Post.objects.get(pk=pk)
            if post.user == user:
                post.delete()
                return JsonResponse({"Success": "successfully deleted"}, status=204)
            else:
                return JsonResponse({"error": "Post does not belong to current user"}, staus=401)


        except Post.DoesNotExist:
            return JsonResponse({"Failed": f"Post with id : {pk} , does not exist"}, staus=404)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def follow(request, pk):
    if request.method == "POST":
        try:
            follower = request.user
            following = User.objects.get(pk=pk)
            follow = Followers.objects.create(source=follower, target=following)
            follow.save()

            return JsonResponse({"Success": "successfully followed"}, status=200)
        except IntegrityError:
            return JsonResponse({"Failed": "Already followed"}, status=406)
        except User.DoesNotExist:
            return JsonResponse({"Failed": f"User with id : {pk} , does not exist"}, status=404)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def unfollow(request, pk):
    if request.method == "POST":
        try:
            follower = request.user
            following = User.objects.get(pk=pk)
            follow = Followers.objects.get(source=follower, target=following)
            follow.delete()
            return JsonResponse({"Success": "successfully unfollowed"}, status=200)

        except User.DoesNotExist:
            return JsonResponse({"Failed": f"User with id : {pk} , does not exist"}, status=404)
        except Followers.DoesNotExist:
            return JsonResponse({"Failed": "Already unfollowed"}, status=406)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def like(request, pk):
    if request.method == "POST":
        try:
            user = request.user
            post = Post.objects.get(pk=pk)
            like = Like.objects.create(post=post, user=user)
            like.save()
            return JsonResponse({"Success": "successfully liked"}, status=200)

        except IntegrityError:
            return JsonResponse({"Failed": "Already liked"}, status=406)
        except Post.DoesNotExist:
            return JsonResponse({"Failed": f"Post with id : {pk} , does not exist"}, status=404)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def unlike(request, pk):
    if request.method == "POST":
        try:
            user = request.user
            post = Post.objects.get(pk=pk)
            like = Like.objects.get(post=post, user=user)
            like.delete()
            return JsonResponse({"Success": "successfully unliked"}, status=200)

        except Post.DoesNotExist:
            return JsonResponse({"Failed": f"Post with id : {pk} , does not exist"}, status=404)
        except Like.DoesNotExist:
            return JsonResponse({"Failed": "Already unliked"}, status=406)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)


@csrf_exempt
@jwt_required
def comment(request, pk):
    if request.method == "POST":
        try:
            user = request.user
            post = Post.objects.get(pk=pk)
            comment = request.POST.get('comment')
            if not comment:
                return JsonResponse({"error": "Invalid Input"}, status=400)

            com_obj = Comment.objects.create(user=user, post=post, comment=comment)
            com_obj.save()

            return JsonResponse({"Comment_ID": com_obj.id})

        except Post.DoesNotExist:
            return JsonResponse({"Failed": f"Post with id : {pk} , does not exist"}, status=404)
        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)



@csrf_exempt
@jwt_required
def all_post(request):
    if request.method == "GET":

        try:
            posts_data={}
            user = request.user
            posts = Post.objects.filter(user=user)
            i=1
            for post in posts:

                num_likes = Like.objects.filter(post=post).count()
                comments=Comment.objects.filter(post=post)
                comments = [comment.comment for comment in comments]

                data = {
                    "Post-ID": post.id,
                    "Title": post.title,
                    "Description": post.description,
                    "Created At": post.created_at,
                    "Likes": num_likes,
                    "Comments": comments
                }
                posts_data[i]=data
                i+=1

            return JsonResponse(dict(posts_data), status=201)

        except Exception as e:
            return JsonResponse({"error": e.__str__()}, status=500)

    return JsonResponse({"error": "Method Not Supported"}, status=405)