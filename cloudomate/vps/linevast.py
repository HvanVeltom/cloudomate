import itertools
import json
import sys
import urllib

from bs4 import BeautifulSoup

from cloudomate.gateway.bitpay import extract_info
from cloudomate.vps.clientarea import ClientArea
from cloudomate.vps.hoster import Hoster
from cloudomate.vps.vpsoption import VpsOption


class LineVast(Hoster):
    name = "linevast"
    website = "https://linevast.de/"
    required_settings = [
        'firstname',
        'lastname',
        'email',
        'address',
        'city',
        'state',
        'zipcode',
        'phonenumber',
        'password',
    ]
    clientarea_url = 'https://panel.linevast.de/clientarea.php'

    def __init__(self):
        super(LineVast, self).__init__()

    def register(self, user_settings, vps_option):
        """
        Register RockHoster provider, pay through CoinBase
        :param user_settings: 
        :param vps_option: 
        :return: 
        """
        self.br.open(vps_option.purchase_url)
        self.br.select_form(nr=2)
        self.fill_in_server_form()
        self.br.submit()
        self.br.open('https://panel.linevast.de/cart.php?a=view')
        self.br.follow_link(text_regex=r"Checkout")
        self.br.select_form(name='orderfrm')
        self.fill_in_user_form(user_settings)
        page = self.br.submit()
        if 'checkout' in page.geturl():
            contents = BeautifulSoup(page.read(), 'lxml')
            errors = contents.find('div', {'class': 'checkout-error-feedback'}).text
            print(errors)
            sys.exit(1)
        self.br.select_form(nr=0)
        page = self.br.submit()
        amount, address = extract_info(page.geturl())
        return amount, address

    def fill_in_server_form(self):
        """
        Fills in the form containing server configuration.
        :return: 
        """
        self.br.form['configoption[61]'] = ['657']  # Paris
        self.br.form.new_control('text', 'ajax', {'name': 'ajax', 'value': 1})
        self.br.form.new_control('text', 'a', {'name': 'a', 'value': 'confproduct'})
        self.br.form.method = "POST"

    def fill_in_user_form(self, user_settings):
        """
        Fills in the form with user information.
        :param user_settings: settings
        :return: 
        """
        self.br.form['firstname'] = user_settings.get("firstname")
        self.br.form['lastname'] = user_settings.get("lastname")
        self.br.form['email'] = user_settings.get("email")
        self.br.form['phonenumber'] = user_settings.get("phonenumber")
        self.br.form['companyname'] = user_settings.get("companyname")
        self.br.form['address1'] = user_settings.get("address")
        self.br.form['city'] = user_settings.get("city")
        countrycode = user_settings.get("countrycode")

        # State input changes based on country: USA (default) -> Select, Other -> Text
        self.br.form['state'] = user_settings.get("state")
        self.br.form['postcode'] = user_settings.get("zipcode")
        self.br.form['country'] = [countrycode]
        self.br.form['password'] = user_settings.get("password")
        self.br.form['password2'] = user_settings.get("password")
        self.br.form['paymentmethod'] = ['bitpay']
        self.br.find_control('accepttos').items[0].selected = True

    def start(self):
        """
        Linux (OpenVZ) and Windows (KVM) pages are slightly different, therefore their pages are parsed by different 
        methoods. Windows configurations allow a selection of Linux distributions, but not vice-versa.
        :return: possible configurations.
        """
        openvz_hosting_page = self.br.open("https://linevast.de/angebote/linux-openvz-vserver-mieten.html")
        options = self.parse_openvz_hosting(openvz_hosting_page.get_data())

        kvm_hosting_page = self.br.open("https://linevast.de/angebote/kvm-vserver-mieten.html")
        options = itertools.chain(options, self.parse_kvm_hosting(kvm_hosting_page.get_data()))
        return options

    def parse_openvz_hosting(self, page):
        soup = BeautifulSoup(page, "lxml")
        table = soup.find('table', {'class': 'plans-block'})
        details = table.tbody.tr
        names = table.findAll('div', {'class': 'plans-title'})
        i = 0
        for plan in details.findAll('div', {'class': 'plans-content'})[1:]:
            option = self.parse_openvz_option(plan)
            option.name = names[i].text.strip() + ' OVZ'
            i = i + 1
            yield option

    @staticmethod
    def parse_openvz_option(plan):
        elements = plan.findAll("div", {'class': 'info'})
        option = VpsOption()
        option.storage = elements[0].text.split(' GB')[0]
        option.cpu = elements[1].text.split(' vCore')[0]
        option.ram = elements[2].text.split(' GB')[0]
        option.bandwidth = 'unmetered'
        option.connection = str(int(elements[4].text.split(' GB')[0]) * 1000)
        option.price = plan.find('div', {'class': 'plans-price'}).span.text.replace(u'\u20AC', '')
        option.purchase_url = plan.a['href']
        return option

    def parse_kvm_hosting(self, page):
        soup = BeautifulSoup(page, "lxml")
        table = soup.find('table', {'class': 'plans-block'})
        details = table.tbody.tr
        names = table.findAll('div', {'class': 'plans-title'})
        i = 0
        for plan in details.findAll('div', {'class': 'plans-content'})[1:]:
            option = self.parse_kvm_option(plan)
            option.name = names[i].text.strip() + ' KVM'
            i = i + 1
            yield option

    @staticmethod
    def parse_kvm_option(plan):
        elements = plan.findAll("div", {'class': 'info'})
        option = VpsOption()
        option.storage = elements[0].text.split(' GB')[0]
        option.cpu = elements[1].text.split(' vCore')[0]
        option.ram = elements[3].text.split(' GB')[0]
        option.bandwidth = 'unmetered'
        option.connection = str(int(elements[4].text.split(' GB')[0]) * 1000)
        option.price = plan.find('div', {'class': 'plans-price'}).span.text.replace(u'\u20AC', '')
        option.purchase_url = plan.a['href']
        return option

    def get_status(self, user_settings):
        clientarea = ClientArea(self.br, self.clientarea_url, user_settings)
        clientarea.print_services()

    def set_rootpw(self, user_settings):
        clientarea = ClientArea(self.br, self.clientarea_url, user_settings)
        info = clientarea.get_service_info()
        self.br.open("https://vm.linevast.de/login.php")
        self.br.select_form(nr=0)
        self.br.form['username'] = info[2]
        self.br.form['password'] = info[3]
        self.br.form.new_control('text', 'Submit', {'name': 'Submit', 'value': '1'})
        self.br.form.new_control('text', 'act', {'name': 'act', 'value': 'login'})
        self.br.form.method = "POST"
        page = self.br.submit()
        if not self._check_login(page.get_data()):
            print("Login failed")
            sys.exit(2)
        self.br.open("https://vm.linevast.de/home.php")
        vi = self._extract_vi_from_links(self.br.links())
        data = {
            'act': 'rootpassword',
            'opt': user_settings.get('rootpw'),
            'vi': vi
        }
        data = urllib.urlencode(data)
        page = self.br.open("https://vm.linevast.de/_vm_remote.php", data)
        if not self._check_set_rootpw(page.get_data()):
            print("Setting password failed")
            sys.exit(2)
        else:
            print("Setting password succesful")

    @staticmethod
    def _extract_vi_from_links(links):
        for link in links:
            if "_v=" in link.url:
                return link.url.split("_v=")[1]
        return False

    @staticmethod
    def _check_set_rootpw(text):
        data = json.loads(text)
        if data['success'] and data['success'] == '1' \
                and data['updtype'] and data['updtype'] == '1' \
                and data['apistate'] and data['apistate'] == '1':
            return True
        return False

    @staticmethod
    def _check_login(text):
        data = json.loads(text)
        if data['success'] and data['success'] == '1':
            return True
        return False

    def get_ip(self, user_settings):
        clientarea = ClientArea(self.br, self.clientarea_url, user_settings)
        info = clientarea.get_service_info()
        print(info[1])
