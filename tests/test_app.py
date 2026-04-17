import os
import shutil
import unittest

import yaml

from app import app


class CMSTest(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()
        self.data_path = os.path.join(os.path.dirname(__file__), 'data')
        os.makedirs(self.data_path, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.data_path, ignore_errors=True)

    def create_document(self, name, content=""):
        with open(os.path.join(self.data_path, name), 'w') as file:
            file.write(content)

    def create_user_file(self, username, password):
        with open(os.path.join(self.data_path, 'users.yml'), 'w') as file:
            file.write(yaml.dump({username: password}))

    def admin_session(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess['username'] = 'admin'
            return c

    def test_index(self):
        self.create_document("about.md")
        self.create_document("changes.txt")

        response = self.client.get('/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("about.md", response.get_data(as_text=True))
        self.assertIn("changes.txt", response.get_data(as_text=True))

    def test_viewing_text_document(self):
        self.create_document("history.txt",
                             "Python 0.9.0 (initial release) is released.")

        with self.client.get('/history.txt') as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, "text/plain; charset=utf-8")
            self.assertIn("Python 0.9.0 (initial release) is released.",
                          response.get_data(as_text=True))

    def test_document_not_found(self):
        # Attempt to access a nonexistent file and verify a redirect happens
        with self.client.get("/notafile.ext") as response:
            self.assertEqual(response.status_code, 302)

        # Verify redirect and message handling works
        with self.client.get(response.headers['Location']) as response:
            self.assertEqual(response.status_code, 200)
            self.assertIn("notafile.ext does not exist",
                          response.get_data(as_text=True))

        # Assert that a page reload removes the message
        with self.client.get("/") as response:
            self.assertNotIn("notafile.ext does not exist",
                             response.get_data(as_text=True))

    def test_viewing_markdown_document(self):
        self.create_document("about.md", "# Python is...")

        response = self.client.get('/about.md')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content_type, "text/html; charset=utf-8")
        self.assertIn("<h1>Python is...</h1>", response.get_data(as_text=True))

    def test_editing_document(self):
        self.create_document("changes.txt")
        self.admin_session()

        response = self.client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 200)
        self.assertIn("<textarea", response.get_data(as_text=True))

    def test_editing_document_signed_out(self):
        self.create_document("about.md", "# Python is...")
        response = self.client.get("/changes.txt/edit")
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn("You must be signed in",
                      follow_response.get_data(as_text=True))

    def test_updating_document(self):
        self.create_document("changes.txt")
        self.admin_session()
        response = self.client.post("/changes.txt/edit",
                                    data={'file_content': "new content"})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("changes.txt successfully updated",
                      follow_response.get_data(as_text=True))

        with self.client.get("/changes.txt") as content_response:
            self.assertEqual(content_response.status_code, 200)
            self.assertIn("new content",
                          content_response.get_data(as_text=True))

    def test_updating_document_signed_out(self):
        self.create_document("changes.txt")
        response = self.client.post("/changes.txt/edit",
                                    data={'file_content': "new content"})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.headers['Location'])
        self.assertIn("You must be signed in",
                      follow_response.get_data(as_text=True))

    def test_creating_new_document(self):
        self.admin_session()
        response = self.client.get('/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Create new document</label>',
                      response.get_data(as_text=True))

        response = self.client.post('/new',
                                    data={'new_file_name': 'hello.txt'})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertEqual(follow_response.status_code, 200)
        self.assertIn('hello.txt successfully created',
                      follow_response.get_data(as_text=True))

    def test_creating_new_document_signed_out(self):
        response = self.client.get('/new')
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn("You must be signed in",
                      follow_response.get_data(as_text=True))

    def test_creating_existing_document(self):
        self.create_document("hello.txt")
        self.admin_session()

        response = self.client.get('/new')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Create new document</label>',
                      response.get_data(as_text=True))

        response = self.client.post('/new',
                                    data={'new_file_name': 'hello.txt'})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertEqual(follow_response.status_code, 200)
        self.assertIn('hello.txt already exists',
                      follow_response.get_data(as_text=True))

    def test_creating_unnamed_document(self):
        self.admin_session()
        response = self.client.post('/new',
                                    data={'new_file_name': ''})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertEqual(follow_response.status_code, 200)
        self.assertIn('A file name is required',
                      follow_response.get_data(as_text=True))
        self.assertIn('Create new document</label>',
                      follow_response.get_data(as_text=True))

    def test_deleting_existing_document(self):
        self.admin_session()
        self.create_document("hello.txt")
        response = self.client.post('/hello.txt/delete')
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn('hello.txt successfully deleted',
                      follow_response.get_data(as_text=True))

    def test_deleting_nonexisting_document(self):
        self.admin_session()
        response = self.client.post('/hello.txt/delete')
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn('hello.txt does not exist',
                      follow_response.get_data(as_text=True))

    def test_deleting_document_signed_out(self):
        response = self.client.post('/hello.txt/delete')
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn("You must be signed in",
                      follow_response.get_data(as_text=True))

    def test_user_sign_in(self):
        self.create_user_file('test_user',
                              '$2b$12$m/rttWLM/kR8TUU5zD4K3uLuiwsvRH6Ghat0mY6tHTyVB/vLWVnny')
        response = self.client.get('/users/signin')
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/users/signin',
                                    data={'username': 'test_user',
                                          'password': 'password123'})
        self.assertEqual(response.status_code, 302)

        follow_response = self.client.get(response.location)
        self.assertIn('Welcome!', follow_response.get_data(as_text=True))

    def test_user_sign_in_invalid(self):
        self.create_user_file('test_user',
                              '$2b$12$m/rttWLM/kR8TUU5zD4K3uLuiwsvRH6Ghat0mY6tHTyVB/vLWVnny')
        response = self.client.post('/users/signin',
                                    data={'username': 'test_user',
                                          'password': 'badpassword'})
        self.assertEqual(response.status_code, 422)
        self.assertIn('Credentials are invalid', response.get_data(as_text=True))


if __name__ == '__main__':
    unittest.main()
