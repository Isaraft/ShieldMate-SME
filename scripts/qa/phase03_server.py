# Test harness only, never imported by or shipped with the application.
from app.main import create_app
from app.config import Settings
app=create_app(Settings(environment='test',database_url='sqlite:////tmp/shieldmate-phase03-browser.db',trusted_origins=['http://127.0.0.1:15173']))
def fixture(hostname,expected,timeout):
    assert hostname.startswith('_shieldmate-challenge.') and expected.startswith('shieldmate-verification=')
    if hostname=='_shieldmate-challenge.qaowned.example.com':return 'match'
    if hostname=='_shieldmate-challenge.qapending.example.com':return 'not_found'
    return 'temporarily_unavailable'
app.state.check_txt=fixture
