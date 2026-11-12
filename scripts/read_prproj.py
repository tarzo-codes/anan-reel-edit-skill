"""Read a Premiere .prproj WITHOUT Premiere (works while the MCP bridge is busy or Premiere is closed).

  python read_prproj.py project.prproj out.json [--print SEQUENCE_NAME]

Dumps every sequence: tracks, clips (start/end/in/speed/file or nested sequence), effects with their
keyframes (times in source seconds; adjustment layers and graphics start at 3600 s), readable strings
from text layers (font names + the words), and transitions. Use it to read a past reel's edit, or to
re-learn the style from a newer project. The file is gzipped XML; it is copied, never modified.
"""
import gzip, tempfile, os
import sys, re, json, base64, xml.etree.ElementTree as ET
TPS = 254016000000
src = sys.argv[1]
if src.lower().endswith('.prproj'):
    root = ET.fromstring(gzip.open(src).read())
else:
    root = ET.parse(src).getroot()
byid, byuid = {}, {}
for el in root:
    if 'ObjectID' in el.attrib: byid[el.attrib['ObjectID']] = el
    if 'ObjectUID' in el.attrib: byuid[el.attrib['ObjectUID']] = el
def ref(e):
    if e is None: return None
    if 'ObjectRef' in e.attrib: return byid.get(e.attrib['ObjectRef'])
    if 'ObjectURef' in e.attrib: return byuid.get(e.attrib['ObjectURef'])
    return None
def f(e, path):
    """path like 'ClipTrackItem/TrackItem/Start'; follows refs automatically"""
    cur = e
    for p in path.split('/'):
        if cur is None: return None
        nxt = cur.find(p)
        if nxt is None: return None
        r = ref(nxt)
        cur = r if r is not None else nxt
    return cur
def txt(e, path):
    x = f(e, path); return x.text if x is not None else None
def sec(t): return round(int(t)/TPS, 3) if t not in (None,'') else None

def params(comp):
    out = {}
    ps = f(comp, 'Component/Params') 
    if ps is None: return out
    for p in ps:
        pe = ref(p)
        if pe is None: continue
        name = pe.findtext('Name') or pe.findtext('Component/Name') or ''
        kf = pe.findtext('Keyframes'); start = pe.findtext('StartKeyframe'); cv = pe.findtext('CurrentValue')
        tv = pe.findtext('IsTimeVarying')
        if pe.tag == 'ArbVideoComponentParam':
            sv = pe.findtext('StartKeyframeValue') or ''
            # pull readable strings out of base64 blobs (text layers)
            strs = []
            for blob in [sv] + re.findall(r'[A-Za-z0-9+/=]{40,}', kf or ''):
                try:
                    raw = base64.b64decode(blob + '=' * (-len(blob) % 4))
                    for m in re.findall(rb'(?:[\x20-\x7e]\x00){3,}', raw): strs.append(m.decode('utf-16le'))
                    for m in re.findall(rb'[\x20-\x7e]{4,}', raw): strs.append(m.decode())
                except Exception: pass
            if strs: out[name or 'arb'] = {'strings': list(dict.fromkeys(strs))[:12]}
            continue
        d = {}
        if tv == 'true' and kf: 
            keys = [k.split(',') for k in kf.strip(';').split(';') if k]
            d['keys'] = [(round(int(k[0])/TPS - 0,3), k[1] if len(k)>1 else None) for k in keys][:12]
            d['nkeys'] = len(keys)
        else:
            v = start or cv
            if v: d['v'] = v.split(',')[1] if (start and ',' in v) else v
        if d: out[name or pe.tag] = d
    return out

def effects(item):
    chain = f(item, 'ClipTrackItem/ComponentOwner/Components')
    res = []
    if chain is None: return res
    comps = f(chain, 'ComponentChain/Components')
    if comps is None: return res
    for c in comps:
        ce = ref(c)
        if ce is None: continue
        dn = ce.findtext('Component/DisplayName') or ce.findtext('DisplayName') or ce.findtext('MatchName') or ce.tag
        res.append({'fx': dn, 'match': ce.findtext('MatchName'), 'params': params(ce)})
    return res

