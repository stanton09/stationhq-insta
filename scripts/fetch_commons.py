"""Fetch public-domain US military media from Wikimedia Commons for the Veterans Day video."""
import json, os, urllib.request, urllib.parse
OUT = '../content/vets/src'
os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'StationHQ-bot/1.0 (stationhq.app)'}
API = 'https://commons.wikimedia.org/w/api.php?'

import time
def get(url):
    for k in range(6):
        try:
            time.sleep(1.5)
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(10 * (k + 1))
    raise RuntimeError('rate limited')
import urllib.error

Q = {
  'army': 'US Army soldiers salute flag ceremony',
  'navy': 'US Navy sailors aircraft carrier flight deck',
  'airforce': 'US Air Force F-22 flyover',
  'marines': 'US Marines Iwo Jima memorial ceremony',
  'coastguard': 'US Coast Guard cutter rescue helicopter',
  'spaceforce': 'US Space Force guardians ceremony',
  'salute': 'soldier saluting American flag Veterans Day',
  'cemetery': 'Arlington National Cemetery flags in Veterans Day',
  'firefighter': 'Air Force firefighters live fire training',
}
meta = {}
for key, q in Q.items():
    p = dict(action='query', format='json', generator='search', gsrsearch=f'{q} filetype:bitmap',
             gsrnamespace=6, gsrlimit=6, prop='imageinfo', iiprop='url|extmetadata|size', iiurlwidth=1600)
    try:
        r = json.loads(get(API + urllib.parse.urlencode(p)))
    except Exception as e:
        print('ERR', key, e); continue
    pages = sorted(r.get('query', {}).get('pages', {}).values(), key=lambda x: x.get('index', 99))
    n = 0
    for pg in pages:
        ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
        lic = em.get('LicenseShortName', {}).get('value', '')
        if 'public domain' not in lic.lower() and 'pd' not in lic.lower():
            continue
        if ii.get('width', 0) < 1000: continue
        fn = f'{key}_{n}.jpg'
        try:
            open(f'{OUT}/{fn}', 'wb').write(get(ii['thumburl']))
        except Exception as e:
            print('ERR dl', e); continue
        meta[fn] = dict(title=pg['title'], license=lic, artist=em.get('Artist', {}).get('value', '')[:200],
                        url=ii['descriptionurl'])
        n += 1
        if n >= 4: break
    print(key, n)

# Taps audio
for q in ['Taps United States Navy Band', 'Taps bugle call', 'Taps US Army Band']:
    p = dict(action='query', format='json', generator='search', gsrsearch=f'{q} filetype:audio',
             gsrnamespace=6, gsrlimit=3, prop='imageinfo', iiprop='url|extmetadata')
    r = json.loads(get(API + urllib.parse.urlencode(p)))
    for i, pg in enumerate(r.get('query', {}).get('pages', {}).values()):
        ii = pg['imageinfo'][0]; em = ii.get('extmetadata', {})
        lic = em.get('LicenseShortName', {}).get('value', '')
        ext = ii['url'].rsplit('.', 1)[-1]
        fn = f'taps_{len([k for k in meta if k.startswith("taps")])}.{ext}'
        try:
            open(f'{OUT}/{fn}', 'wb').write(get(ii['url']))
        except Exception as e:
            print('ERR audio', e); continue
        meta[fn] = dict(title=pg['title'], license=lic, url=ii['descriptionurl'])
json.dump(meta, open(f'{OUT}/meta.json', 'w'), indent=1)
print(json.dumps(meta, indent=1))
