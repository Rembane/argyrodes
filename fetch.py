# coding: utf-8

from bs4 import BeautifulSoup
import conf, requests

data = {}

def first(li):
    try:
        return li[0]
    except IndexError:
        return None

def truestr(s):
    if s:
        return s
    else:
        return u''

def main():
    s    = requests.Session()
    r1   = s.post('http://valberedning.sverok.se/users/login', data={'data[User][username]' : conf.username, 'data[User][password]' : conf.password})
    r2   = s.get('http://valberedning.sverok.se/admin/nominees')

    for id_ in filter(bool, [t.get('data-id', '') for t in BeautifulSoup(r2.text).find_all('div', 'nominee-list-item')]):
        ri      = s.get('http://valberedning.sverok.se/admin/nominees/edit/{}'.format(id_))
        soup    = BeautifulSoup(ri.text)
        nominee = [('image', first([x.find('img')['src'] for x in soup.find_all('div', 'nominee-image')]))]
        for label in soup.find_all('label'):
            lbltxt  = unicode(truestr(label.string))
            element = label.find_next_sibling(attrs={'id' : label['for']}) or label.find_previous_sibling(attrs={'id' : label['for']})
            elname  = element.name
            val     = ''

            if elname == 'input' and element['type'] == 'text':
                val = element.get('value', '')
            elif elname == 'textarea':
                val = unicode(truestr(element.string))
            elif elname == 'select':
                val = unicode(truestr(element.find('option', selected='selected').string))
            else:
                continue

            if all((lbltxt, val)):
                nominee.append((lbltxt, val))

        print nominee
        data[id_] = nominee

if __name__ == '__main__':
    main()
