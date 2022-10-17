# -*- coding: utf-8 -*-
###############################################################################
#    License, author and contributors information in:                         #
#    __openerp__.py file at the root folder of this module.                   #
###############################################################################

from odoo import models, fields, api
from odoo.tools.translate import _

from logging import getLogger
import feedparser
from datetime import datetime, timedelta
from time import mktime
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from urllib3.exceptions import InsecureRequestWarning
import ast

_logger = getLogger(__name__)


class AcademyPublicTenderingRSSFeed(models.Model):
    """ Access data for the different RSS (Really Simple Syndication) feeds

    """

    _name = 'academy.public.tendering.rss.feed'
    _description = u'Academy public tendering RSS feed'

    _inherit = ['image.mixin', 'mail.thread', 'mail.activity.mixin']

    _rec_name = 'name'
    _order = 'name ASC'

    name = fields.Char(
        string='Short name',
        required=True,
        readonly=False,
        index=True,
        default=None,
        help='Name will be used to identify the RSS feed',
        size=50,
        translate=True
    )

    source = fields.Char(
        string='Source',
        required=True,
        readonly=False,
        index=False,
        default=None,
        help='URL of the RSS feed',
        size=255,
        translate=False
    )

    title = fields.Char(
        string='Title',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='RSS feed title',
        size=255,
        translate=True
    )

    link = fields.Char(
        string='Link',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='URL of the main site',
        size=255,
        translate=False
    )

    description = fields.Text(
        string='Description',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Some additional information to distinguish the news feed',
        translate=True
    )

    lang = fields.Char(
        string='Language',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help=False,
        size=5,
        translate=False
    )

    publisher = fields.Char(
        string='Publisher',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help='Publisher email address',
        size=127,
        translate=False
    )

    published = fields.Datetime(
        string='Published',
        required=False,
        readonly=True,
        index=False,
        default=fields.datetime.now(),
        help='Date and time it was published'
    )

    consulted = fields.Datetime(
        string='Consulted',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Date and time it was last consulted'
    )

    active = fields.Boolean(
        string='Active',
        required=False,
        readonly=False,
        index=False,
        default=True,
        help='Check it to show this attempt or uncheck to archivate'
    )

    official = fields.Boolean(
        string='Is official',
        required=False,
        readonly=False,
        index=True,
        default=False,
        help='Checked if the feed corresponds to an official journal'
    )

    item_ids = fields.One2many(
        string='Items',
        required=False,
        readonly=True,
        index=True,
        default=None,
        help='Items in RSS feed',
        comodel_name='academy.public.tendering.rss.item',
        inverse_name='feed_id',
        domain=[],
        context={},
        auto_join=False,
        limit=None
    )

    item_count = fields.Integer(
        string='Item count',
        required=False,
        readonly=True,
        index=False,
        default=0,
        help='Number of items in RSS feed',
        compute='_compute_item_count'
    )

    reader = fields.Char(
        string='Reader',
        required=False,
        readonly=True,
        index=False,
        default=None,
        help=False,
        size=50,
        translate=False
    )

    options = fields.Text(
        string='Options',
        required=False,
        readonly=False,
        index=False,
        default=None,
        help='JSON string with some extra information',
        translate=True
    )

    @api.depends('item_ids')
    def _compute_item_count(self):
        for record in self:
            record.item_count = len(record.item_ids)

    _sql_constraints = [
        (
            'unique_source',
            'UNIQUE(source)',
            _(u'The source already exists')
        )
    ]

    @staticmethod
    def _get_date(feed, key):
        key = '{}_parsed'.format(key)
        result = None

        if key in feed.keys():
            tstruct = feed[key]
            result = datetime.fromtimestamp(mktime(tstruct))

        return result

    @staticmethod
    def _get_attr(feed, key):
        return feed[key] if key in feed.keys() else None

    @staticmethod
    def _safe_date(str_val, date_format, default=None):
        try:
            dt = datetime.strptime(str_val, date_format)
            return dt.date()
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_datetime(str_val, date_format, default=None):
        try:
            return datetime.strptime(str_val, date_format)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _safe_dictionary(str_dict, default={}):
        try:
            return ast.literal_eval(str_dict)
        except (ValueError, TypeError):
            return default

    @staticmethod
    def _dt_today():
        now = datetime.now()
        return now.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _safe_cast(val, to_type, default=None):
        """ Performs a safe cast between `val` type to `to_type`
        """

        try:
            return to_type(val)
        except (ValueError, TypeError):
            return default

    def get_options(self):
        self.ensure_one()

        return self._safe_dictionary(self.options)

    def get_option(self, name, default=None):
        self.ensure_one()

        options = self.get_options()

        return options.get(name, default)

    @staticmethod
    def _get_base_url(url):
        parts = urlparse(url)
        return '{}://{}'.format(parts.scheme, parts.netloc)

    @staticmethod
    def _make_absolute_links(url, soup):
        if not soup:
            return

        for a in soup.findAll('a'):
            if a.get('href'):
                a['href'] = urljoin(url, a['href'])
                a['target'] = '_blank'

        for link in soup.findAll('link'):
            if link.get('href'):
                link['href'] = urljoin(url, link['href'])

        for img in soup.findAll('img'):
            if img.get('src'):
                img['src'] = urljoin(url, img['src'])

    @staticmethod
    def _http_get(url, headers={}, params={}):
        http_headers = {'User-Agent': 'Chrome/51.0.2704.103 Safari/537.36'}
        http_headers.update(headers)

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        response = None
        try:
            response = requests.get(
                url, headers=http_headers, params=params, verify=False)
        except Exception as ex:
            msg = _('Request GET {} has failed. System says: {}')
            _logger.error(msg.format(url, ex))

        if response:
            if response.status_code == 200:
                msg = _('Request GET {}. Response code: {}')
                _logger.debug(msg.format(url, response.status_code))
            else:
                msg = _('Request GET {}. Response code: {}')
                _logger.warning(msg.format(url, response.status_code))
        else:
            msg = _('Request GET {} has failed')
            _logger.error(msg.format(url))

        return response

    def _get_last_update_limit(self):
        """ Get oldest datetime from which RSS entries will be append to the
        database.

        The oldest datetime will be the result of subtract a number of days
        from the current day. The number of days can be configured via the
        ``academy_public_tendering_rss.feed_days_ago`` parameter.

        Returns:
            datetime: datetime from which RSS entries will be read
        """

        param_name = 'academy_public_tendering_rss.feed_days_ago'
        param_obj = self.env['ir.config_parameter']
        days_ago = param_obj.get_param(param_name)
        if days_ago:
            days_ago = self._safe_cast(days_ago, int, 10)
        else:
            days_ago = 10
            
        oldest = self._dt_today()
        oldest = oldest - timedelta(days=abs(days_ago))

        return oldest

    def _get_last_update(self):
        """ Get the last create_date value from database and compares it with
        oldest limit from which RSS entries will be append to the database.

        Returns:
            datetime: maximum between last create_date and the olders limit
        """
        oldest = self._get_last_update_limit()

        domain = [('feed_id', '=', self.id)]
        gob_obj = self.env['academy.public.tendering.rss.item']
        last = gob_obj.search(domain, limit=1, order='create_date DESC')

        if last and last.create_date:
            oldest = max(last.create_date, oldest)

        msg = _('RSS feed will be updated from {}')
        _logger.info(msg.format(oldest.strftime('%d/%m/%Y')))

        return oldest

    def _update_feed_information(self, feed):
        self.ensure_one()

        self.title = self._get_attr(feed, 'title')
        self.link = self._get_attr(feed, 'link')
        self.description = self._get_attr(feed, 'subtitle')
        self.lang = self._get_attr(feed, 'language')
        self.publisher = self._get_attr(feed, 'publisher')
        self.published = self._get_date(feed, 'published')

        self.consulted = fields.datetime.now()

        msg = _('RSS feed {} updated. Published: {}, consulted: {}')
        _logger.info(msg.format(self.name, self.published, self.consulted))

    @api.model
    def _read_item_values(self, entry):
        guid = self._get_attr(entry, 'id')
        published = self._get_date(entry, 'published')
        now = fields.datetime.now()

        return {
            'guid': guid,
            'name': self._get_attr(entry, 'title'),
            'link': self._get_attr(entry, 'link'),
            'description': self._get_attr(entry, 'summary'),
            'published': published,
            'guid_hash': hash(guid),
            'safe_date': published or now
        }

    def _get_specific_reader(self):
        """ This model provides some specific RSS feed static methods to get
        the content linked to the RSS entries.

        Returns:
            function: return the static method (<class 'function'>) or None
        """
        self.ensure_one()

        reader = None
        if self.reader and hasattr(self, self.reader):
            reader = getattr(self, self.reader)
            msg = _('{} will be used as specific reader')
            _logger.info(msg.format(self.reader))

        return reader

    @staticmethod
    def _try_to_update_body(reader, values):
        """ Call RSS feed specific method to read some content in the page
        linked to the RSS entry.


        Args:
            reader (function): RSS feed specific static method to get content
            related with the RSS entries
            values (dict): dictionary of values with a link key, to which the
            content will be added
        """

        if reader and 'link' in values.keys():
            content = None

            try:
                content = reader(values['link'])

                if not content:
                    msg = _('0 bytes of content have been read from {}')
                    _logger.warning(msg.format(values['link']))
                else:
                    values['body'] = content

                    msg = _('{} bytes of content have been read from {}')
                    _logger.info(msg.format(len(content), values['link']))

            except Exception as ex:
                msg = _('Unable to read RSS feed link {}. System sais: {}')
                _logger.warning(msg.format(values['link'], ex))

    def _get_only_new_items(self, values_list, last_date=None):
        result = []

        if values_list:

            item_obj = self.env['academy.public.tendering.rss.item']
            last_date = last_date or self._get_last_update()

            available = [values['guid_hash'] for values in values_list]

            domain = [
                '&',
                ('guid_hash', 'in', available),
                '|', ('active', '=', True), ('active', '!=', True)
            ]
            existing = item_obj.search_read(domain, ['guid_hash'])
            existing = [item['guid_hash'] for item in existing]

            for values in values_list:
                if values['guid_hash'] not in existing and \
                   values['safe_date'] >= last_date:

                    result.append(values)

            msg = _('There are {} items in feed, {} will be added to database')
            _logger.info(msg.format(len(available), len(result)))

        return result

    def _consult(self):
        self.ensure_one()

        response = self._http_get(self.source)
        if not response or not response.status_code == 200:
            return

        parsed = feedparser.parse(response.text)

        self._update_feed_information(parsed.feed)

        m2m_ops = []
        reader = self._get_specific_reader()

        values_list = []
        for entry in parsed.entries:
            values = self._read_item_values(entry)
            values_list.append(values)

        values_list = self._get_only_new_items(values_list)
        if not values_list:
            return

        if reader:
            for values in values_list:
                self._try_to_update_body(reader, values)

        for values in values_list:
            m2m_ops.append([0, 0, values])

        self.item_ids = m2m_ops

    def consult(self):

        for record in self:
            record._consult()

    @api.model
    def consult_all(self):
        feed_set = self.search([])

        if feed_set:
            msg = _('All public tendering RSS feeds ({}) will be consulted')
            _logger.info(msg.format(len(feed_set)))

            dt = datetime.now().strftime('%c')
            expected = len(feed_set)
            done = 0

            for feed in feed_set:  # One by one in case one of them fails

                try:
                    feed.consult()
                    done = done + 1
                except Exception as ex:
                    msg = "Feed {} could not be read at {}. System says: {}"
                    _logger.error(msg.format(feed.name, dt, ex))

            if done == expected:
                msg = _('All RSS ({} / {}) feeds have been processed')
                _logger.info(msg.format(done, expected))
            else:
                msg = _('Some RRS feeds could not be read, '
                        'Only {} of {} have been processed')
                _logger.warning(msg.format(done, expected))

        else:
            msg = _('There is no any public tendering RSS feeds to consult')
            _logger.info(msg)

    # ---------------------------- SPECIFIC READERS ---------------------------

    def _boe_reader(self, link):
        response = self._http_get(link)
        root_url = self._get_base_url(link)
        result = None

        if response.status_code == 200:
            page = BeautifulSoup(response.text, 'lxml')

            attrs = {'id': 'textoxslt'}
            item = page.find('div', attrs=attrs)

            if item:
                self._make_absolute_links(root_url, item)
                result = item.decode_contents()

        return result

    def _doga_reader(self, link):
        response = self._http_get(link)
        root_url = self._get_base_url(link)
        result = None

        response.encoding = 'utf-8'

        if response.status_code == 200:

            page = BeautifulSoup(response.text, 'lxml')
            attrs = {'id': 'audioid'}
            parent = page.find('div', attrs=attrs)

            if parent:
                item = parent.find('div')

                self._make_absolute_links(root_url, item)

                if item:
                    result = item.decode_contents()

        return result

    def _inap_reader(self, link):
        root_url = self._get_base_url(link)
        result = None

        for i in range(0, 3):
            response = self._http_get(link)

            if response.status_code == 200:

                page = BeautifulSoup(response.text, 'lxml')

                attrs = {'class': 'asset-content'}
                parent = page.find('div', attrs=attrs)

                if parent:
                    attrs = {'class': 'container'}
                    item = parent.find('div', attrs=attrs)

                    if item:
                        self._make_absolute_links(root_url, item)
                        result = item.decode_contents()
                        break

        return result

    def _madrid_city_reader(self, link):
        root_url = self._get_base_url(link)
        result = None

        for i in range(0, 3):
            response = self._http_get(link)

            if response.status_code == 200:

                page = BeautifulSoup(response.text, 'lxml')

                attrs = {'class': 'mainContent'}
                item = page.find('main', attrs=attrs)

                if item:
                    self._make_absolute_links(root_url, item)
                    result = item.decode_contents()

        return result
