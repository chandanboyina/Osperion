import unittest
from app.extract import extract, normalize_url

class ExtractTests(unittest.TestCase):
    def test_structured_identifiers_and_username(self):
        text='''{"id":"6439661898","userID":"17841406416964957","username":"example_user","media_id":"3986677175125512082","url":"https://instagram.com/example_user"}'''
        r=extract(text)
        types={a['type'] for a in r['artifacts']}
        values={a['value'] for a in r['artifacts']}
        self.assertIn('profile_id',types)
        self.assertIn('username',types)
        self.assertIn('3986677175125512082',values)
    def test_url_normalization(self):
        self.assertEqual(normalize_url('https://cdn.example.com/a.jpg?sig=abc&x=1'), 'https://cdn.example.com/a.jpg')

if __name__=='__main__': unittest.main()
