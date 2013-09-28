# coding: utf-8

from bs4 import BeautifulSoup
from collections import defaultdict
from pymongo import MongoClient
import conf, re, requests, time

digipattern = re.compile(r'\d+')

def first(li):
    try:
        return li[0]
    except IndexError:
        return None

def timestamper():
    return int(time.time())

def fetch_nominees_info(s, ids):
    for id_ in ids:
        ri      = s.get('http://valberedning.sverok.se/admin/nominees/edit/{}'.format(id_))
        soup    = BeautifulSoup(ri.text)
        nominee = {
                    'image'     : first([x.find('img')['src'] for x in soup.find_all('div', 'nominee-image')]),
                    'id'        : int(id_), 
                    'timestamp' : timestamper()
                  }

        for label in soup.find_all('label'):
            lbltxt  = unicode(getattr(label, 'string', u''))
            element = label.find_next_sibling(attrs={'id' : label['for']}) or label.find_previous_sibling(attrs={'id' : label['for']})
            elname  = element.name
            val     = ''

            if elname == 'input' and element['type'] == 'text':
                val = element.get('value', '')
            elif elname == 'textarea':
                val = unicode(getattr(element, 'string', u''))
            elif elname == 'select':
                val = unicode(getattr(element.find('option', selected='selected'), 'string', u''))
            else:
                continue

            if all((lbltxt, val)):
                nominee[lbltxt] = val

        yield nominee

def fetch_questionnaires_info(s, ids):
    for id_ in ids:
        # Map
        ri            = s.get('http://valberedning.sverok.se/admin/questionnaires/edit/{}'.format(id_))
        soup          = BeautifulSoup(ri.text)
        questionnaire = defaultdict(list)

        for t in soup.find_all(['textarea', 'input']):
            if t.name == 'input' and t['type'] not in ['checkbox', 'radio']:
                continue

            if 'visible' in t['name']:
                continue

            curr = {'id' : digipattern.search(t['name']).group()}

            for t1 in t.previous_elements:
                if t1.name == 'h3':
                    curr['header'] = t1.text
                    break

            if t.name == 'textarea':
                curr['val'] = u''.join(t.stripped_strings)

            if t.name == 'input':
                if t['type'] in ['checkbox', 'radio']:
                    # I suppose we got a couple of distinct cases:
                    foundit = False
                    for x in t.children:
                        if x.name == 'label':
                            curr['val'] = x.text
                            foundit = True
                            break

                    if not foundit:
                        curr['val'] = t.next_sibling.text

                    curr['checked'] = bool(t.get('checked', False))

            questionnaire[curr['id']].append(curr)

        # Reduce
        for (k,v) in questionnaire.iteritems():
            acc = v[0]

            if 'checked' in acc:
                acc['val'] = [(acc['val'], acc['checked'])]
                del acc['checked']
            else:
                acc['val'] = [acc['val']]

            for x in v[1:]:
                if 'checked' in x:
                    acc['val'].append((x['val'], x['checked']))
                else:
                    acc['val'].append(x['val'])

            questionnaire[k] = acc

        questionnaire['id'] = int(id_)
        yield questionnaire

def main():
    db = MongoClient('localhost', 27017).db

    s   = requests.Session()
    r1  = s.post('http://valberedning.sverok.se/users/login', data={'data[User][username]' : conf.username, 'data[User][password]' : conf.password})
    r2  = s.get('http://valberedning.sverok.se/admin/nominees')
    ids = filter(bool, [t.get('data-id', '') for t in BeautifulSoup(r2.text).find_all('div', 'nominee-list-item')])

    for n in fetch_nominees_info(s, ids):
        print n
        db.nominees.insert(n)

    for q in fetch_questionnaires_info(s, ids):
        print q
        db.questionnaire.insert(q)

if __name__ == '__main__':
    main()
