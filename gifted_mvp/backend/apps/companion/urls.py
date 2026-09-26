from django.urls import path

from .views import CompanionOverviewView, ConversationDetailView, ConversationListView, ConversationMessagesView

urlpatterns = [
    path("companion/overview/", CompanionOverviewView.as_view(), name="companion-overview"),
    path("companion/conversations/", ConversationListView.as_view(), name="companion-conversations"),
    path("companion/conversations/<int:pk>/", ConversationDetailView.as_view(), name="companion-conversation"),
    path(
        "companion/conversations/<int:pk>/messages/",
        ConversationMessagesView.as_view(),
        name="companion-conversation-messages",
    ),
]
