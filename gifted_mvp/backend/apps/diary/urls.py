from django.urls import path

from .views import (
    CompanionDraftView,
    DiaryOverviewView,
    EntryDetailView,
    EntryListView,
    EntryPhotosView,
    PhotoDetailView,
)

urlpatterns = [
    path("diary/overview/", DiaryOverviewView.as_view(), name="diary-overview"),
    path("diary/entries/", EntryListView.as_view(), name="diary-entries"),
    path("diary/entries/<int:pk>/", EntryDetailView.as_view(), name="diary-entry"),
    path("diary/entries/<int:pk>/attachments/", EntryPhotosView.as_view(), name="diary-entry-attachments"),
    path("diary/attachments/<int:pk>/", PhotoDetailView.as_view(), name="diary-attachment"),
    path("diary/companion-draft/", CompanionDraftView.as_view(), name="diary-companion-draft"),
]
