mksite
======
About
-----
mksite is a small Python script made to simplify creating 
new websites on a Slicehost VPS.

Currently, it will create a vhost configuration file and 
the necessary directories for a site. These are all 
specified by template files and thus can be copied and 
modified to suit your specific needs and software.

Installation
------------
### Requirements
+ Python (tested with 2.6.4 and 2.7)
+ [Template-Python][1]

### Install
To install, simply run the included `install.sh` script. 
You may need to modify the user and group that it installs 
files as before using it.

### Configuration
At the very least, you need to check 
`/etc/mksite/mksite.conf` and make any changes from that 
to match your environment.

Optionally, create and modify [templates][2] as needed. 

Templates
---------
### Template Structure
Underneath the `templates` directory are 1 or more folders, 
one per template. Each template has at least two files, the 
configuration file and the actual template. Additional files 
may be present for other operations.

All files for the template and the folder they're in share 
a common name. In the case of the standard default template, 
it is `standard`. The folder is standard and inside of it are 
files such as standard.conf.

mksite will look for and use the following files:

+ _name_.conf: configuration file
+ _name_.tpl: template file
+ _name_.dirs: file specifying directories to create


### Template Configuration File
The [templating system][1] used for mksite is easy to work 
with. All variables that get substituted are inside `[% %]`. 

As an example, the following line is in standard.tpl:

> `ServerAlias www.[% domain %]`

If `domain` is specified as `example.com`, mksite will generate 

> `ServerAlias www.example.com`

Other than `domain`, no variables are assumed to exist. They 
are all specified in the template itself.

Let's look at the standard template.

    [template]
    name      = Standard website
    author    = Ross Nelson
    license   = Public domain
    ask       = email

The `[template]` section gives a name to the template, lists the 
template's author, and specifies a license.

The `ask` value is used to force mksite to ask for a value for 
a given variable, even if a default is given. We'll get to 
variables next, but for now we see that the email address is 
listed as one we ask for.

Variables have two parts:

1. Variable name
2. Description of the variable

    [variables]
    domain = Domain name
    root = Root directory
    publicdirectory = Public HTML directory
    cgidirectory = CGI-BIN directory
    errorlog = Error log file
    accesslog = Access log file
    directoryindex = Directory index
    email = Webmaster e-mail address

Those are variables from the standard template. On the left is 
the variable name that we will use throughout the rest of the 
template, and on the right is our description. If the user is 
asked to specify a value for one of the variables, it will be 
shown the description.

We know from the `ask` variable in `[template]` that we can force 
the user to give a value for something. We can also specify 
defaults (remember, even if a default is specified, the user 
will be asked for a value for something in `ask`).

Defaults can be used to specify a value for something to be 
put in the configuration file that is static or a value that 
is based on other values.

For example, the standard template has the following:

    [defaults]
    directoryindex  = index.php index.xhtml index.htm index.html
    root            = /srv/[% domain %]
    publicdirectory = [% root %]/public
    cgidirectory    = [% root %]/cgi-bin/
    errorlog        = [% root %]/logs/error.log
    accesslog       = [% root %]/logs/access.log
    email           = webmaster@[% domain %]

As you can see, `publicdirectory` is given here but not in `ask`. 
This will result in `publicdirectory` being filled in with the 
correct value (e.g., `/srv/example.com/public`) but it won't be 
presented to the user.

Also included is `email`. This was the one value that we want to 
ask the user for a value. Since it has a default given here, when 
the user goes to create a site using this template, it will default 
to that but make them confirm this choice or substitute their own 
value.

If you want to add a new variable that the user must give a value 
for, add it to `[variables]` but do not give it a default.

### Directory File

The directory file is used to tell mksite to create certain 
directories for you while it is creating the domain. This can be 
used to set up a directory structure that matches the vhost 
configuration.

As with the template file and the configuration file, this will be 
processed by the [template engine][1] before it is used, allowing 
you to do things like referencing `[% root %]` (a variable in the 
standard template) as shown here:

    [% root %]             [% mksiteuser %]  [% mksitegroup %]   755
    [% root %]/cgi-bin     [% mksiteuser %]  [% mksitegroup %]   755
    [% root %]/logs        [% mksiteuser %]  [% mksitegroup %]   777
    [% root %]/private     [% mksiteuser %]  [% mksitegroup %]   700
    [% root %]/public      [% mksiteuser %]  [% mksitegroup %]  2750

There are four fields to every entry:

1. The directory to create
2. The user to set as the directory owner
3. The group to set as the directory owning group
4. The mode to set for the directory

Obviously, when running mksite, you have to have permission to set 
the owner, owning group, and mode as well as make the directory itself.


### Built-in Variables
There are a number of variables that are filled in by mksite when it 
runs (overwriting any user-specified values for them):

+ `domain`: the domain the user is configuring
+ `timestamp`: a timestamp showing date and time mksite ran
+ `templatename`: the name of the template (from the configuration)
+ `templateauthor`: the author of the template (from the configuration)
+ `templatelicense`: the license for the template (from the configuration)
+ `mksiteuser`: the user specified in `mksite.conf`
+ `mksitegroup`: the group specified in `mksite.conf`
+ `mksiteuid`: the UID of `mksiteuser`
+ `mksitegid`: the GID of `mksitegroup`




[1]: http://template-toolkit.org/python/index.html
[2]: http://github.com/rnelson/slicehost-mksite/tree/master/templates