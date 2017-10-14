"""Storage layout used by server_collector to store stats of machines into the DB.
"""

import logging
import pymysql
from collections import namedtuple

MachineStats = namedtuple('MachineStats', 'id ip_addr cpu_usage mem_usage uptime event_logs collection_date')


class StorageError(Exception):
  """Base class exceptions for the Stats library module."""

  def __init__(self, msg):
    super(StorageError, self).__init__()
    self.msg = msg

class LogStatsError(StorageError):
  """Exception raised when sql error is detected with email insert query."""

  def __init__(self, query):
    self.query = query
    super(LogStatsError, self).__init__('Error detected with email query: %s' %
                                        self.query)


class Storage(object):
  DEFAULT_DB_HOSTNAME = 'localhost'
  DEFAULT_DB_NAME = 'crossover_db'
  insert_qry = '''INSERT INTO collected_stats(ip_addr, os, cpu_usage, mem_usage, uptime, event_logs)
                  VALUES(%s)'''
  not_treated_stats_qry = '''SELECT id, ip_addr, os, cpu_usage, mem_usage, uptime, event_logs
    FROM collected_stats WHERE consulted_for_alerts != '0'  ORDER BY collection_date DESC;'''
  get_machine_qry = '''SELECT id, ip_addr, cpu_usage, mem_usage, uptime, event_logs, collection_date
    FROM collected_stats WHERE consulted_for_alerts = 0 and ip_addr = '%s';'''
  mark_stat_as_treated_qry = '''UPDATE collected_stats SET consulted_for_alerts=1 WHERE id=%s;'''


  def __init__(self, username, password, hostname=DEFAULT_DB_HOSTNAME, database=DEFAULT_DB_NAME):
    """Contruct a Storage() instance and initiate a DB().

    Note: By defult a dev DB will be used unless database='prod' is passed to
    the contructor.

    Args:
      cs_instance: CloudSql Instance.
      database: str, valid self.DB_DICT key. Examples: 'dev', 'prod'.
      username: DB username.
      password: DB password.
      hostname: str, host address of the DB. Used instead of CloudSql instance
        for tests purpose for eg.
      port: int, port of the DB server. Used with host instead of CloudSql
        instance for tests purpose for eg.
    """
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
    logger = logging.getLogger(__name__)

    self.db = DB(database, username, password, hostname, logger)

  @classmethod
  def WrapStr(cls, strings, quotechar='`'):
    """Wrap list of strings with quotechar.

    Note: Method is expecting to get list but it can also handle single string
    and wrap it with quotechar.

    Args:
      strings: list of str. Example: ['str1', 'str2']
      quotechar: Single char which is used to wrap the list of strings.

    Returns:
      Single string having all list elements joined and wrapped with quotechar.
    """
    values = []
    for s in strings:
      if isinstance(s, list):
        values.append(('%c{0}%c' % (quotechar, quotechar)).format(
            ', '.join(s)))
      else:
        values.append(('%c{0}%c' % (quotechar, quotechar)).format(s))
    return ', '.join(values)

  def store_machine_stats(self, ip_addr, stats):
    os, cpu_usage, mem_usage, uptime, event_logs = stats
    query = self.insert_qry % (Storage.WrapStr([ip_addr, os, cpu_usage, mem_usage, uptime, event_logs], '\''))
    record_id = self.db.ExecuteQuery(query, 'lastrowid')
    if record_id is None:
      self.logger.error('Machine stat hasn\'t been recorded correctly, query: %s', query)
      raise LogStatsError(query)
    else:
      return record_id

  def get_non_treated_stats(self, ip_addr):
    results = self.db.ExecuteQuery(self.get_machine_qry % ip_addr, 'fetchall()')

    not_treated_stats =[]

    for result in results:
      id, ip_addr, cpu_usage, mem_usage, uptime, event_logs, collection_date = result
      not_treated_stats.append(MachineStats(
        id=id, ip_addr=ip_addr, cpu_usage=cpu_usage, mem_usage=mem_usage, uptime=uptime,
        event_logs=event_logs, collection_date=collection_date))
    return not_treated_stats

  def mark_stat_as_treated(self, stat_id):
    return self.db.ExecuteQuery(self.mark_stat_as_treated_qry % int(stat_id), 'lastrowid')

class DB(object):
  """Wrapper class that handles low level DB calls."""

  def __init__(self, database, username, password, hostname, logger=None):
    """Create a DB instance.

    Args:
      database: str, database name.
      username: str, username used to connect to DB.
      password: str, password used to connect to DB.
      hostname: str, host address of the DB. 
      port: int, port of the DB server.
    """
    db_params = {'host': hostname,
                 'db': database,
                 'user': username,
                 'passwd': password}

    if not logger:
      logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)-8s %(message)s')
      self.logger = logging.getLogger(__name__)
    else:
      self.logger = logger

    try:
      self.db = pymysql.connect(**db_params)
      self.cursor = self.db.cursor()
      self.logger.info('Initialization of DB: %s.%s', hostname, database)
    except pymysql.OperationalError as e:
      self.logger.fatal('[Can be safely ignored in dev/test environment ] Error while connecting to DB: %s', e)

  def Close(self):
    if self.db:
      self.db.close()

  def ExecuteQuery(self, query, return_type='lastrowid'):
    """Execute SQL query and return the results according to return_type.

    Args:
      query: string, query to be executed.
      return_type: string, the attribute or method of the cursor that needs to
        be returned. if it's a method it should include the parentheses, e.g:
        lastrowid, rowcount, fetchall()

    Returns:
      Return the values of the attribute or the method of Cursor spcified by
        return_type.
    """
    if self.cursor is None:
      self.cursor = self.db.cursor()
    try:
      self.logger.info('query to be executed: %s', query)
      self.cursor.execute(query)
      self.db.commit()
      return self._GetResults(return_type)
    except pymysql.MySQLError:
      self.logger.error('issue found with query: %s', query)

  def _GetResults(self, return_type):
    """Wrapper to return either an attribute or a method of the cursor.

    Args:
      return_type: string, valid attribute or method of pymysql.connect.cursor.
      Valid examples: lastrowid, rowcount, fetchall()

    Returns:
      Values of either the attribute or the method results of return_type.
    """
    if return_type[-2:] == '()':
      return getattr(self.cursor, return_type[:-2])()
    else:
      return getattr(self.cursor, return_type)
