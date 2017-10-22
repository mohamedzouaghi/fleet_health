# Fleet Health
> Author: Mohamed ZOUAGHI - mohamedzouaghi@gmail.com  
Simple python scripts that collect remote machines system stats (Example: CPU usage, memory usage etc...) and generate alerts when threshold are violated.
The entire project is fully written in Python.

## 1. Architecture
There are 3 main scripts that are primarily hosted in the server instance and which fullfil the following roles:  
- The “Collector”: This is the main script which runs from a cronjob configured in the server
instance. This scripts reads configuration of the different machines (aka client instance)
from config.xml and starts an ssh connection with each client. The collector is responsible
for sending to the clients the specific public key (which is used to encrypt data) and the
local_collector.py script which collects data. The server collector is also responsible of
retrieving encrypted data (which are written in a  file in the client instance), decrypting
them (using its private key) and storing the data in the database.
- The “alerter”: This is an independent module which is also ran from cronjob in the server
side. Its sole mission is to pull client system stats from the database (data which were
previously gathered by the server collector), compare data with the different alert thresholds
(configured in the config.xml) and send notification if needed. The alerter won’t only send
latest alerts, it also look for older records in the DB and trigger alerts if those records
that weren’t treated before (case of previous malfunction of the alerter for instance)  
**Note:** The breakdown between those two server modules makes the application faster, more
robust and more fault tolerant since a  breakage at the collector level won’t impact the
notifications, and vice versa. Thanks to this independency they can even be ran from two
different servers (each one doing its own job)  
**Note:** The two server modules (collector and alerter) were designed to run from cronjobs rather
than implementing an internal sleep mode. This has the benefits of saving resources since the
cronjob would only require resources when the time comes to run whereas the sleep-like
approach would require the script to be constantly running and therefore more exposed to
potential breakage.

- The “local_alerter”: This is the script which runs in the client side. It’s physically hosted in
the server and is transferred when there is a  need to pull client data. Local_alerter is also
responsible for encrypting data. This is done with the public key provided by the server
(through a  file transfer). Once the data are pulled and encrypted they will be written
locally into the client instance and it will be waiting for the server collector to retrieve
them.
  - lib/storage: This module provides an abstraction layer to the server scripts to access to
the database either to collect or to store records. Server scripts don’t need to know DB details. They simply use the API-like functions made available to them through
lib/storage.  
**Note:** Thanks to this decoupling, any database or any other storage solution can be supported
without having to touch any code from the server scripts.
  - lib/config: Same as for the storage but for the xml config file. Server scripts don’t have to
know anything about config.xml they delegate the interaction to lib/config
 - Config.xml: The key file which contains config data related to clients (including their
connection credentials and their alerts threshold)
 - The directory encrypted_stats: Temporary directory where clients data wait to be
decrypted and processed
 - The directory public_keys: Temporary directory which hosts the public_keys before
being sent to clients.



## 2. Instructions to install and configure prerequisites or dependencies

The project has been developed using python3 (3.5.3 to be more precise) and MySQL 5.9. Here after the list of libraries that need to be installed.  
**Note:** Some of the following packages are probably already installed, if that's the case no need to reinstall them.

### Server machine - pckages and dependencies:
All used packages can be installed using pip (for instruction on how to install pi see: https://pip.pypa.io/en/stable/installing/#do-i-need-to-install-pip)

* paramiko: (http://www.paramiko.org/installing.html)  
Used to establish sh connection. Installation can be made by:  
sudo pip install paramiko  
**Note:** there is no need to install this in the client side

* cryptography:  (https://cryptography.io/en/latest/)  
Used both by server and client to encrypt/decrypt messages. Installation can be made by:
sudo pip install cryptography

* PyMySQL: (https://github.com/PyMySQL/PyMySQL)  
Used to interact with MySQL. Installation can be made by:  
sudo pip install PyMySQL

* lxml: (http://lxml.de/)  
sed to manipulate xml files. Installation can be made by:  
sudo pip install lxml



### Client machines - Packages and dependencies:
* In most OS the sshd is not installed/activated by default, thus depending to the OS flavour
SSH server should be installed. For Linux it can be done by installing openssh-server. For Ubuntu:
sudo apt-get install openssh-server
For other distros checkout the openssh-server manuals.

* psutil: (https://pythonhosted.org/psutil/)
Used to pull system stats from cross platforms. Installation can be made by:
sudo pip install psutil

* cryptography:  (https://cryptography.io/en/latest/)
Used both by server and client to encrypt/# fleet_health to decrypt messages. Installation can be made by:  
sudo pip install cryptography  

## 3. Instructions to create and initialize the database  

- DB Instructions:  
MySQL is the database which was chosen to run this project. The way to install MySQL differs according to the os. The guidelines can be found at https://dev.mysql.com/doc/refman/5.7/en/installing.html

The sql scripts that needs to be run can be found under Source/sql_script...

- SMTP instructions:  
Currently the code uses a testing SMTP account credentials with gmail SMTP service. It's highlly recomended to change the account. This can be easily done from the code in alerter.py.

## 4. Assumptions

Here are the list of assumptions that were made:  

* The server intance which is used for central management role is a Linux box  
* The server modules are run as cronjobs, so they need to configured through crontab and its
the user reponsabilty to decide when to run them  
* The config.xml file can have as many client and alert records as user wants but its structure shouldn't change.  
* It is the project owner's responsability to make sure that usernames configured in the xml file are valid users with enough permissions to accept ssh connection, run script and create files.
* It is the project owner's responsabiliy to make sure smtp server/credential are valid

