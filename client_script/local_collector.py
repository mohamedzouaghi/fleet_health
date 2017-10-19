#!/usr/bin/python3
# OR ENV??

import sys
import os
import psutil
import argparse
import datetime
import time

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend


OUTPUT_DATA_FILEPATH = '/tmp/data_output.txt'
# test

#ETRICS_MAPPING = {proc: ''}

def collect_cpu_usage(max_from_individual=False):
	# max_from_individual if true returns the percent of the max used CPU core
	# otherise it returns the total usage
	# To be implemented using percpu parameter
	return psutil.cpu_percent(interval=1)

def collect_mem_usage():
  # According to psutil documentation the best way to get th memory usage
  # is by calulating the 100% - avaiable/total rather than using directly
  # used / total
  # Documentation ref: https://pythonhosted.org/psutil/
  # interval needs to be checked
  memory = psutil.virtual_memory()
  if memory:
    return '%2.2f' % (memory.available / memory.total * 100)
  else:
  	return -1

def collect_uptime():
  now = datetime.datetime.now()
  current_timestamp = time.mktime(now.timetuple())
  return current_timestamp - psutil.boot_time()

def collect_event_logs():
  return 'empty'

def encrypt_text(message, public_key):
  #public_key = serialization.load_pem_public_key(public_pem_data, backend=default_backend())
  #print('debug public key: %s' % isinstance(public_key, rsa.RSAPublicKey))
  #return isinstance(public_key, rsa.RSAPublicKey)

  ciphertext = public_key.encrypt(message.encode('utf-8'), padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                        algorithm=hashes.SHA256(),
                                                        label=None))
  return ciphertext

def format_results(results, csv_char=','):
  # format according to csv format
  return csv_char.join(results)

def collect_sys_stats(public_key=None): #metrics
  os_family = os.name # or sys,platform
  # metrics is a list which contains the metrics that need to be collected
  #canonical_metrics = [m.lower() for m in metrics]
  #if 'cpu' in canonical_metrics:
  # return value is a tuple of the format: os, cpu_usage, mem_usage, uptime, event_logs
  cpu_usage = collect_cpu_usage()
  mem_usage = collect_mem_usage()
  uptime =  collect_uptime()
  event_logs = collect_event_logs() if os.name == 'nt' else 'empty'

  # need tocheck whether to use tuple or namedtuple or list or other...
  stats_results = format_results((os.name, str(cpu_usage), str(mem_usage), str(uptime), event_logs))
  #print('debug: %s, %s' % (str(cpu_usage), str(mem_usage)))
  #return cpu_usage, mem_usage
  if public_key:
    return encrypt_text(stats_results, public_key)
  else:
    return stats_results

def get_public_key(pk_file):
  pk_file = open(pk_file, 'rb')
  public_pem_data = pk_file.read()#.encode('utf-8')
  public_key = serialization.load_pem_public_key(public_pem_data, backend=default_backend())
  return public_key

def write_data_to_file(data, data_filepath):
  data_file = open(data_filepath, 'wb')
  data_file.write(data)
  #print(data)
  return data_filepath

def main():
  parser = argparse.ArgumentParser()
  parser.add_argument('-p', '--public_pem_data', required=False,
                      help='Public pem data to be used to generate the public key that will be'
                           ' used to encrypt output.')

  parser.add_argument('-f', '--public_key_file', required=True,
                      help='File that containt the public key that will be used to encrypt output.')
  parser.add_argument('-o', '--output_data_file', required=False, default=OUTPUT_DATA_FILEPATH,
                      help='File that containt the public key that will be used to encrypt output.')
  #parser.add_argument('public_pem_data')

  args = parser.parse_args()
  clean_public_pem_data = None

  if args.public_pem_data:
    clean_public_pem_data = args.public_pem_data.encode('utf-8')#[1:-1].replace('\\\\n', '\\n')
    #clean_pem = clean_public_pem_data.encode('utf-8')
    #print(clean_public_pem_data)
    #print(clean_public_pem_data)
  #return
  #print(args.public_pem_data.encode('utf-8'))
 
  #pem_test = clean_pem.splitlines()
  #PK_TEST.encode('utf-8')
  #clean_pem
  stats = collect_sys_stats(get_public_key(args.public_key_file))
  #print('data: %s' % stats)
  #output_file = write_data_to_file(stats, args.output_data_file)
  output_file = write_data_to_file(stats, args.output_data_file.strip())
  print(output_file)
  #return args.output_data_file
  # encrypt sys stats

if __name__ == '__main__':
  main()