from uuid import uuid4

import pytest

from app.domain.entities.content.content import Content
from app.domain.exceptions.domain_exceptions import ValidationError


class TestContentDomain:
    def test_create_valid_content(self):
        org_id = uuid4()
        user_id = uuid4()
        content = Content.create(
            organization_id=org_id,
            title="Welcome Email Series",
            content_type="email",
            created_by=user_id,
        )
        assert content.title == "Welcome Email Series"
        assert content.content_type == "email"
        assert content.status == "draft"
        assert content.version == 1

    def test_create_content_empty_title_raises_error(self):
        with pytest.raises(ValidationError, match="Content title is required"):
            Content.create(organization_id=uuid4(), title="", content_type="blog", created_by=uuid4())

    def test_create_content_invalid_type_raises_error(self):
        with pytest.raises(ValidationError, match="Invalid content type"):
            Content.create(
                organization_id=uuid4(),
                title="Test",
                content_type="invalid_type",
                created_by=uuid4(),
            )

    def test_content_lifecycle(self):
        content = Content.create(
            organization_id=uuid4(),
            title="Blog Post",
            content_type="blog",
            created_by=uuid4(),
        )
        assert content.status == "draft"

        content.submit_for_review()
        assert content.status == "review"

        content.approve()
        assert content.status == "approved"

        content.publish()
        assert content.status == "published"
        assert content.published_at is not None

    def test_submit_for_review_from_wrong_status(self):
        content = Content.create(
            organization_id=uuid4(),
            title="Test",
            content_type="blog",
            created_by=uuid4(),
        )
        content.submit_for_review()
        content.approve()
        with pytest.raises(ValidationError, match="Cannot submit"):
            content.submit_for_review()

    def test_request_changes(self):
        content = Content.create(
            organization_id=uuid4(), title="Test", content_type="blog", created_by=uuid4()
        )
        content.submit_for_review()
        content.request_changes()
        assert content.status == "draft"

    def test_update_body_increments_version(self):
        content = Content.create(
            organization_id=uuid4(), title="Test", content_type="blog", created_by=uuid4()
        )
        assert content.version == 1
        content.update_body("New body content")
        assert content.version == 2
        assert content.body == "New body content"
