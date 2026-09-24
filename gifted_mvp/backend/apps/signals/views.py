from rest_framework.generics import ListAPIView

from common.permissions.roles import IsStudent

from .models import LearnerSignal
from .serializers import LearnerSignalSerializer


class MySignalsView(ListAPIView):
    serializer_class = LearnerSignalSerializer
    permission_classes = [IsStudent]

    def get_queryset(self):
        return LearnerSignal.objects.filter(learner=self.request.user).select_related("signal")
