#!/usr/bin/env python
#
# mksite v0.0.3
# Copyright (C) 2010-2014 Ross Nelson
# http://github.com/rnelson/mksite

from datetime import datetime
from optparse import OptionParser
from template import Template
from template.util import TemplateException
import ConfigParser
import grp
import os
import pwd
import re
import subprocess


MKSITE = {
	'name' : 'mksite',
	'version' : '0.0.3',
	'author' : 'Ross Nelson',
	'url' : 'http://github.com/rnelson/mksite',
	'copyright' : 'Copyright (C) 2010-2014 Ross Nelson'
}

DEFAULTCONF = {
	'confdir' : '/etc/apache2/sites-available',
	'templates' : '/etc/mksite/templates',
	'defaulttemplate' : 'standard',
	'siteroot' : '/srv',
	'user' : pwd.getpwnam(os.environ['USER'])[0],
	'group' : grp.getgrgid(pwd.getpwnam(os.environ['USER'])[3])[0]
}


def parseConfig(configFile):
	"""Parses the configuration file
	
	Example configuration:
		[main]
		confdir=/etc/apache2/sites-available
		templates=/etc/mksite/templates
		siteroot=/srv
		user=apache
		group=nobody
	"""
	
	# Make sure the configuration file exists
	if not os.path.exists(configFile):
		print('warning: configuration file ' + configFile + ' does not exist')
	
	# Open the config file
	ini = ConfigParser.ConfigParser()
	ini.read(configFile)
	
	# Get the values
	confdir   = getConfigValue(ini, 'main', 'confdir',         DEFAULTCONF['confdir'])
	tpls      = getConfigValue(ini, 'main', 'templates',       DEFAULTCONF['templates'])
	deftpl    = getConfigValue(ini, 'main', 'defaulttemplate', DEFAULTCONF['defaulttemplate'])
	siteroot  = getConfigValue(ini, 'main', 'siteroot',        DEFAULTCONF['siteroot'])
	user      = getConfigValue(ini, 'main', 'user',            DEFAULTCONF['user'])
	group     = getConfigValue(ini, 'main', 'group',           DEFAULTCONF['group'])
	
	# Create and return a dictionary with all of the settings
	settings = { 'confdir' : confdir, 'templates' : tpls, 'defaulttemplate' : deftpl, 'siteroot' : siteroot, 'user' : user, 'group' : group }
	return settings


def getConfigValue(config, section, name, default=''):
	"""Gets a value from the configuration. If not found, returns the default"""
	
	try:
		val = config.get(section, name)
	except:
		val = default
	
	return val


