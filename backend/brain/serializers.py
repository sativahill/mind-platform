from rest_framework import serializers

from .models import Brain


PUBLIC_EDITABLE_SECTIONS = {
    "user",
}

class BrainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brain
        fields = [
            "id",
            "data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class BrainUpdateSerializer(serializers.Serializer):
    data = serializers.DictField()

    def validate_data(self, value):
        protected_sections = (
            set(value)
            - PUBLIC_EDITABLE_SECTIONS
        )

        if protected_sections:
            section_list = ", ".join(
                sorted(protected_sections)
            )
            raise serializers.ValidationError(
                "These Brain sections are system-owned: "
                f"{section_list}."
            )

        user_data = value.get("user")
        if (
            "user" in value
            and not isinstance(user_data, dict)
        ):
            raise serializers.ValidationError(
                "The user section must be an object."
            )

        return value
