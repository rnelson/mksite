# Domain:     [% domain %]
# Public:     [% publicdirectory %]
# Created:    [% timestamp %] (by [% creator %])

<VirtualHost *:80>
	# Admin email, server name, and any aliases
	ServerAdmin [% email %]
	ServerName [% domain %]
	ServerAlias www.[% domain %]
	
	# Hide information about the server software
	ServerSignature Off
	
	# Index file and document root settings, telling it where
	# the site is located and what files to use for the index
	DirectoryIndex [% directoryindex %]
	DocumentRoot [% publicdirectory %]
	
	# Logging
	LogLevel warn
	ErrorLog [% errorlog %]
	CustomLog [% accesslog %]
	
	# Public directory settings
	<Directory [% publicdirectory %]>
		Options -Indexes +Includes ExecCGI FollowSymLinks
		
		AddHandler fcgid-script .php
		FCGIWrapper /usr/lib/cgi-bin/php5 .php
	</Directory>
	
	# CGI settings
	ScriptAlias /cgi-bin/ [% cgidirectory %]
	<Location /cgi-bin>
		Options +ExecCGI
	</Location>
</VirtualHost>
