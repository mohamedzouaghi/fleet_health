
import logging
import argparse


from lib import storage
from lib import config

import smtplib

from email.mime import multipart
from email.mime import text

# METRICS_MAP: {xml_key: db_key} 
METRICS_MAP = {'memory': 'mem_usage', 'cpu': 'cpu_usage', 'uptime': 'uptime'}

class Alerter(object):

  # don't forget to create a new account
  DEFAULT_SMTP_SERVER = 'smtp.gmail.com'
  DEFAULT_EMAIL_USERNAME = 'azzouaghi@gmail.com'  
  DEFAULT_EMAIL_PASSWORD = 'zouaghi_2010'

  def __init__(self, username, password, logger=None):
    if not logger:
      logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
      self.logger = logging.getLogger(__name__)
    else:
      self.logger = logger
    self.db = storage.Storage(username, password)

  def run_alerts(self, dryrun):
    alerted_machines = []
    self.clients = config.get_clients_details()

    for m in self.clients:
      stats = self.db.get_non_treated_stats(m.ip)

      if not stats:
        # Don't forget to include event logs!!
        self.logger.info('All stats for client[%s] has been already treated. Nothing to do.', m.ip)
        continue
      else:
        for s in stats:
          if self.treat_stat(m, s, dryrun=dryrun) and m.ip not in alerted_machines:
            alerted_machines.append(m.ip)
    return alerted_machines

  def treat_stat(self, machine, stat, dryrun):
    # machine info from XML
    alerted_machine = False
    alert_to_be_triggered = False
    metrics_to_be_alerted = []
    for alert in machine.alerts:
      metric_name = alert.type
      # This makes the % sign optional in the xml file
      xml_val = float(alert.limit[:-1]) if alert.limit.endswith('%') else float(alert.limit)
      db_val = float(getattr(stat, METRICS_MAP[alert.type]))

      if  xml_val <= db_val:
        metrics_to_be_alerted.append((metric_name, xml_val, db_val))
        self.logger.info('Alert to be triggered, machine: %s\txml: %s db: %s metric: %s' % (
            machine.ip, xml_val, db_val, metric_name))
        alert_to_be_triggered = True
    if alert_to_be_triggered:
      # Following ensure that the stat record won't be treated in the next iteration
      if self.send_alert(machine, metrics_to_be_alerted, dryrun=dryrun):
        self.db.mark_stat_as_treated(stat.id)
        self.logger.info('Alert [%s] marked as treated in the DB.' % stat.id)
        alerted_machine = True
    else:
      self.logger.info('No alert to be trigeered for: %s' % machine.ip)

    return alerted_machine

  def send_email(self, email_text, destination, subject, email_username=DEFAULT_EMAIL_USERNAME,
                 email_password=DEFAULT_EMAIL_PASSWORD):

    sent_from = email_username
    sent_to = destination

    msg = multipart.MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = sent_from
    msg['To'] = sent_to

    body = text.MIMEText(email_text, 'plain')
    msg.attach(body)
    
    server = smtplib.SMTP_SSL(self.DEFAULT_SMTP_SERVER, 465)
    server.ehlo()
    server.login(email_username, email_password)

    sent_result = server.sendmail(sent_from, sent_to, msg.as_string())
    print(sent_result)
    print(msg.as_string())
    server.close()
    # sent_result will be an empty dict if all messages were sent
    # otherwise it contains the address of the recipient who didn't receive the notification
    return not sent_result


  def send_alert(self, machine, metrics_to_be_alerted, dryrun=True):
    subject = 'Notification alert related to machine: %s' % machine.ip
    destination = machine.mail
    email_text = ['You are receiving this notification because one of your machine'
                  ' seems to have reached its configured threshold.']

    for m in metrics_to_be_alerted:
      email_text.append(
          '\nMetric type: %s\nThreshold: %s\nPulled value from machine: %s'% (m[0], m[1], m[2]))

    if dryrun:
      self.logger.warn('The following text wasn\'t sent because simulate_send_email'
                       ' was deactivated:\n%s' % ''.join(email_text))
      return False
    else:
      return self.send_email(''.join(email_text), destination, subject)


def main():

  parser = argparse.ArgumentParser()
  parser.add_argument('-u', '--username', required=False, default=config.DEFAULT_USERNAME,
                      help='username used for DB operations.')
  parser.add_argument('-p', '--password', required=False, default=config.DEFAULT_PASSWORD,
                      help='username used for DB operations.')
  parser.add_argument('-d', '--dryrun', required=False, dest='dryrun', action='store_true',
                      help='If set to false no alert will be sent. Mosly used for debug purpose.')
  parser.add_argument('--no-d', '--no-dryrun', required=False, dest='dryrun', action='store_false',
                      help='If set to false no alert will be sent. Mosly used for debug purpose.')
  args = parser.parse_args()

  alerter = Alerter(args.username, args.password)
  alerter.run_alerts(args.dryrun)


if __name__ == '__main__':
  main()