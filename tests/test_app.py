import unittest

from app import app


class CMSTest(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_index(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("about.txt", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))
        self.assertIn("history.txt", response.get_data(as_text=True))

    def test_viewing_text_document(self):
        with self.client.get('/history.txt') as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("Python 0.9.0 (initial release) is released.",
                      response.get_data(as_text=True))

    def test_missing_document(self):
        with self.client.get('/hello.txt') as response:
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.location, '/')

        # flash message should display on next get request
        with self.client.get('/') as response:
            self.assertIn("hello.txt does not exist.",
                      response.get_data(as_text=True))

        # flash messge should be gone on subsequent requests
        with self.client.get('/') as response:
            self.assertNotIn("hello.txt does not exist.",
                      response.get_data(as_text=True))

    def test_missing_document(self):
        with self.client.get('/info.md') as response:
            self.assertIn("<h1>I am markdown!</h1>", response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
