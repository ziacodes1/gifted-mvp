from rest_framework.pagination import PageNumberPagination


class DefaultPagination(PageNumberPagination):
    """20 items/page per spec; clients may override with ?page_size=."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
