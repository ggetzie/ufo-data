import BeautifulSoup as BS

ufo_cols = ['sighted_at', 'reported_at', 'location', 'shape', 'duration', 'description']
zip_cols = ['zip', 'latitude', 'longitude', 'city', 'state', 'county', 'type']

def load_data(filename, delimiter, cols):
    f = open(filename)
    records = []
    for r in f.readlines():
        records.append(dict(zip(cols, [d.strip(' "') for d in r.split(delimiter)] )))
    f.close()
    return records

def load_fips():
    fips_cols = ['state', 'fips', 'county']
    f = open('data/county2k.txt')
    records = []
    for r in f.readlines():
        record = [r[:2], r[2:7], r[7:71].strip()]
        records.append(dict(zip(fips_cols, record)))
    
    # index records by county, state
    rdict = {}
    for r in records:
        try:
            rdict[(r['county'], r['state'])].append(r)
        except KeyError:
            rdict[(r['county'], r['state'])] = [r]
    return records, rdict

def load_enhanced():
    f = open('data/ufo_more_awesome.tsv')
    records = []
    lines = f.readlines()
    cols = lines[0].split('\t')
    for line in lines[1:]:
        records.append(dict(zip(cols, [d.strip(' "') for d in line.split('\t')])))
    f.close()
    return records

def enhance_ufo_data():
    ufos = load_data('data/ufo_awesome.tsv', '\t', ufo_cols)
    zips = load_data('data/ZIP_CODES.txt', ',', zip_cols)
    fips, fips_dict = load_fips()

    # index zip codes by city, state
    zip_dict = {}
    for zipcode in zips:
        try:
            zip_dict[(zipcode['city'], zipcode['state'])].append(zipcode)
        except KeyError:
            zip_dict[(zipcode['city'], zipcode['state'])] = [zipcode]
            
    # create a new set of ufo records with the county included
    # inp = re.compile('\(.*\)')
    with_counties = []
    bad_ones = []
    for ufo in ufos:
        better = ufo.copy()
        try:
            location = remove_parens(ufo['location'])
            cs = [s.upper().strip() for s in location.split(',')]
            if len(cs) != 2:
                bad_ones.append(better)
                continue
            if 'COUNTY' in cs[0]:
                county = cs[0]
            else:
                county = zip_dict[(cs[0], cs[1])][0]['county']
            better['county'] = county
            better['city'] = cs[0]
            better['state'] = cs[1]
        except KeyError:
            bad_ones.append(better)
            continue

        fips_code = findfips(better, fips)
        if fips_code == -1:
            bad_ones.append(better)
        else:
            better['fips'] = fips_code
            with_counties.append(better)

    ma = open('data/ufo_more_awesome.tsv', 'w')
    ks = with_counties[0].keys()
    ks.sort()
    ma.write('\t'.join(ks) + '\n')
    for ufo in with_counties:
        vals = [ufo[k].strip('\n') for k in ks]
        ma.write('\t'.join(vals) + '\n')
    ma.close()
    return with_counties, bad_ones

def color_map():
    wc = load_enhanced()
    sc = sitings_by_county(wc)
    svg = open('data/USA_Counties_with_names.svg', 'r').read()
    soup = BS.BeautifulSoup(svg, selfClosingTags=['defs','sodipodi:namedview'])
    colors = ["#F1EEF6", "#D4B9DA", "#C994C7", "#DF65B0", "#DD1C77", "#980043"]
    paths = soup.findAll('path')

    path_style = 'font-size:12px;fill-rule:nonzero;stroke:#FFFFFF;stroke-opacity:1;stroke-width:0.1;stroke-miterlimit:4;stroke-dasharray:none;stroke-linecap:butt;marker-start:none;stroke-linejoin:bevel;fill:'
    
    for p in paths:
 
        if p['id'] not in ["State_Lines", "separator"]:
            # pass
            try:
                num = sc[p['id']]
            except:
                print "%s not found" % p['id']
                continue
        
            if num > 100:
                color_class = 5
            elif num > 50:
                color_class = 4
            elif num > 20:
                color_class = 3
            elif num > 10:
                color_class = 2
            elif num > 5:
                color_class = 1
            else:
                color_class = 0

            color = colors[color_class]
            p['style'] = path_style + color

    ufomap = open('data/ufomap.svg', 'w')
    ufomap.write(soup.prettify())
    ufomap.close()
    
    
def sitings_by_county(ufodata):
    scount = {}
    for ufo in ufodata:
        scount.setdefault(ufo['fips'], 0)
        scount[ufo['fips']] += 1
    return scount

def findfips(uforec, fipdata):
    
    for fip in fipdata:
        if uforec['county'] in fip['county'].upper() and uforec['state'] == fip['state']:
            return fip['fips']
    return -1

def remove_parens(some_str):
    record = True
    good_str = ""
    
    for c in some_str:

        if c == "(":
            record = False
        if  c == ")":
            record = True
            continue
        if  record:
            good_str += c

    return good_str
    
