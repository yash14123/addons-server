import os
import logging
from datetime import datetime

log = logging.getLogger('z.startup')

# Remember when mod_wsgi loaded this file so we can track it in nagios.
wsgi_loaded = datetime.now()

# Tell celery that we're using Django.
os.environ['CELERY_LOADER'] = 'django'

import django.conf
import django.core.handlers.wsgi
import django.core.management
import django.utils

# Do validate and activate translations like using `./manage.py runserver`.
# http://blog.dscpl.com.au/2010/03/improved-wsgi-script-for-use-with.html
django.utils.translation.activate(django.conf.settings.LANGUAGE_CODE)
utility = django.core.management.ManagementUtility()
command = utility.fetch_command('runserver')
command.validate()

# This is what mod_wsgi runs.
django_app = django.core.handlers.wsgi.WSGIHandler()


# Normally we could let WSGIHandler run directly, but while we're dark
# launching, we want to force the script name to be empty so we don't create
# any /z links through reverse.  This fixes bug 554576.
def application(env, start_response):
    if 'HTTP_X_ZEUS_DL_PT' in env:
        env['SCRIPT_URL'] = env['SCRIPT_NAME'] = ''
    env['wsgi.loaded'] = wsgi_loaded
    env['hostname'] = django.conf.settings.HOSTNAME
    env['datetime'] = str(datetime.now())
    return django_app(env, start_response)


# Initialize Newrelic if we configured it
newrelic_ini = getattr(django.conf.settings, 'NEWRELIC_INI', None)

if newrelic_ini:
    import newrelic.agent
    try:
        newrelic.agent.initialize(newrelic_ini)
    except Exception:
        log.exception('Failed to load new relic config.')
