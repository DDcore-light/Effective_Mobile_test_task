from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from access_control.models import AccessRule, BusinessElement
from access_control.serializers import (
    AccessRuleSerializer,
    BusinessElementSerializer,
    RoleSerializer,
)
from core.permissions import ResourcePermission
from users.models import Role


class RoleListView(APIView):
    business_element = "roles"
    permission_classes = [ResourcePermission]

    def get(self, request):
        qs = Role.objects.all()
        return Response(RoleSerializer(qs, many=True).data)

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BusinessElementListView(APIView):
    business_element = "business_elements"
    permission_classes = [ResourcePermission]

    def get(self, request):
        qs = BusinessElement.objects.all()
        return Response(BusinessElementSerializer(qs, many=True).data)

    def post(self, request):
        serializer = BusinessElementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccessRuleListView(APIView):
    business_element = "access_rules"
    permission_classes = [ResourcePermission]

    def get(self, request):
        qs = AccessRule.objects.select_related("role", "element").all()
        return Response(AccessRuleSerializer(qs, many=True).data)

    def post(self, request):
        serializer = AccessRuleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class AccessRuleDetailView(APIView):
    business_element = "access_rules"
    permission_classes = [ResourcePermission]

    def get_object(self, pk):
        return AccessRule.objects.select_related("role", "element").get(pk=pk)

    def get(self, request, pk):
        rule = self.get_object(pk)
        return Response(AccessRuleSerializer(rule).data)

    def patch(self, request, pk):
        rule = self.get_object(pk)
        serializer = AccessRuleSerializer(rule, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        rule = self.get_object(pk)
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
