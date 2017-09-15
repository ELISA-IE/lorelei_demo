__author__ = 'boliangzhang'

import os
from lorelei_demo.app import lorelei_demo_dir


class GeoName(object):
    """
    Main class of GeoName API.
    """
    def __init__(self):
        """
        Load GeoName gaz files.
        """
        self.language_code_dict = self.load_language_code_dict()
        self.countries = self.load_countries()
        self.cities = self.load_cities()
        self.admin1 = self.load_admin1()
        self.admin2 = self.load_admin2()

    def load_language_code_dict(self):
        """
        Load language code dict. Language code dict is used for looking up language code for a given IL language.
        :return: language_code_dict: dict
            Key: str (language name)
            value: list (language codes)
        """
        # load language code
        f = open(os.path.join(
            lorelei_demo_dir,
            'data/name_tagger/gaz/general/GeoName/iso-languagecodes.txt'),
            encoding="utf8"
        )
        f.readline()  # skip the first line

        language_code_dict = dict()  # key is language code, value is language
        language_set = set()
        for line in f:
            line = line.split('\t')
            code = []
            if line[0]:
                code.append(line[0].strip())
            if line[1]:
                code.append(line[1].strip())
            if line[2]:
                code.append(line[2].strip())
            language_code_dict[line[3].strip().lower()] = code

            language_set.add(line[3])

        # print(str(len(language_set)) + ' languages are added.')

        return language_code_dict

    def load_countries(self):
        """
        Load countries.
        :return: countries: list
            It returns a list of Country instances.
        """
        # load country info, country info is used to find which countries speak
        # the IL language
        class Country(object):
            def __init__(self, iso, iso3, iso_numeric, fips, country, capital,
                         continent, languages, neighbours):
                self.iso = iso
                # self.iso3 = iso3
                # self.iso_numeric = iso_numeric
                self.fips = fips
                self.country = country
                self.capital = capital
                self.continent = continent
                self.languages = languages
                self.neighbours = neighbours

        f = open(os.path.join(
            lorelei_demo_dir,
            'data/name_tagger/gaz/general/GeoName/countryInfo.txt'),
            encoding="utf8"
        )
        countries = []
        languages_spoken_in_countries = []
        for line in f:
            if line.startswith('#') or not line:
                continue
            line = line.split('\t')
            iso = line[0]
            iso3 = line[1]
            iso_numeric = line[2]
            fips = line[3]
            country = line[4]
            capital = line[5]
            continent = line[8]
            languages = line[15].split(',')
            languages = [item.split('-')[0] for item in languages]  # some language has area code, e.g., zh-CN, zh-TW
            neighbours = line[17].split(',')

            c = Country(iso, iso3, iso_numeric, fips, country, capital, continent, languages, neighbours)
            languages_spoken_in_countries += c.languages
            countries.append(c)
        # print(str(len(countries))+' countries are added.')
        # print('number of languages spoken in countries: '+str(len(set(languages_spoken_in_countries))))

        return countries

    def load_cities(self):
        """
        Load cities.
        :return: cities: list
            It returns a list of City instances.
        """
        # load cities whose population is greater than 1000.
        class City(object):
            def __init__(self, geonameid, name, asciiname, alternatenames,
                         country_code, latitude, longtitude,
                         population, admin1, admin2):
                self.geonameid = geonameid
                self.name = name
                self.asciiname = asciiname
                self.alternatenames = alternatenames
                self.country_code = country_code
                self.latitude = latitude
                self.longtitude = longtitude
                self.population = population
                self.admin1 = admin1
                self.admin2 = admin2

        f = open(os.path.join(
            lorelei_demo_dir,
            'data/name_tagger/gaz/general/GeoName/cities1000.txt'),
            encoding="utf8"
        )
        cities = []
        for line in f:
            line = line.split('\t')
            geonameid = line[0]
            name = line[1]
            asciiname = line[2]
            alternatenames = set(line[3].split(','))
            latitude = line[4]
            longtitude = line[5]
            country_code = line[8]
            admin1 = line[10]
            admin2 = line[11]
            population = line[14]
            c = City(geonameid, name, asciiname, alternatenames, country_code,
                     latitude, longtitude,
                     population, admin1, admin2)
            cities.append(c)
        # print(str(len(cities))+' cities are added.')

        return cities

    def load_admin1(self):
        class Admin1(object):
            def __init__(self, admin1_code, country_code, name, ascii_name,
                         geonameid):
                self.admin1_code = admin1_code
                self.country_code = country_code
                self.name = name
                self.ascii_name = ascii_name
                self.geonameid = geonameid

        admin1 = []
        f = open(os.path.join(
            lorelei_demo_dir,
            'data/name_tagger/gaz/general/GeoName/admin1CodesASCII.txt'),
            encoding='utf-8'
        )
        for line in f.readlines():
            line = line.split('\t')
            admin1_code = line[0]
            country_code = line[0].split('.')[0]
            name = line[1]
            ascii_name = line[2]
            geonameid = line[3]

            a = Admin1(admin1_code, country_code, name, ascii_name, geonameid)

            admin1.append(a)

        return admin1

    def load_admin2(self):
        class Admin2(object):
            def __init__(self, admin2_code, admin1_code, name, ascii_name,
                         geonameid):
                self.admin2_code = admin2_code
                self.admin1_code = admin1_code
                self.name = name
                self.ascii_name = ascii_name
                self.geonameid = geonameid

        admin2 = []
        f = open(os.path.join(
            lorelei_demo_dir,
            'data/name_tagger/gaz/general/GeoName/admin2Codes.txt'),
            encoding='utf-8'
        )
        for line in f.readlines():
            line = line.split('\t')
            admin2_code = line[0]
            admin1_code = '.'.join(line[0].split('.')[:2])
            name = line[1]
            ascii_name = line[2]
            geonameid = line[3]

            a = Admin2(admin2_code, admin1_code, name, ascii_name, geonameid)

            admin2.append(a)

        return admin2

    def search_city_by_country(self, country='', country_code=''):
        """
        Lookup cities based on given country name.
        :param country: str
        :return: cities: list
            List of city instances.
        """
        # get country code
        if not country_code:
            for c in self.countries:
                if c.country.lower() == country.lower():
                    country_code = c.iso
        # get cities by country code
        cities = []
        for c in self.cities:
            if c.country_code.lower() == country_code.lower():
                cities.append(c)

        return cities

    def search_city_by_language(self, language):
        """
        Lookup cities based on language.
        :param language: str
        :return: cities: list
            List of city instances.
        """
        # lookup language code
        try:
            language_code = self.language_code_dict[language.lower()]
        except KeyError:
            print("couldn't find language code for this language.")
            raise

        countries = []  # countries that speak the given language
        for c in self.countries:
            if len(set(language_code) & set(c.languages)) > 0:
                countries.append(c)

        cities = []
        for c in countries:
            cities += self.search_city_by_country(c.country)

        return cities

    def search_city_by_continent(self, continent='', continent_code=''):
        """
        Lookup citites based on continent
        :param continent: str
        :param continent_code: str
        :return: cities: list
            List of city instances.
        """
        continent_abbr = {'africa': 'AF',
                          'antarctica': 'AN',
                          'asia': 'AS',
                          'europe': 'EU',
                          'north america': 'NA',
                          'oceania': 'OC',
                          'south and central america': 'SA',
                          }
        if not continent_code:
            try:
                continent_code = continent_abbr[continent.lower()]
            except KeyError:
                print('invalid continent name.')
                raise

        countries = []
        for c in self.countries:
            if c.continent == continent_code:
                countries.append(c)

        cities = []
        for c in countries:
            cities += self.search_city_by_country(c.country)

        return cities

    def search_all_countries(self):
        """
        Return all coutries names which are in many kinds of languages (depends
        on GeoName database).

        :return:    List of countries names (string).
        """
        countries = []
        for c in self.countries:
            countries.append(c.country)

        return countries

    def search_all_cities(self):
        """
        Return all cities names in many kinds of languages (depends on GeoName
         database).

        :return:    List of cities names (string).
        """
        cities = []
        for c in self.cities:
            cities += [c.name] + list(c.alternatenames)

        return cities

    def search_city_position(self, city):
        city = self.query_to_city(city)

        if not city:
            return None, None

        admin1 = ''
        if ',' in city:
            city, admin1 = [item.strip() for item in city.split(',')]

        found_cities = []
        for c in self.cities:
            if city == c.name or city in c.alternatenames:
                found_cities.append(c)

        if not found_cities:
            return None, None

        # locate city by admin1 code
        if admin1:
            for c in found_cities:
                c_admin1 = '%s.%s' % (c.country_code, c.admin1)
                for a in self.admin1:
                    if a.admin1_code == c_admin1:
                        if a.name == admin1:
                            return c.latitude, c.longtitude

        # if cities with similar name found, return one with largest population
        res = None
        population = 0
        for c in found_cities:
            if int(c.population) > int(population):
                res = c
                population = c.population

        return res.latitude, res.longtitude

    def is_loc(self, query):
        for country in self.countries:
            if query == country.country:
                return True
        for city in self.cities:
            if query == city.name or query in city.alternatenames:
                return True
        for a1 in self.admin1:
            if query in [a1.name, a1.ascii_name]:
                return True
        for a2 in self.admin2:
            if query in [a2.name, a2.ascii_name]:
                return True

        return False

    def get_country_capital(self, country):
        for c in self.countries:
            if c.country == country:
                capital = c.capital
                return capital

        return None

    def query_to_city(self, query):
        # if query is a country, returns its capital
        if query in self.search_all_countries():
            capital = self.get_country_capital(query)
            if capital:
                return capital

        return query


if __name__ == "__main__":
    # word_count()
    # city_gaz_loader("Yoruba")

    geo_name = GeoName()

    # china_cities = geo_name.search_city_by_country('CHINA')
    # print(len(china_cities))
    # asia_cities = geo_name.search_city_by_continent('asia')
    # print(len(asia_cities))
    # chinese_cities = geo_name.search_city_by_language('chinese')
    # print(len(chinese_cities))
    # world_countries = geo_name.search_all_countries()

    pass
