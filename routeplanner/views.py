from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import RoutePlanRequestSerializer
from .ors_client import get_route_geojson, extract_route_info, RoutingError
from .utils import build_route_cumulative_miles, plan_fuel_stops


class RoutePlanView(APIView):
    """
    POST /api/route-plan/

    {
      "start": {"lat": 37.7749, "lng": -122.4194},
      "end":   {"lat": 34.0522, "lng": -118.2437}
    }
    """

    def post(self, request, *args, **kwargs):
        serializer = RoutePlanRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        start = serializer.validated_data["start"]
        end = serializer.validated_data["end"]
        start_coord = (start["lng"], start["lat"])
        end_coord = (end["lng"], end["lat"])

        try:
            geojson = get_route_geojson(start_coord, end_coord)
            distance_miles, duration_hours, coords = extract_route_info(geojson)
        except RoutingError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Build cumulative distances
        cum_miles = build_route_cumulative_miles(coords)

        # Plan fuel stops using station prices
        plan = plan_fuel_stops(
            total_distance_miles=distance_miles,
            route_coords=coords,
            cum_miles=cum_miles,
            vehicle_range_miles=500.0,
            mpg=10.0,
        )

        response_data = {
            "route": {
                "distance_miles": round(distance_miles, 2),
                "duration_hours": round(duration_hours, 2),
                "geometry": {
                    "type": "LineString",
                    "coordinates": coords,
                },
            },
            "vehicle": {
                "range_miles": 500,
                "mpg": 10,
            },
            "fuel_plan": {
                "total_gallons": plan["total_gallons"],
                "total_fuel_cost": plan["total_cost"],
                "stops": plan["stops"],
            },
        }

        return Response(response_data, status=status.HTTP_200_OK)
