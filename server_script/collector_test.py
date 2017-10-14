import unittest
import collector

from unittest import mock

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa


# TODO(mohamedzouaghi): Add more tests to cover ssh_connect
class CollectorTest(unittest.TestCase):
  def setUp(self):
    self.private_key_example = rsa.generate_private_key(public_exponent=65537,
                                                        key_size=2048,
                                                        backend=default_backend())
    self.public_key_example = self.private_key_example.public_key()


  def test_valid_get_crypto_keys(self):
    calculated_private_key, calculated_public_key = collector.get_crypto_keys()
    self.assertEqual(isinstance(calculated_private_key, rsa.RSAPrivateKey), True)
    self.assertEqual(isinstance(calculated_public_key, rsa.RSAPublicKey), True)

  def test_valid_get_public_pem_data(self):
    calculated_pem = collector.get_public_pem_data(self.public_key_example)
    self.assertEqual(isinstance(calculated_pem, bytes), True)

  def test_empty_return_get_decrypted_output(self):
    with mock.patch('builtins.open', mock.mock_open(read_data=b'not equal to cipher')):
      resulting_plain_text = collector.get_decrypted_output(None,
                                                           self.private_key_example)
      self.assertEqual(resulting_plain_text, '')


if __name__ == '__main__':
  unittest.main()
