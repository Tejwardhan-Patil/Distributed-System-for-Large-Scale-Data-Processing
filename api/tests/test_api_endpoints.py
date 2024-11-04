import unittest
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "https://website.com/api"
AUTH_USER = "nate"
AUTH_PASS = "password"

class TestAPIEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Common setup for all tests
        cls.auth = HTTPBasicAuth(AUTH_USER, AUTH_PASS)

    def test_get_root(self):
        """Test the root endpoint of the API"""
        response = requests.get(f"{BASE_URL}/", auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Welcome", response.text)

    def test_get_items(self):
        """Test fetching all items"""
        response = requests.get(f"{BASE_URL}/items", auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_post_create_item(self):
        """Test creating a new item"""
        payload = {
            "name": "NewItem",
            "description": "A new item created via the API",
            "price": 29.99
        }
        response = requests.post(f"{BASE_URL}/items", json=payload, auth=self.auth)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Item created successfully", response.text)

    def test_get_item(self):
        """Test fetching a single item by ID"""
        item_id = 1
        response = requests.get(f"{BASE_URL}/items/{item_id}", auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)
        self.assertEqual(response.json()["id"], item_id)

    def test_put_update_item(self):
        """Test updating an existing item"""
        item_id = 1
        payload = {
            "name": "UpdatedItem",
            "description": "An updated item description",
            "price": 39.99
        }
        response = requests.put(f"{BASE_URL}/items/{item_id}", json=payload, auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIn("Item updated successfully", response.text)

    def test_delete_item(self):
        """Test deleting an item by ID"""
        item_id = 1
        response = requests.delete(f"{BASE_URL}/items/{item_id}", auth=self.auth)
        self.assertEqual(response.status_code, 204)

    def test_unauthenticated_access(self):
        """Test accessing an endpoint without authentication"""
        response = requests.get(f"{BASE_URL}/items")
        self.assertEqual(response.status_code, 401)

    def test_invalid_credentials(self):
        """Test accessing an endpoint with invalid credentials"""
        wrong_auth = HTTPBasicAuth("paul", "wrong_password")
        response = requests.get(f"{BASE_URL}/items", auth=wrong_auth)
        self.assertEqual(response.status_code, 403)

    def test_pagination(self):
        """Test fetching paginated results"""
        params = {
            "page": 1,
            "size": 5
        }
        response = requests.get(f"{BASE_URL}/items", params=params, auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("items" in response.json())
        self.assertEqual(len(response.json()["items"]), 5)

    def test_sorting(self):
        """Test sorting items"""
        params = {
            "sort": "price",
            "order": "asc"
        }
        response = requests.get(f"{BASE_URL}/items", params=params, auth=self.auth)
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertTrue(all(items[i]['price'] <= items[i+1]['price'] for i in range(len(items) - 1)))

    def test_filter_by_category(self):
        """Test filtering items by category"""
        params = {
            "category": "electronics"
        }
        response = requests.get(f"{BASE_URL}/items", params=params, auth=self.auth)
        self.assertEqual(response.status_code, 200)
        items = response.json()["items"]
        self.assertTrue(all(item['category'] == 'electronics' for item in items))

    def test_rate_limiting(self):
        """Test the API rate limiting"""
        for _ in range(20):
            response = requests.get(f"{BASE_URL}/items", auth=self.auth)
        self.assertEqual(response.status_code, 429)

    def test_invalid_endpoint(self):
        """Test accessing an invalid endpoint"""
        response = requests.get(f"{BASE_URL}/invalid_endpoint", auth=self.auth)
        self.assertEqual(response.status_code, 404)

    def test_upload_image(self):
        """Test uploading an image file"""
        files = {'file': open('test_image.jpg', 'rb')}
        response = requests.post(f"{BASE_URL}/items/upload", files=files, auth=self.auth)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Image uploaded successfully", response.text)

    def test_get_item_image(self):
        """Test fetching an item's image"""
        item_id = 1
        response = requests.get(f"{BASE_URL}/items/{item_id}/image", auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/jpeg", response.headers['Content-Type'])

    def test_bulk_create_items(self):
        """Test bulk creation of items"""
        payload = [
            {"name": "Item1", "description": "First bulk item", "price": 10.99},
            {"name": "Item2", "description": "Second bulk item", "price": 12.99}
        ]
        response = requests.post(f"{BASE_URL}/items/bulk", json=payload, auth=self.auth)
        self.assertEqual(response.status_code, 201)
        self.assertIn("Items created successfully", response.text)

    def test_token_authentication(self):
        """Test token-based authentication"""
        token = "token"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(f"{BASE_URL}/items", headers=headers)
        self.assertEqual(response.status_code, 200)

    def test_search_items(self):
        """Test searching items by keyword"""
        params = {
            "q": "laptop"
        }
        response = requests.get(f"{BASE_URL}/items/search", params=params, auth=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.json()["items"]) > 0)

if __name__ == '__main__':
    unittest.main()