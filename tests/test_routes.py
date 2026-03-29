"""
Account API Service Test Suite

Test cases can be run with the following:
  nosetests -v --with-spec --spec-color
  coverage report -m
"""
import os
import logging
from unittest import TestCase
from tests.factories import AccountFactory
from service.common import status  # HTTP Status Codes
from service.models import db, Account, init_db
from service import talisman
from service.routes import app

DATABASE_URI = os.getenv(
    "DATABASE_URI", "postgresql://postgres:postgres@localhost:5432/postgres"
)

BASE_URL = "/accounts"
HTTPS_ENVIRON = {"wsgi.url_scheme": "https"}


######################################################################
#  T E S T   C A S E S
######################################################################
class TestAccountService(TestCase):
    """Account Service Tests"""

    @classmethod
    def setUpClass(cls):
        """Run once before all tests"""
        app.config["TESTING"] = True
        app.config["DEBUG"] = False
        app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URI
        app.logger.setLevel(logging.CRITICAL)
        talisman.force_https = False
        init_db(app)

    @classmethod
    def tearDownClass(cls):
        """Runs once before test suite"""

    def setUp(self):
        """Runs before each test"""
        db.session.query(Account).delete()  # clean up the last tests
        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Runs once after each test case"""
        db.session.remove()

    ######################################################################
    #  H E L P E R   M E T H O D S
    ######################################################################

    def _create_accounts(self, count):
        """Factory method to create accounts in bulk"""
        accounts = []
        for _ in range(count):
            account = AccountFactory()
            response = self.client.post(BASE_URL, json=account.serialize())
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                "Could not create test Account",
            )
            new_account = response.get_json()
            account.id = new_account["id"]
            accounts.append(account)
        return accounts

    ######################################################################
    #  A C C O U N T   T E S T   C A S E S
    ######################################################################

    def test_index(self):
        """It should get 200_OK from the Home Page"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_health(self):
        """It should be healthy"""
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.get_json()
        self.assertEqual(data["status"], "OK")

    def test_create_account(self):
        """It should Create a new Account"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Make sure location header is set
        location = response.headers.get("Location", None)
        self.assertIsNotNone(location)

        # Check the data is correct
        new_account = response.get_json()
        self.assertEqual(new_account["name"], account.name)
        self.assertEqual(new_account["email"], account.email)
        self.assertEqual(new_account["address"], account.address)
        self.assertEqual(new_account["phone_number"], account.phone_number)
        self.assertEqual(new_account["date_joined"], str(account.date_joined))

    def test_bad_request(self):
        """It should not Create an Account when sending the wrong data"""
        response = self.client.post(BASE_URL, json={"name": "not enough data"})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unsupported_media_type(self):
        """It should not Create an Account when sending the wrong media type"""
        account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=account.serialize(),
            content_type="test/html"
        )
        self.assertEqual(response.status_code, status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    # ADD YOUR TEST CASES HERE ...
    def test_read_an_account(self):
        """It should Read a single Account"""
        test_account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()
        account_id = new_account["id"]

        response = self.client.get(
            f"{BASE_URL}/{account_id}",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["id"], account_id)
        self.assertEqual(data["name"], test_account.name)
        self.assertEqual(data["email"], test_account.email)
        self.assertEqual(data["address"], test_account.address)
        self.assertEqual(data["phone_number"], test_account.phone_number)
        self.assertEqual(data["date_joined"], str(test_account.date_joined))


    def test_account_not_found(self):
        """It should not Read an Account that is not found"""
        response = self.client.get(
            f"{BASE_URL}/0",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_list_all_accounts(self):
        """It should List all Accounts"""
        account_list = []
        for _ in range(5):
            test_account = AccountFactory()
            response = self.client.post(
                BASE_URL,
                json=test_account.serialize(),
                content_type="application/json"
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            new_account = response.get_json()
            account_list.append(new_account)

        response = self.client.get(BASE_URL, content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(len(data), len(account_list))

    def test_update_account(self):
        """It should Update an existing Account"""
        test_account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()
        account_id = new_account["id"]

        updated_account = AccountFactory()
        response = self.client.put(
            f"{BASE_URL}/{account_id}",
            json=updated_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = response.get_json()
        self.assertEqual(data["id"], account_id)
        self.assertEqual(data["name"], updated_account.name)
        self.assertEqual(data["email"], updated_account.email)
        self.assertEqual(data["address"], updated_account.address)
        self.assertEqual(data["phone_number"], updated_account.phone_number)
        self.assertEqual(data["date_joined"], str(updated_account.date_joined))
    
    def test_update_account_not_found(self):
        """It should not Update an Account that is not found"""
        test_account = AccountFactory()
        response = self.client.put(
            f"{BASE_URL}/0",
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account(self):
        """It should Delete an Account"""
        test_account = AccountFactory()
        response = self.client.post(
            BASE_URL,
            json=test_account.serialize(),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_account = response.get_json()
        account_id = new_account["id"]

        response = self.client.delete(
            f"{BASE_URL}/{account_id}",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        response = self.client.get(
            f"{BASE_URL}/{account_id}",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_account_not_found(self):
        """It should Delete an Account even if it does not exist"""
        response = self.client.delete(
            f"{BASE_URL}/0",
            content_type="application/json"
        )
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_security_headers(self):
      """It should return security headers on the home page"""
      response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)
  
      self.assertEqual(response.status_code, status.HTTP_200_OK)
      self.assertEqual(response.headers["X-Frame-Options"], "SAMEORIGIN")
      self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
      self.assertEqual(
          response.headers["Content-Security-Policy"],
          "default-src 'self'; object-src 'none'"
      )
      self.assertEqual(
          response.headers["Referrer-Policy"],
          "strict-origin-when-cross-origin"
      )
    
    def test_cors_headers(self):
        """It should return CORS headers on the home page"""
        response = self.client.get("/", environ_overrides=HTTPS_ENVIRON)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.headers["Access-Control-Allow-Origin"], "*")
