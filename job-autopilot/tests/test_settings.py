"""Unit tests for settings routes"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models import Setting


# Create test database
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


def override_get_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    """Create tables before each test"""
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)


class TestSettingsRoutes:
    """Tests for settings endpoints"""
    
    def test_get_settings_empty(self, client):
        """Test getting settings when none are configured"""
        response = client.get("/settings/api/data")
        assert response.status_code == 200
        data = response.json()
        
        assert data["llm_api_key_set"] is False
        assert data["telegram_bot_token_set"] is False
        assert data["browser_agent_provider"] == "manual"
        assert data["vacancy_fetch_interval_minutes"] == 30
    
    def test_save_llm_settings(self, client):
        """Test saving LLM configuration"""
        payload = {
            "llm_api_key": "sk-test123",
            "llm_base_url": "https://api.openai.com/v1",
            "llm_model": "gpt-4o"
        }
        
        response = client.post("/settings/api/save", json=payload)
        assert response.status_code == 200
        
        # Verify settings were saved
        with Session(engine) as session:
            api_key_setting = session.get(Setting, "LLM_API_KEY")
            assert api_key_setting is not None
            assert api_key_setting.value == "sk-test123"
            assert api_key_setting.is_secret is True
    
    def test_save_telegram_settings(self, client):
        """Test saving Telegram configuration"""
        payload = {
            "telegram_api_id": "12345678",
            "telegram_api_hash": "abc123def456",
            "telegram_bot_token": "123456:ABCdefGHIjklMNOpqrsTUVwxyz"
        }
        
        response = client.post("/settings/api/save", json=payload)
        assert response.status_code == 200
        
        # Verify settings were saved
        with Session(engine) as session:
            api_id = session.get(Setting, "TELEGRAM_API_ID")
            assert api_id is not None
            assert api_id.value == "12345678"
            assert api_id.is_secret is True
    
    def test_save_scheduler_settings(self, client):
        """Test saving scheduler configuration"""
        payload = {
            "vacancy_fetch_interval_minutes": 60,
            "telegram_monitor_interval_minutes": 10,
            "summary_interval_hours": 8
        }
        
        response = client.post("/settings/api/save", json=payload)
        assert response.status_code == 200
        
        # Reload and verify
        response = client.get("/settings/api/data")
        data = response.json()
        assert data["vacancy_fetch_interval_minutes"] == 60
        assert data["telegram_monitor_interval_minutes"] == 10
        assert data["summary_interval_hours"] == 8
    
    def test_save_browser_agent_provider(self, client):
        """Test saving browser agent provider setting"""
        payload = {
            "browser_agent_provider": "clipboard"
        }
        
        response = client.post("/settings/api/save", json=payload)
        assert response.status_code == 200
        
        # Reload and verify
        response = client.get("/settings/api/data")
        data = response.json()
        assert data["browser_agent_provider"] == "clipboard"
    
    def test_keep_existing_flag_prevents_overwrite(self, client):
        """Test that keep_existing flag prevents overwriting existing secrets"""
        # First save a secret
        payload1 = {
            "llm_api_key": "sk-original",
        }
        response = client.post("/settings/api/save", json=payload1)
        assert response.status_code == 200
        
        # Try to overwrite with keep_existing=True and empty value
        payload2 = {
            "llm_api_key": None,
            "llm_api_key_keep_existing": True
        }
        response = client.post("/settings/api/save", json=payload2)
        assert response.status_code == 200
        
        # Verify original value is preserved
        response = client.get("/settings/api/data")
        data = response.json()
        assert data["llm_api_key_set"] is True
    
    def test_settings_response_includes_set_flags(self, client):
        """Test that response includes _set flags for all secret fields"""
        # Save some settings
        payload = {
            "llm_api_key": "sk-test",
            "telegram_api_id": "123456",
            "telegram_bot_token": "token123"
        }
        client.post("/settings/api/save", json=payload)
        
        response = client.get("/settings/api/data")
        data = response.json()
        
        assert data["llm_api_key_set"] is True
        assert data["telegram_api_id_set"] is True
        assert data["telegram_bot_token_set"] is True
        assert data["telegram_api_hash_set"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
