import os
import sys

import paramiko
import argparse
import logging
import time

from random import randint

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization

from lib import storage
from lib import config


logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
global_logger = logging.getLogger(__name__)


def store_stats(ip_addr, stats, username, password):
  #stats has the format: os, cpu_usage, mem_usage, uptime, event_logs
  db = storage.Storage(username, password)
  db_row_id = db.store_machine_stats(ip_addr, stats.split(','))
  global_logger.info('Stats recorded: %s', db_row_id)


def get_crypto_keys():
  private_key = rsa.generate_private_key(public_exponent=65537,
                                         key_size=2048,
                                         backend=default_backend())
  public_key = private_key.public_key()
  return private_key, public_key

def get_public_pem_data(public_key):
  return public_key.public_bytes(encoding=serialization.Encoding.PEM,
                                format=serialization.PublicFormat.SubjectPublicKeyInfo)


def get_decrypted_output(encrypted_file, private_key):
  file = open(encrypted_file, 'rb')
  ciphertext = file.read()
  plaintext = ''
  try:
    plaintext = private_key.decrypt(ciphertext, padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                             algorithm=hashes.SHA256(), label=None))
  except ValueError as e:
    global_logger.error('Major issue happened with decryption: %s', e)

  return plaintext

def write_to_file(filename, content, mode):
  try:
    pk_file = open(filename, mode)
    pk_file.write(content)
    pk_file.close()
    return True
  except:
    global_logger.error('Error while writin to file')
    return False

# TODO(mohamedzouaghi): Refactor the ssh_connect function to make it shorter
def ssh_connect(machine, max_retry=config.DEFAULT_RETRY):
  # machine is of a type Client namedtuple
  ssh_client = paramiko.SSHClient()
  ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  retry = 0
  while retry <= max_retry:
    try:
      ssh_client.connect(machine.ip, int(machine.port), username=machine.username,
                         password=machine.password, timeout=4)
      break
    except (paramiko.ssh_exception.NoValidConnectionsError, OSError) as e:
      global_logger.warn('Issue wih ssh connection: %s.', e)
      if retry + 1 <= max_retry:
        sleep_duration = 30 + 30 * retry
        global_logger.warn('Sleeping for %d seconds before retrying.', sleep_duration)
        time.sleep(sleep_duration)
      retry += 1

  if retry > max_retry:
    fatal_error_msg = 'Fatal error with connection. Exiting.'
    global_logger.fatal(fatal_error_msg)
    sys.exit('Fatal error with connection. Exiting.')

  source_file_path = os.path.join('..', 'client_script')
  client_script = 'local_collector.py'
  # below is for linux only
  target_file_path = '/tmp/'
  # below to be removed only useful for debug
  target_client_script = client_script[:-3] + str(randint(0, 10000)) + client_script[-3:]
  local_copy_stats_results_filepath = 'encrypted_stats'


  private_key, public_key = get_crypto_keys()
  # pem_data is the serialization of the pubic_key to bytes so client machine can re-generate
  # the public key
  public_pem_data = get_public_pem_data(public_key)
  source_pk_filepath = 'public_keys' 
  pk_filename = 'pk_' + machine.ip + str(randint(0, 100000)) + '.pk'


  if not write_to_file(os.path.join(source_pk_filepath, pk_filename), public_pem_data, 'wb'):
    global_logger.fatal('Fatal error with public key storing. Exiting.')

  
  sftp = ssh_client.open_sftp()
  copy_pk_results = sftp.put(os.path.join(source_pk_filepath, pk_filename), os.path.join(target_file_path, pk_filename))
  global_logger.info('copy_pk_results: %s', copy_pk_results)

  sftp = ssh_client.open_sftp()
  sftp_results = sftp.put(os.path.join(source_file_path, client_script), os.path.join(target_file_path, target_client_script))
  global_logger.info('sftp_results: %s', sftp_results)

  # TODO(mohamedzouaghi): Need to change this so it suports Windows and MacOS
  command = 'python3 ' + target_file_path + target_client_script + ' -f ' + target_file_path + pk_filename
  stdin, stdout, stderr = ssh_client.exec_command(command)
  encrypted_remote_filename = stdout.read().decode('utf-8').rstrip()

  encrypted_local_name = os.path.join(local_copy_stats_results_filepath, encrypted_remote_filename.split('/')[-1].rstrip())

  global_logger.info('received stdout:\n%s\nReceived stderr:\n%s' % (encrypted_remote_filename, stderr.read()))
  copy_stats_results = sftp.get(encrypted_remote_filename, encrypted_local_name)
  decrypted_output = get_decrypted_output(encrypted_local_name, private_key)
  global_logger.info('received_output_aftr_decryption: %s', decrypted_output.decode('utf-8'))
  return decrypted_output.decode('utf-8')


def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--username', required=False, default=config.DEFAULT_USERNAME,
      help='username used for DB operations.')
  parser.add_argument('-p', '--password', required=False, default=config.DEFAULT_PASSWORD,
      help='username used for DB operations.')
  parser.add_argument('-r', '--retry', required=False, default=config.DEFAULT_RETRY, type=int,
      help='Numbr of ssh connection attempts in case first attemp fails. Eg: If 1, there will be on more attempt etc...')

  args = parser.parse_args()

  remote_machines = config.get_clients_details(include_alerts=False)
  for m in remote_machines:
    machine_stat = ssh_connect(m, max_retry=args.retry)
    store_stats(m.ip, (machine_stat), args.username, args.password)



if __name__ == '__main__':
  main()