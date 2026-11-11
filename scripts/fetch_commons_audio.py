import json, os, time, urllib.request, urllib.parse, urllib.error
OUT = '../content/vets/src'; os.makedirs(OUT, exist_ok=True)
UA = {'User-Agent': 'StationHQ-bot/1.0 (stationhq.app)'}
API = 'https://commons.wikimedia.org/w/api.php?'
def get(url):
    for k in range(6):
        try:
            time.sleep(2); return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=90).read()
        except urllib.error.HTTPError as e:
            if e.code != 429: raise
            time.sleep(15 * (k + 1))
meta = {}
for q in ['Armed Forces Medley', 'Armed Forces Salute band', 'Armed Forces Medley United States Navy Band', 'Stars and Stripes Forever United States Marine Band']:
    p = dict(action='query', format='json', generator='search', gsrsearch=f'{q} filetype:audio', gsrnamespace=6, gsrlimit=4, prop='imageinfo', iiprop='url|extmetadata')
    r = json.loads(get(API + urllib.parse.urlencode(p)))
    for pg in r.get('query', {}).get('pages', {}).values():
        if pg['title'] in [m['title'] for m in meta.values()]: continue
        ii = pg['imageinfo'][0]; lic = ii.get('extmetadata', {}).get('LicenseShortName', {}).get('value', '')
        ext = ii['url'].split('?')[0].rsplit('.', 1)[-1]
        fn = f'med_{len(meta)}.{ext}'
        try: open(f'{OUT}/{fn}', 'wb').write(get(ii['url']))
        except Exception as e: print('ERR', e); continue
        meta[fn] = dict(title=pg['title'], license=lic, url=ii['descriptionurl'])
json.dump(meta, open(f'{OUT}/meta_audio.json', 'w'), indent=1)
print(json.dumps(meta, indent=1))
