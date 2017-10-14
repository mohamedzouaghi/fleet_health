
from lxml import etree
from collections import namedtuple

# how to get current dir in python
DEFAULT_XML_FILE = 'config.xml'

# Structure to organize the XML data
Alert = namedtuple('Alert', 'type limit')
Client = namedtuple('Client', 'ip port username password mail alerts')

DEFAULT_USERNAME = ''
DEFAULT_PASSWORD = ''
DEFAULT_RETRY = 3

def get_clients_details(xml_file=DEFAULT_XML_FILE, include_alerts=True):
  """Open the config xml file and retrieves client details.
    If there is no need for alert details it can be skipped by desactivating include_alerts.

  Args:
    xml_file: str, xml filepath and file name.
    include_alerts: bolean, include alert details if True.

  Returns:
    list of Client namedtuple instances.
  """
  clients = []
  uniq_ip_addresses = []
  tree = etree.parse(xml_file)
  root = tree.getroot()
  client_tags = root.findall('client')
  for c in client_tags:
    # If ip addr is duplicated we only consider the first record. following ones
    # are ignored
    if c.get('ip') in uniq_ip_addresses:
      continue
    else:
      uniq_ip_addresses.append(c.get('ip'))

    client = Client(ip=c.get('ip'), port=c.get('port'), username=c.get('username'),
                    password=c.get('password'), mail=c.get('mail'), alerts=[])
    if include_alerts:
      alert_tags = c.findall('alert')
      for a in alert_tags:
        client.alerts.append(Alert(type=a.get('type'), limit=a.get('limit')))
    clients.append(client)

  return clients 

