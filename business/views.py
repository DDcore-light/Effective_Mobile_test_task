from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.permissions import ResourcePermission


class BaseMockListView(APIView):
    permission_classes = [ResourcePermission]
    data_source = []

    def get(self, request):
        scope = getattr(request, "access_scope", "own")
        if scope == "all":
            items = self.data_source
        else:
            items = [i for i in self.data_source if i["owner"] == request.user.email]
        return Response({"scope": scope, "count": len(items), "results": items})

    def post(self, request):
        return Response(
            {"detail": "Mock-создание принято (объект не сохраняется, это заглушка)."},
            status=status.HTTP_201_CREATED,
        )


class BaseMockDetailView(APIView):
    permission_classes = [ResourcePermission]
    data_source = []

    def _find(self, pk):
        return next((i for i in self.data_source if i["id"] == pk), None)

    def _check_owner(self, request, obj):
        scope = getattr(request, "access_scope", "own")
        if scope == "all":
            return True
        return obj["owner"] == request.user.email

    def get(self, request, pk):
        obj = self._find(pk)
        if obj is None:
            return Response({"detail": "Не найдено."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_owner(request, obj):
            return Response(
                {"detail": "Нет доступа к чужому объекту."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(obj)

    def patch(self, request, pk):
        obj = self._find(pk)
        if obj is None:
            return Response({"detail": "Не найдено."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_owner(request, obj):
            return Response(
                {"detail": "Нет доступа к чужому объекту."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response({"detail": "Mock-обновление принято (не сохраняется).", "object": obj})

    def delete(self, request, pk):
        obj = self._find(pk)
        if obj is None:
            return Response({"detail": "Не найдено."}, status=status.HTTP_404_NOT_FOUND)
        if not self._check_owner(request, obj):
            return Response(
                {"detail": "Нет доступа к чужому объекту."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)
from business.data import ORDERS, PRODUCTS, STORES


class ProductListView(BaseMockListView):
    business_element = "products"
    data_source = PRODUCTS


class ProductDetailView(BaseMockDetailView):
    business_element = "products"
    data_source = PRODUCTS
class StoreListView(BaseMockListView):
    business_element = "stores"
    data_source = STORES


class StoreDetailView(BaseMockDetailView):
    business_element = "stores"
    data_source = STORES


class OrderListView(BaseMockListView):
    business_element = "orders"
    data_source = ORDERS


class OrderDetailView(BaseMockDetailView):
    business_element = "orders"
    data_source = ORDERS
