from django.shortcuts import get_object_or_404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Book
from .serializers import BookSerializer
from .services import update_brain_from_book


class BookView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        books = Book.objects.filter(
            user=request.user
        )

        serializer = BookSerializer(
            books,
            many=True,
        )

        return Response(serializer.data)

    def post(self, request):
        serializer = BookSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        book = Book.objects.create(
            user=request.user,
            title=serializer.validated_data["title"],
            description=serializer.validated_data.get(
                "description",
                "",
            ),
            cover_url=serializer.validated_data.get(
                "cover_url",
                "",
            ),
            progress=serializer.validated_data.get(
                "progress",
                0,
            ),
            quotes=serializer.validated_data.get(
                "quotes",
                [],
            ),
            insights=serializer.validated_data.get(
                "insights",
                [],
            ),
            is_completed=serializer.validated_data.get(
                "is_completed",
                False,
            ),
        )

        update_brain_from_book(book)

        return Response(
            BookSerializer(book).data,
            status=201,
        )


class BookDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, book_id):
        book = get_object_or_404(
            Book,
            id=book_id,
            user=request.user,
        )

        serializer = BookSerializer(
            book,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save()

        update_brain_from_book(book)

        return Response(serializer.data)
