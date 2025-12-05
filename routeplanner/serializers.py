from rest_framework import serializers


class PointSerializer(serializers.Serializer):
    lat = serializers.FloatField()
    lng = serializers.FloatField()


class RoutePlanRequestSerializer(serializers.Serializer):
    start = PointSerializer()
    end = PointSerializer()

    def validate(self, data):
        for key in ("start", "end"):
            lat = data[key]["lat"]
            lng = data[key]["lng"]
            if not (24 <= lat <= 50 and -125 <= lng <= -66):
                raise serializers.ValidationError(
                    f"{key} must be within the continental USA bounds."
                )
        return data
