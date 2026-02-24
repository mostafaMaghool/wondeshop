from rest_framework import generics, permissions, mixins
from .serializers import *
from drf_spectacular.utils import extend_schema
from store.serializers import *
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import *
from store.models import *
from django.shortcuts import get_object_or_404
from rest_framework import status
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.views import APIView
from rest_framework.permissions import *
from rest_framework.generics import GenericAPIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from user.permissions import IsSuperOrSiteAdmin



# Mostafa

class UserDetailAPIView(mixins.RetrieveModelMixin,
                        mixins.UpdateModelMixin,
                        mixins.DestroyModelMixin,
                        generics.GenericAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    lookup_field = 'pk'

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.update(request, *args, **kwargs)

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        return self.destroy(request, *args, **kwargs)
    
    def get_permissions(self):
            if self.request.method in permissions.SAFE_METHODS:
                if self.request.user.is_staff:
                    return [IsSuperOrSiteAdmin()]
                return [permissions.IsAuthenticated()]

            pk = self.kwargs.get('pk')
            if str(pk) == str(self.request.user.pk):
                return [permissions.IsAuthenticated()]
            return [IsSuperOrSiteAdmin()]

    def get_object(self):
        obj = super().get_object()
        self.check_object_permissions(self.request, obj)
        return obj
    

class RegisterAPIView(
    mixins.CreateModelMixin,
    generics.GenericAPIView
):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        request=RegisterSerializer,
        responses={201: RegisterSerializer},
        description="User registration"
    )
    def post(self, request, *args, **kwargs):
        return self.create(request, *args, **kwargs)
    

class LoginAPIView(TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer

    @extend_schema(
        request=TokenObtainPairSerializer,
        responses={200: TokenObtainPairSerializer},
        description="JWT login"
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserProfleView(mixins.CreateModelMixin,generics.GenericAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get(self,request,*args,**kwargs):
        return Response(self.get_serializer(request.user).data)
    
    
@api_view(['GET'])
def profile_info(request, pk):
    try:
        profile = UserProfile.objects.get(user__pk=pk)
        serializer = UserProfileSerializer(profile)
    except UserProfile.DoesNotExist:
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
    return Response(serializer.data)


class UserPanelAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        cart = Cart.objects.filter(user=user).first()

        total_items = 0
        total_price = 0
        items = []

        if cart:
            for item in cart.items.all():
                total_items += item.quantity
                total_price += item.quantity * item.product.price

            items = CartSerializer(cart).data.get("items", [])

        return Response({
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone" : user.phone
            },
            "cart": {
                "id": cart.id if cart else None,
                # "is_active": cart.is_active if cart else False,
                "total_items": total_items,
                "total_price": total_price,
                "items": items
            }
        })
    
class ChangePasswordView(GenericAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={"request": request}
        )
        serializer.is_valid(raiseExceptions=True)
        serializer.save()
        return Response({"detail": "Password changed successfully!"})


class PasswordResetRequestView(GenericAPIView):
    serializer_class = PasswordResetRequestSerializer

    def post(self, request):
        serializer = self.get_serializer(
            data=request.data,
            context={
                "send_reset": nullcontext  # serializers send email TODO
            }
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Check your email, recovery email has been sent"})

class PasswordResetConfirmView(GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer


    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password reset successful"})


class LogoutView(GenericAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"detail": "User logged out"})