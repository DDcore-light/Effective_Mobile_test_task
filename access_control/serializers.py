from rest_framework import serializers

from access_control.models import AccessRule, BusinessElement
from users.models import Role


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["id", "name", "description"]


class BusinessElementSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessElement
        fields = ["id", "name", "description"]


class AccessRuleSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source="role.name", read_only=True)
    element_name = serializers.CharField(source="element.name", read_only=True)

    class Meta:
        model = AccessRule
        fields = [
            "id", "role", "role_name", "element", "element_name",
            "create_permission",
            "read_permission", "read_all_permission",
            "update_permission", "update_all_permission",
            "delete_permission", "delete_all_permission",
        ]
