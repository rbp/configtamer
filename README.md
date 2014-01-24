thecpa - The ConfigParser Alternative
======================================

#### Or: The Crimson Permanent Assurance!

thecpa is a configuration file format, and accompanying Python parser.

thecpa is a powerful, flexible configuration file format. It's meant to be
straightforward to write and clear to read, allowing complex
configurations but making the simple ones simple.

### A simple example

A configuration file can be as simple as a list of key/values:

```
document_root: /var/www/htdocs
logs_dir: /var/log/foobar
access_log: {logs_dir}/access.log
error_log: {logs_dir}/error.log
```

And here is how it would be parsed:

```python
    >>> import thecpa
    >>> config = thecpa.parse("example.config")
    >>> config.document_root
    '/var/www.htdocs'
    >>> config.error_log
    '/var/log/foobar/error.log
```


### A more interesting example

You can also use sections in your configuration file, and tell one
section to fall back to another section's values:

```
production:
    code_dir: /var/src/some_project
    wsgi_dir: {code_dir}/app.wsgi

    servers:
        dbservers = db1, db2
        webservers: web1,
                    web2,
                    web42,

development [default: production]:
    code_dir: ~/code/some_project/

    servers:
        dbservers: devserver1
        webservers: {dbservers}
```

```python
    >>> config = thecpa.parse("example.config")
    >>> config.production.wsgi_dir
    '/var/src/some_project/app.wsgi'
    >>> config.development.wsgi_dir
    '~/code/some_project//app.wsgi'
    >>> config.production.dbservers
    'db1, db2'
```

It's good to be able to apply some structure to the config file. But
note that config.production.dbservers is returned as a string (as are
all other values). You can tell thecpa that this was supposed to be a
list, and it will behave correctly (even allowing trailling commas and
whitespace):

```python
    >>> config.production.dbservers.as_list()
    ['db1', 'db2']
    >>> config.production.webservers.as_list()
    ['web1', 'web2', 'web42']
```

### An example with specs

You can use `as_list` (and `as_int`, `as_bool` etc), but that can get
tiresome. It also doesn't give the person writing the configuration
a clue as to which type of value they whould use.

For that, thecpa lets you use an annotated example as specs:

```
production:
    debug: True [optional, default=True]
    code_dir: /path/to/code [path]
    wsgi_dir: {code_dir}/app.wsgi [path]
    instances = 2 [optional, int, default=1]

    servers:
        dbservers = db1, db2 [list]
        webservers: web1,
                    web2,
                    web42,   [list]
```

Given the specs above (which you can include in your software's
documentation), here's how parsing would work:

```python
    >>> parser = thecpa.parser("example.specs")
    >>> config = parser.parse("example.config")
    >>> config.production.wsgi_dir
    '/var/src/some_project/app.wsgi'
    >>> config.development.wsgi_dir
    '~/code/some_project/app.wsgi'
    >>> config.production.dbservers
    ['db1', 'db2']
    >>> config.production.webservers
    ['web1', 'web2', 'web42']
    >>> config.development.instances
    1
```

A few things are worth noting, here: accessing
`config.production.dbservers` directly already treats the value as a
list. Also, had you noticed in the previous examples that
`config.development.wsgi_dir` had a duplicated slash? thecpa now knows
that this is a path and fixes that. Finally,
`config.development.instances` uses the default integer value set in
the specs, even though it wasn't specified anywhere in the
configuration.


### More examples and documentation

Please look at the full documentation on... TODO :)

(It's coming, I promise! I haven't even settled on the name yet ;))


Features
=======

- Works on Python 2 (>= 2.7) and Python 3 (>= 3.3)
- Hierarchical key interpolation, using curly braces: {section.subsection.subsubsection.some_key}
- Configuration keys can be accessed as attributes or dict keys: `config.some_key == config['some_key']`
- Annotated example files can be used as specification (for value type, optional and default values etc).



FAQ
====

## "thecpa"? What kind of name is that??

I needed a name, I was looking for puns, Monty Python references and something I could get away with by cramming "CP" (for ConfigParser) in it...


## Why not... ?

### ConfigParser

ConfigParser is not hierarchical. "Intrinsic defaults" are defined in code (as a dict passed into the ConfigParser object), instead of separately, as a specification.

In ConfigParser you can't access options as attributes, and not even
(in Python 2) as dict keys.


### ConfigObj

Hasn't been updated in nearly 4 years.


### JSON, YAML, Clojure's EDN

These are not really configuration formats, they are data description formats. You can use them for config, of course, but they are more verbose than necessary, and distract from the config itself.


### XML

Seriously?
