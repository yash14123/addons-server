import datetime
import os

from django.conf import settings

from nose.tools import eq_

from olympia.amo.tests import TestCase
from olympia.addons.models import Addon
from olympia.devhub.cron import update_blog_posts
from olympia.devhub.tasks import convert_purified
from olympia.devhub.models import BlogPost


class TestRSS(TestCase):

    def test_rss_cron(self):
        url = os.path.join(
            settings.ROOT, 'src', 'olympia', 'devhub', 'tests',
            'rss_feeds', 'blog.xml')

        settings.DEVELOPER_BLOG_URL = url

        update_blog_posts()

        eq_(BlogPost.objects.count(), 5)

        bp = BlogPost.objects.all()[0]
        url = ("http://blog.mozilla.com/addons/2011/06/10/"
               "update-in-time-for-thunderbird-5/")
        eq_(bp.title, 'Test!')
        eq_(bp.date_posted, datetime.date(2011, 6, 10))
        eq_(bp.permalink, url)


class TestPurify(TestCase):
    fixtures = ['base/addon_3615']

    def setUp(self):
        super(TestPurify, self).setUp()
        self.addon = Addon.objects.get(pk=3615)

    def test_no_html(self):
        self.addon.the_reason = 'foo'
        self.addon.save()
        last = Addon.objects.get(pk=3615).modified
        convert_purified([self.addon.pk])
        addon = Addon.objects.get(pk=3615)
        eq_(addon.modified, last)

    def test_has_html(self):
        self.addon.the_reason = 'foo <script>foo</script>'
        self.addon.save()
        convert_purified([self.addon.pk])
        addon = Addon.objects.get(pk=3615)
        assert addon.the_reason.localized_string_clean