def media_of(item):
    sc = f(item, 'ClipTrackItem/SubClip')
    name = sc.findtext('Name') if sc is not None else None
    clip = f(sc, 'Clip') if sc is not None else None
    info = {'name': name}
    if clip is not None:
        c = clip.find('Clip')
        if c is not None:
            info['in'] = sec(c.findtext('InPoint')); info['out'] = sec(c.findtext('OutPoint'))
            info['speed'] = c.findtext('PlaybackSpeed')
            src = ref(c.find('Source'))
            if src is not None:
                med = f(src, 'MediaSource/Media')
                if med is not None:
                    info['file'] = med.findtext('ActualMediaFilePath') or med.findtext('FilePath') or med.findtext('Title')
                seq = f(src, 'SequenceSource/Sequence')
                if seq is not None: info['nested'] = seq.findtext('Name')
    return info

out = {}
for seq in root.iter('Sequence'):
    if 'ObjectUID' not in seq.attrib: continue
    sname = seq.findtext('Name')
    S = {'tracks': []}
    tgs = seq.find('TrackGroups')
    for tg in (tgs if tgs is not None else []):
        g = ref(tg.find('Second'))
        if g is None: continue
        kind = g.tag
        if kind == 'VideoTrackGroup':
            S['fw'] = g.findtext('FrameRect'); S['frame'] = g.findtext('TrackGroup/FrameRate')
        tracks = f(g, 'TrackGroup/Tracks')
        if tracks is None: continue
        for ti, t in enumerate(tracks):
            te = ref(t)
            if te is None: continue
            T = {'kind': te.tag, 'idx': ti, 'items': [], 'transitions': []}
            ci = te.find('ClipTrack/ClipItems/TrackItems')
            if ci is not None:
                for it in ci:
                    ie = ref(it)
                    if ie is None: continue
                    st = sec(f(ie, 'ClipTrackItem/TrackItem/Start').text if f(ie,'ClipTrackItem/TrackItem/Start') is not None else 0)
                    en = sec(txt(ie, 'ClipTrackItem/TrackItem/End'))
                    d = {'start': st, 'end': en}
                    d.update(media_of(ie))
                    if kind=='VideoTrackGroup' or True: d['fx'] = effects(ie)
                    T['items'].append(d)
            tr = te.find('ClipTrack/TransitionItems/TrackItems')
            if tr is not None:
                for it in tr:
                    ie = ref(it)
                    if ie is None: continue
                    st = sec(ie.findtext('.//TrackItem/Start') or 0); en = sec(ie.findtext('.//TrackItem/End'))
                    T['transitions'].append({'start': st, 'end': en, 'name': ie.findtext('.//DisplayName')})
            if T['items'] or T['transitions']: S['tracks'].append(T)
    out[sname] = S
json.dump(out, open(sys.argv[2],'w'), indent=1, default=str)
for k,v in out.items():
    n = sum(len(t['items']) for t in v['tracks'])
    ends = [i['end'] for t in v['tracks'] for i in t['items'] if i['end']]
    print(f"{k!r}: {len(v['tracks'])} tracks, {n} items, len {max(ends) if ends else 0}s, frame={v.get('frame')} rect={v.get('fw')}")

if '--print' in sys.argv:
    name = sys.argv[sys.argv.index('--print') + 1]
    for t in out[name]['tracks']:
        print(f"-- {t['kind']} #{t['idx']}")
        for tr in t['transitions']: print(f"   [TRANS] {tr['start']}-{tr['end']} {tr['name']}")
        for i in t['items']:
            src = ('nest:' + i['nested']) if i.get('nested') else os.path.basename(str(i.get('file') or ''))
            print(f"   {i['start']:>7}-{i['end']:<7} {str(i.get('name'))[:40]:40} {src} in={i.get('in')}")
            for fx in i['fx']:
                ps = [f"{k}:{v['nkeys']}k{[x[1] for x in v['keys'][:4]]}@{[x[0] for x in v['keys'][:4]]}" if 'keys' in v
                      else f"{k}:{v['strings'][:4]}" for k, v in fx['params'].items() if 'keys' in v or 'strings' in v]
                if ps: print(f"        fx {fx['fx']}: " + '; '.join(ps[:6]))
