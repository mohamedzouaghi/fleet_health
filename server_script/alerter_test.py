import unittest

from unittest import mock

import alerter

from lib import config
from lib import storage


# TODO(mohamedzouaghi): Add more tests to cover 
class AlerterTest(unittest.TestCase):
  def setUp(self):
    self.alerter = alerter.Alerter(None, None)

  @mock.patch('lib.storage.Storage.get_non_treated_stats')
  @mock.patch('lib.config.get_clients_details') 
  def test_empty_run_alerts(self, mock_get_cl_details, mock_get_non_treated):
    mock_get_cl_details.return_value = []
    alerted_machines = self.alerter.run_alerts(dryrun=True)
    self.assertEqual([], alerted_machines)

  @mock.patch('lib.storage.Storage.get_non_treated_stats')
  @mock.patch('lib.config.get_clients_details')
  def test_dryrun_valid_run_alerts(self, mock_get_cl_details, mock_get_non_treated):
    mock_al1 = config.Alert(type='cpu', limit='10')
    mock_cl1 = config.Client(ip='1.2.3.4', port='111', username='yo', password='man', mail='m@m.m', alerts=[mock_al1])
    nock_db_c1 = storage.MachineStats(
      id=100, ip_addr='1.2.3.4', cpu_usage='90', mem_usage='95', uptime=999, event_logs='', collection_date='')


    mock_get_cl_details.return_value = [mock_cl1]
    mock_get_non_treated.return_value = [nock_db_c1]

    dryrun_alerted_machines = self.alerter.run_alerts(dryrun=True)
    # Empty list because dryrun activated
    self.assertEqual([], dryrun_alerted_machines)


  @mock.patch('lib.storage.Storage.get_non_treated_stats')
  @mock.patch('lib.config.get_clients_details')
  @mock.patch('alerter.Alerter.treat_stat') 
  def test_valid_run_alerts(self, mock_treat_stat, mock_get_cl_details, mock_get_non_treated):
    mock_al1 = config.Alert(type='cpu', limit='10')
    mock_cl1 = config.Client(ip='1.2.3.4', port='111', username='yo', password='man', mail='m@m.m', alerts=[mock_al1])
    nock_db_c1 = storage.MachineStats(
      id=100, ip_addr='1.2.3.4', cpu_usage='90', mem_usage='95', uptime=999, event_logs='', collection_date='')


    mock_get_cl_details.return_value = [mock_cl1]
    mock_get_non_treated.return_value = [nock_db_c1]
    mock_treat_stat.return_value = [mock_cl1.ip]

    alerted_machines = self.alerter.run_alerts(dryrun=False)
    self.assertEqual([mock_cl1.ip], alerted_machines)

if __name__ == '__main__':
  unittest.main()
