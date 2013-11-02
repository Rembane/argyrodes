# coding: utf-8

from bs4 import BeautifulSoup
from collections import defaultdict
import conf, re, requests, subprocess, time

template = \
u"""{images}
[b]Namn:[/b] {name}
{info}
[b]Accepterar kandidatur som:[/b] {accepted_nominations}

[b]Presentation:[/b]
{presentation}

{questionnaire}

URL till kandidaten på valberedning.sverok.se: [url={url}]{url}[/url]
"""

image_template = u"[img]http://valberedning.sverok.se{}[/img]"
info_template  = u"[b]{}[/b] {}"
q_template     = u"[b]{}[/b]\n{}"

def first(li):
    try:
        return li[0]
    except IndexError:
        return None

def pairify(xs):
    it = iter(xs)
    while True:
        yield (it.next(), it.next())

def fetch_nominees_info(ids):
    for id_ in ids:
        ri      = requests.get('http://valberedning.sverok.se/nominees/view/{}'.format(id_))
        soup    = BeautifulSoup(ri.text)
        info    = soup.find('div', 'info')
        nominee = {
                    'images'               : [x['src'].strip() for x in getattr(soup.find('div', id='galleri'), 'find_all', lambda x: [])('img')],
                    'name'                 : info.h2.text.strip(),
                    'info'                 : list(pairify(x.text.strip() for x in info.find_all(['label', 'span'], recursive=False))),
                    'accepted_nominations' : [(x.text.split(':')[0].strip(), bool(x.find(text=re.compile(r'Valberedningens ')))) for x in info.find('ul', 'nominations').find_all('li') if x.find_all('span', text=re.compile(r'(Accepterat)|(Valberedningens )'))],
                    'presentation'         : soup.find('div', 'presentation').text.strip(),
                    'url'                  : 'http://valberedning.sverok.se/nominees/view/{}'.format(id_)
                  }

        if not nominee['accepted_nominations']:
            # Skip people who haven't accepted anything
            continue

        form                = soup.find('form')
        nominee['qanswers'] = []
        if form:
            result = []
            for t in form:
                if t.name == 'span' and t.text:
                    if u'Här kommer tre korta' not in t.text:
                        result.append(t.text.strip())
                elif t.name == 'div':
                    if 'textarea' in t.get('class', ''):
                        result.append(t.text.strip())
                    elif 'limit-wrapper' in t.get('class', ''):
                        result.append(', '.join(sorted([x.text for x in t.find_all('label', 'selected')])))
                    elif 'radio' in t.get('class', ''):                    
                        result.append(t.previous_sibling.text.strip())
                        result.append(t.find('input', checked='checked').next_sibling.text.strip())

            nominee['qanswers'] = list(pairify(result))

        yield nominee

def main():
    abbrs = { u'Förbundsordförande'          : u'O',
              u'Vice Förbundsordförande'     : u'VO', 
              u'Förbundssekreterare'         : u'S',
              u'Ledamot i förbundsstyrelsen' : u'L',
              u'Revisor'                     : u'R',
              u'Valberedare'                 : u'VB',
              True                           : u'*',
              False                          : u''
            }

    short_order = dict(zip(['O', 'VO', 'S', 'L', 'VB', 'R'], range(6)))
    def short_sort(li):
        return zip(*sorted([(short_order[x.replace('*', '')], x) for x in li]))[1]

    ids = filter(bool, [t.get('data-id', '') for t in BeautifulSoup(requests.get('http://valberedning.sverok.se').text).find_all('div', 'nominee-list-item') if 'turned-down' not in t['class']])

    for n in fetch_nominees_info(ids):
        shorts                    = ['{}{}'.format(abbrs[x], abbrs[y]) for x,y in n['accepted_nominations']]
        n['accepted_nominations'] = u', '.join(sorted(zip(*n['accepted_nominations'])[0]))
        n['images']               = u' '.join(map(image_template.format, n['images']))
        n['info']                 = u'\n'.join([info_template.format(*x) for x in sorted(n['info'])])
        n['questionnaire']        = u'\n\n'.join([q_template.format(*x) for x in n['qanswers']])
        s = template.format(**n)

        print n['name']
        for x in [u'{} [{}]'.format(n['name'], u','.join(short_sort(shorts))), s]:
            # Copy data to all clipboards
            for args in ('-pi', '-bi'):
                p = subprocess.Popen(['xsel', args], stdin=subprocess.PIPE)
                p.communicate(x.encode('utf-8'))

            raw_input('In buffer!')

if __name__ == '__main__':
    main()
