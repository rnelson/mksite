#!/usr/bin/env python
#
# mksite v0.0.1
# Ross Nelson, pretendamazing.org

from datetime import datetime
from optparse import OptionParser
import ConfigParser
import grp
import os
import pwd
import subprocess
import sys

DEFAULTCONF = { 'confdir' : '/etc/apache2/sites-available', 'siteroot' : '/srv', 'user' : pwd.getpwnam(os.environ['USER'])[0], 'group' : grp.getgrgid(pwd.getpwnam(os.environ['USER'])[3])[0], 'gperms' : '755', 'lperms' : '777', 'pperms' : '2750' }

def parseConfig(configFile):
	"""Parses the configuration file
	
	Example configuration:
		[main]
		confdir=/etc/apache2/sites-available
		siteroot=/srv
		user=apache
		group=nobody
		gperms=755
		lperms=777
		pperms=2750
	"""
	
	# Make sure the configuration file exists
	if not os.path.exists(configFile):
		print('warning: configuration file ' + configFile + ' does not exist')
	
	# Open the config file
	config = ConfigParser.ConfigParser()
	config.read(configFile)
	
	# Get the values
	confdir  = getConfigValue(config, 'main', 'confdir',  DEFAULTCONF['confdir'])
	siteroot = getConfigValue(config, 'main', 'siteroot', DEFAULTCONF['siteroot'])
	user     = getConfigValue(config, 'main', 'user',     DEFAULTCONF['user'])
	group    = getConfigValue(config, 'main', 'group',    DEFAULTCONF['group'])
	gperms   = getConfigValue(config, 'main', 'gperms',   DEFAULTCONF['gperms'])
	lperms   = getConfigValue(config, 'main', 'lperms',   DEFAULTCONF['lperms'])
	pperms   = getConfigValue(config, 'main', 'pperms',   DEFAULTCONF['pperms'])
	
	# Create and return a dictionary with all of the settings
	settings = { 'confdir' : confdir, 'siteroot' : siteroot, 'user' : user, 'group' : group, 'gperms' : gperms, 'lperms' : lperms, 'pperms' : pperms }
	return settings

def getConfigValue(config, section, name, default=''):
	"""Gets a value from the configuration. If not found, returns the default"""
	
	try:
		val = config.get(section, name)
	except:
		val = default
	
	return val

def writeVhost(settings, domain):
	"""Writes a site's vhost configuration file"""
	
	# Variables
	curtime = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
	conf = str(os.path.join(settings['confdir'], domain))
	site = str(os.path.join(settings['siteroot'], domain))
	pubdir = str(os.path.join(site, 'public'))
	logdir = str(os.path.join(site, 'logs'))
	newline = '\n'
	
	# Open the configuration file
	file = open(conf, 'w')
	
	# Write a little informational header
	file.write('# Domain:    ' + domain + newline)
	file.write('# Public:    ' + pubdir + newline)
	file.write('# Created:   ' + curtime + newline)
	file.write('' + newline)
	
	# Config!
	file.write('<VirtualHost *:80>' + newline)
	file.write('  # Admin email, server name, and any aliases' + newline)
	file.write('  ServerAdmin webmaster@' + domain + newline)
	file.write('  ServerName ' + domain + newline)
	file.write('  ServerAlias www.' + domain + newline)
	file.write('  ' + newline)
	file.write('  # Hide information about the server software' + newline)
	file.write('  ServerSignature Off' + newline)
	file.write('  ' + newline)
	file.write('  # Index file and document root settings, telling it where' + newline)
	file.write('  # the site is located and what files to use for the index' + newline)
	file.write('  DirectoryIndex index.php index.xhtml index.htm index.html' + newline)
	file.write('  DocumentRoot ' + pubdir + newline)
	file.write('  ' + newline)
	file.write('  # Logging' + newline)
	file.write('  LogLevel warn' + newline)
	file.write('  ErrorLog ' + str(os.path.join(logdir, 'error.log')) + newline)
	file.write('  CustomLog ' + str(os.path.join(logdir, 'access.log')) + ' combined' + newline)
	file.write('  ' + newline)
	file.write('  # Public directory settings' + newline)
	file.write('  <Directory ' + pubdir + '>' + newline)
	file.write('    Options -Indexes +Includes ExecCGI FollowSymLinks' + newline)
	file.write('    ' + newline)
	file.write('    AddHandler fcgid-script .php' + newline)
	file.write('    FCGIWrapper /usr/lib/cgi-bin/php5 .php' + newline)
	file.write('  </Directory>' + newline)
	file.write('  ' + newline)
	file.write('  # CGI settings' + newline)
	file.write('  ScriptAlias /cgi-bin/ ' + str(os.path.join(site, 'cgi-bin')) + '/' + newline)
	file.write('  <Location /cgi-bin>' + newline)
	file.write('    Options +ExecCGI' + newline)
	file.write('  </Location>' + newline)
	file.write('</VirtualHost>' + newline)
	
	# Cleanup
	file.close()

def makeDirectories(settings, domain):
	"""Creates the directories for the web site"""
	
	# Variables
	site = os.path.join(settings['siteroot'], domain)
	cgidir = os.path.join(site, 'cgi-bin')
	logdir = os.path.join(site, 'logs')
	prvdir = os.path.join(site, 'private')
	pubdir = os.path.join(site, 'public')
	
	# os.chown() requires the uid and gid rather than name, so grab those
	uid = pwd.getpwnam(settings['user'])[2]
	gid = grp.getgrnam(settings['group'])[2]
	
	if not os.path.exists(settings['siteroot']):
		print('error: the site root, ' + settings['siteroot'] + ' does not exist')
		os._exit(-1)
	
	makeDirectory(site, settings['gperms'], uid, gid)
	makeDirectory(cgidir, settings['gperms'], uid, gid)
	makeDirectory(logdir, settings['lperms'], uid, gid)
	makeDirectory(prvdir, '700', uid)
	makeDirectory(pubdir, settings['pperms'], uid, gid)

def makeDirectory(directory, mode='750', uid=-1, gid=-1):
	"""Makes a directory and sets its mode and owner"""
	
	# Does it already exist?
	if os.path.exists(directory):
		print('warning: ' + directory + ' exists')
	else:
		os.mkdir(directory, int(mode, 8))
	
	# chown the directory
	os.chown(directory, uid, gid)
	
	# Change the mode agaon; the mkdir() call isn't setting it properly for 2750, even though '2750'
	# and '02750' both give the same octal value of 1512
	subprocess.call('chmod ' + mode + ' ' + directory, shell=True)

if __name__ == '__main__':
	parser = OptionParser(usage="%prog -d 'domain.ext'", version="%prog 0.0.1")
	parser.add_option('-d', '--domain', action='store', type='string', dest='domain', help='the domain to create')
	parser.add_option('-c', '--conf',   action='store', type='string', dest='config', default='/etc/mksite.conf', help='path to the configuration file')
	parser.add_option('-v', '--vhost',  action='store', type='string', dest='vhost',  help='folder for vhost configs')
	parser.add_option('-u', '--user',   action='store', type='string', dest='user',   help='username to own the folders')
	parser.add_option('-g', '--group',  action='store', type='string', dest='group',  help='group to own the folders')
	parser.add_option('-r', '--root',   action='store', type='string', dest='root',   help='root folder to create the site structure under')
	(options, args) = parser.parse_args()
	
	# Make sure we got a domain
	if options.domain is None:
		parser.error('domain name is required')
	
	# Parse the configuration
	config = parseConfig(options.config)
	
	# Override any defaults/config file values with arguments passed in
	if not options.user is None:
		config['user'] = options.user
	if not options.group is None:
		config['group'] = options.group
	if not options.root is None:
		config['siteroot'] = options.root
	if not options.vhost is None:
		config['confdir'] = options.vhost
	
	# Create the site
	writeVhost(config, options.domain)
	makeDirectories(config, options.domain)
	print 'Done.'