def getTemplateValues(settings, domain, templateName):
	"""Creates and returns a list with values for the template, either defaults or user-specified values"""
	
	# Parse the template configuration file
	tplConfig = ConfigParser.ConfigParser()
	tplConfig.read(os.path.join(os.path.join(settings['templates'], templateName), templateName + '.conf'))
	
	
	# Get the template information
	tpl = {
		'name' : tplConfig.get('template', 'name'),
		'author' : tplConfig.get('template', 'author'),
		'license' : tplConfig.get('template', 'license')
	}
	
	
	# Get all of the variables that we need and set default values
	variableSection = tplConfig.items('variables')
	variables = {}
	variableDescriptions = {}
	
	# Fill in default values (or '' if none given)
	variables['domain'] = domain
	for variable in variableSection:
		name = variable[0]
		desc = variable[1]
		val  = ''
		
		try:
			variables[name] = tplConfig.get('defaults', name)
		except:
			variables[name] = ''
			
		variableDescriptions[name] = variable[1]
	
	
	# Find out what variables we're supposed to ask for
	ask = tplConfig.get('template', 'ask').strip().split()
	
	
	# Prompt the user for anything that the template wanted us to ask
	# for or that we don't have a value for
	values = {}
	for variable in variables:
		# Grab the description and default value
		default = variables[variable]
		
		# Find out if the item is in ask
		varInAsk = False  # next((n for n in ask if n == name), None)
		for v in ask:
			if v.strip() == variable.strip():
				varInAsk = True
		
		if varInAsk or len(default) < 1:
			# Set up our initial value
			value = ''
			if not varInAsk:
				value = default
			
			# Prompt the user
			while len(value) < 1:
				value = str(raw_input(variableDescriptions[variable] + ' [' + default + ']: '))
				
				if len(value) == 0 and len(default) > 0:
					value = default
			
			values[variable] = value
		else:
			values[variable] = default
	
	
	# Fill in software-defined variables
	values['timestamp'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')
	values['creator'] = MKSITE['name'] + ' ' + MKSITE['version']
	values['templatename'] = tpl['name']
	values['templateauthor'] = tpl['author']
	values['templatelicense'] = tpl['license']
	values['mksiteuser'] = config['user']
	values['mksitegroup'] = config['group']
	values['mksiteuid'] = pwd.getpwnam(values['mksiteuser'])[2]
	values['mksitegid'] = grp.getgrnam(values['mksitegroup'])[2]
	
	return values
	os._exit(1)


def writeVhost(settings, domain, templateName, values):
	"""Writes a site's vhost configuration file"""
	
	# Open the file
	conf = str(os.path.join(settings['confdir'], domain))
	outFile = open(conf, 'w')
	
	
	# Write the configuration
	t = Template()
	try:
		tplDir = os.path.join(settings['templates'], templateName)
		templateFilename = os.path.join(tplDir, templateName + '.tpl')
		inFile  = open(templateFilename, 'r')
		source = inFile.read()
		
		# While there are variables left unprocessed, process the string
		expression = r'\[\%.+\%\]'
		while re.search(expression, source) != None:
			source = t.processString(source, values)
		
		# Write what we have
		outFile.write(source)
	except TemplateException, e:
		print "ERROR: %s" % e
	
	
	# Cleanup
	outFile.close()


def makeDirectories(settings, domain, templateName, values):
	"""Creates the directories for the web site"""
	
	t = Template()
	try:
		tplDir = os.path.join(settings['templates'], templateName)
		dirsFile = os.path.join(tplDir, templateName + '.dirs')
		inFile  = open(dirsFile, 'r')
		source = inFile.read()
		
		# Substitute any variables
		expression = '\[\%.+\%\]'
		while re.search(expression, source) != None:
			source = t.processString(source, values)
		
		# Go through each substituted line
		lines = source.split('\n')
		for line in lines:
			if len(line) > 0 and not line.strip().startswith('#'):
				# Split the line up into its pieces
				l = line.split()
				
				directory = l[0]
				user = pwd.getpwnam(l[1])[0]
				group = grp.getgrnam(l[2])[0]
				mode = l[3]
				uid = pwd.getpwnam(l[1])[2]
				gid = grp.getgrnam(l[2])[2]
				
				# Create the directory
				if os.path.exists(directory):
					print('warning: ' + directory + ' exists')
				else:
					os.mkdir(directory, int(mode, 8))
				
				# chown and chmod it
				os.chown(directory, uid, gid)
				subprocess.call('chmod ' + mode + ' ' + directory, shell=True)
	except TemplateException, e:
		print "ERROR: %s" % e


if __name__ == '__main__':
	parser = OptionParser(usage="mksite [-c config] [-t templatename] [-d 'domain.ext']", version=MKSITE['name'] + ' ' + MKSITE['version'])
	parser.add_option('-d', '--domain',   action='store', type='string', dest='domain',   help='the domain to create')
	parser.add_option('-t', '--template', action='store', type='string', dest='template', help='name of the template to use')
	parser.add_option('-c', '--conf',     action='store', type='string', dest='config',   help='path to the configuration file', default='/etc/mksite/mksite.conf')
	(options, args) = parser.parse_args()
	
	# Parse the configuration
	config = parseConfig(options.config)
	
	# If they didn't specify a template or it doesn't exist, have them choose
	template = ''
	if options.template is not None:
		template = options.template
	else:
		templates = []
		templatesDir = config['templates']
		
		# Get the list of all templates
		for template in os.listdir(templatesDir):
			templateDir = os.path.join(templatesDir, template)
			
			if os.path.isdir(templateDir):
				if os.path.exists(os.path.join(templateDir, template + '.conf')):
					templates.append(template)
		
		default = 1
		for i in xrange(len(templates)):
			# Fitting in with the excellent naming for i, j will be the
			# index presented to the user (1 to templateCount, instead
			# of 0 to templateCount-1)
			j = i + 1
			
			# Did we find the default?
			if templates[i] == config['defaulttemplate']:
				default = j
			
			# Open the template configuration and get the name
			tplDir = os.path.join(config['templates'], templates[i])
			tplConfig = ConfigParser.ConfigParser()
			tplConfig.read(os.path.join(tplDir, templates[i] + '.conf'))
			templateName = tplConfig.get('template', 'name')
			
			print str(j) + '. ' + templateName
		
		print ''
		templateNumber = -1
		while templateNumber < 0 or templateNumber > len(templates):
			choice = raw_input('Choose a template [' + str(default) + ']: ')
			if len(choice) == 0:
				choice = str(default)
			templateNumber = int(choice)
		
		template = templates[templateNumber - 1]
	
	# Create the site
	values = getTemplateValues(config, options.domain, template)
	writeVhost(config, values['domain'], template, values)
	makeDirectories(config, values['domain'], template, values)
	print 'Done.'
