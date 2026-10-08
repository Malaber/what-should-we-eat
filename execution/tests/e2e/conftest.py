import os
import threading
import time
import pytest
import uvicorn
import requests

# Set exactly the same environment variables as unit tests for consistency
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "e2e-test-secret-key-32-bytes-minimum"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"
os.environ["DEMO_HOUSEHOLD_ID"] = "99999"

from execution.db.database import Base, engine
from execution.api.main import app

@pytest.fixture(scope="session")
def server_url():
    """Start uvicorn server in a background thread."""
    class UvicornServer(uvicorn.Server):
        def install_signal_handlers(self):
            pass

    import logging
    logging.basicConfig(level=logging.ERROR, filename='/tmp/uvicorn.log', force=True)
    config = uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error", ws="none")
    server = UvicornServer(config)
    
    thread = threading.Thread(target=server.run)
    thread.daemon = True
    thread.start()
    
    # Wait for server to start and bind to a port
    port = None
    started = False
    for _ in range(50):
        if getattr(server, "servers", None) and getattr(server.servers[0], "sockets", None):
            port = server.servers[0].sockets[0].getsockname()[1]
            try:
                r = requests.get(f"http://127.0.0.1:{port}/health")
                if r.status_code == 200:
                    started = True
                    break
            except Exception:
                pass
        time.sleep(0.1)
    
    if not started or not port:
        server.should_exit = True
        thread.join()
        raise RuntimeError("E2E Test server could not start")
        
    os.environ["APP_BASE_URL"] = f"http://localhost:{port}"
    yield f"http://localhost:{port}"
    
    server.should_exit = True
    thread.join(timeout=2.0)

@pytest.fixture(autouse=True)
def _reset_tables():
    # Override the unit suite's in-memory schema fixture: real HTTP requests use
    # separate connections and must not share StaticPool's one SQLite connection.
    yield


@pytest.fixture(autouse=True)
def reset_db_data(tmp_path):
    from sqlalchemy import create_engine, event
    from sqlalchemy.orm import sessionmaker
    from execution.db.database import get_db
    test_engine = create_engine(f"sqlite:///{tmp_path / 'browser.db'}", connect_args={"check_same_thread": False})
    @event.listens_for(test_engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")
    Base.metadata.create_all(test_engine)
    factory = sessionmaker(bind=test_engine)
    def test_db():
        with factory() as session:
            yield session
    app.dependency_overrides[get_db] = test_db
    yield
    app.dependency_overrides.pop(get_db, None)
    test_engine.dispose()

@pytest.fixture
def page(context, server_url):
    """Override playwright's page fixture to automatically navigate to the server URL."""
    page = context.new_page()
    cdp = context.new_cdp_session(page)
    cdp.send("WebAuthn.enable")
    cdp.send("WebAuthn.addVirtualAuthenticator", {"options": {
        "protocol": "ctap2", "transport": "internal", "hasResidentKey": True,
        "hasUserVerification": True, "isUserVerified": True,
        "automaticPresenceSimulation": True,
    }})
    # Adding a custom helper to the page object
    page.base_url = server_url
    yield page
    page.close()

# Provide simulated mobile vs desktop. Pytest-playwright has built-in fixtures,
# but we can configure context globally or per-test if needed.
# Since the user wants to test mobile responsiveness, we'll configure
# some tests or fixtures specifically for mobile.
