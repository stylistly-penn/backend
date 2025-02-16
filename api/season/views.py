from rest_framework import viewsets, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, inline_serializer
from api.season.models import Season
from api.season.serializers import SeasonSerializer
from api.permissions import IsAdminOrReadOnly
from api.accounts.serializers import UserSerializer  # Import the UserSerializer


class SeasonViewSet(viewsets.ModelViewSet):
    queryset = Season.objects.all()
    serializer_class = SeasonSerializer
    permission_classes = [IsAdminOrReadOnly]

    @extend_schema(
        request=inline_serializer(
            name="SeasonUpdateRequest",
            fields={
                "season": serializers.CharField(
                    help_text="Name of the season to update the user's season with (e.g. 'Autumn')"
                )
            },
        ),
        responses=UserSerializer,
        description="""
            Updates the logged-in user's season.
            
            **Request body example:**
            {
                "season": "Autumn"
            }
            
            **Response example:**
            {
                "username": "testuser",
                "email": "",
                "season": {
                    "name": "Autumn",
                    "colors": [
                        {
                            "code": "[59 68 52]",
                            "color_id": 1
                        },
                        ...
                    ]
                }
            }
        """,
    )
    @action(
        detail=False,
        methods=["patch"],
        url_path="user_update",
        permission_classes=[IsAuthenticated],  # Overrides the default permission
    )
    def user_update(self, request):
        # Expect a JSON body with a "season" key containing the season name
        season_name = request.data.get("season")
        if not season_name:
            return Response(
                {"error": "Missing 'season' parameter in request body"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            season_obj = Season.objects.get(name=season_name)
        except Season.DoesNotExist:
            return Response(
                {"error": "Season not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update the logged-in user's season and save
        request.user.season = season_obj
        request.user.save()

        # Return the serialized user data using UserSerializer
        return Response(
            UserSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )
