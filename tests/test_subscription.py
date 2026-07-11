# tests for subscription functionality
import unittest
import json
from app import app
from services.subscription_service import create_subscription, is_subscription_valid

class SubscriptionTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Ensure a clean user for testing; normally you'd set up a test DB
        # For simplicity, we assume user 1 exists.
        self.user_id = 1
        # Create a free subscription (should always be valid)
        create_subscription(self.user_id, 'free', duration_days=0)

    def test_free_subscription_always_valid(self):
        self.assertTrue(is_subscription_valid(self.user_id, 'free'))
        self.assertTrue(is_subscription_valid(self.user_id, 'pro') is False)

    def test_pro_subscription_validation(self):
        # Upgrade to pro for 30 days
        create_subscription(self.user_id, 'pro', duration_days=30)
        self.assertTrue(is_subscription_valid(self.user_id, 'pro'))
        self.assertTrue(is_subscription_valid(self.user_id, 'premium') is False)

    def test_protected_endpoint(self):
        # Attempt to access premium analytics without proper tier
        response = self.app.get('/tasks/premium-analytics?user_id=' + str(self.user_id))
        self.assertEqual(response.status_code, 403)
        # Upgrade subscription
        create_subscription(self.user_id, 'pro', duration_days=30)
        response = self.app.get('/tasks/premium-analytics?user_id=' + str(self.user_id))
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('high_priority_pending', data)

if __name__ == '__main__':
    unittest.main()
