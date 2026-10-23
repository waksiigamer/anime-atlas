def test_search_uses_database_filters_and_accent_normalization(service):
    items, total = service.search(q="acao", year=[2025], dubbed=True, subbed=True)
    assert total == 1
    assert items[0]["id"] == "A1"
    assert items[0]["genres"] == ["Action", "Adventure"]


def test_multiselect_tag_and_descriptor_filters_use_intersection(service):
    assert service.search(tags=["action", "adventure"])[1] == 1
    assert service.search(tags=["action", "drama"])[1] == 1
    assert service.search(content_descriptor=["Violência", "Nudez"])[1] == 1
    assert service.search(content_descriptor=["Violência", "Nudez"], tags=["action"])[1] == 1


def test_filters_are_derived_from_normalized_database(service):
    filters = service.filters()
    assert filters["tags"] == ["Action", "Adventure", "Drama"]
    assert filters["maturity_ratings"] == ["12", "14", "16"]
    assert filters["years"] == [2025, 2024]


def test_pagination_and_sort(service):
    items, total = service.search(sort="title_desc", page=1, page_size=1)
    assert total == 3
    assert items[0]["title"] == "Outro"


def test_detail_returns_normalized_template_structure(service):
    detail = service.detail("A1")
    assert detail["series_metadata"]["episode_count"] == 12
    assert detail["series_metadata"]["tenant_categories"] == ["Action", "Adventure"]
    assert detail["rating"] == {"average": 4.5, "total": 20}
    assert detail["catalog_context"]["card_image"] == "tall"
    assert "sources" not in detail
