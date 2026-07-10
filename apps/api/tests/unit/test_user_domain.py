from app.domain.entities.user import User


class TestUserDomain:
    def test_create_user(self):
        user = User.create(email="test@example.com", name="Test User")
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_active is True

    def test_update_profile(self):
        user = User.create(email="test@example.com", name="Original")
        user.update_profile(name="Updated", avatar_url="https://example.com/avatar.png")
        assert user.name == "Updated"
        assert user.avatar_url == "https://example.com/avatar.png"

    def test_deactivate_user(self):
        user = User.create(email="test@example.com", name="Test User")
        user.deactivate()
        assert user.is_active is False
