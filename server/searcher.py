from flask import current_app
from haversine import haversine

import csv

# This is predetermined by analyzing locations of shops.
LAT_START = 59.166
LAT_INC = 0.01799
LAT_COUNT = 18
LNG_START = 17.866
LNG_INC = 0.0351
LNG_COUNT = 10

# Change lat and lng to grid coordinates
def _map_grid(lat, lng):
    x = (lat - LAT_START) / LAT_INC
    y = (lng - LNG_START) / LNG_INC
    if x < 0 or x >= LAT_COUNT or y < 0 or y >= LNG_COUNT:
        return None
    return int(x), int(y)

# Input class. For sanitization and validation
# TODO: Use an existing library or package
class Input:
    def __init__(self, args):
        _lat = args.get('lat')
        _lng = args.get('lng')
        _radius = args.get('radius')
        _count = args.get('count')
        _tags = args.get('tags')
        self.input_errors = []
        try:
            self.lat = float(_lat)
            self.lng = float(_lng)
            self.radius = int(_radius)
            self.count = int(_count)
        except ValueError:
            self.input_errors.append('One or more of the inputs is not a number')
            return
        #Split the tags and filter out empty strings
        self.tags = filter(bool,_tags.split(','))

        if self.lat < -90 or self.lat > 90:
            self.input_errors.append('lat must be between -90 and 90')

        if self.lng < -180 or self.lng > 180:
            self.input_errors.append('lng must be between -180 and 180')

        if self.radius < 100 or self.lat > 2000:
            self.input_errors.append('radius must be between 100 and 2000')

        if self.count < 0 or self.count > 100:
            self.input_errors.append('count must be between 0 and 100')

# Searcher class. Loads the data and perform a localized search on products.
class Searcher:

    def __init__(self):
        self.s = {} #shops
        # initialize the grid
        # We break down the geo map into a 2d grid composed of approximatey 2m x 2m squares
        # Each grid consists of products in own square and surrounding squares(aprox 2m radius) sorted by popularity
        self.grid = [[[] for y in range(LNG_COUNT)] for x in range(LAT_COUNT)]
        return

    #Loads shops into memory
    def _load_shops(self, shops_file):
        with open(shops_file,"r") as f:
            # Skip first line column headers
            next(f)
            for line in csv.reader(f):
                sid = line[0]
                shop = {
                    'name' : line[1],
                    'lat' : float(line[2]),
                    'lng' : float(line[3]),
                    'tags' : []
                }
                self.s[sid] = shop

    #Loads products into memory and grid
    def _load_products(self, products_file):
        with open(products_file,"r") as f:
            # Skip first line column headers
            next(f)
            for line in csv.reader(f):
                pid = line[0]
                sid = line[1]
                title = line[2]
                popularity = line[3]
                quantity = line[4]

                #Find the corresponding shop and map them into grid
                x, y = _map_grid(self.s[sid]['lat'], self.s[sid]['lng'])

                #Put the products in own square and surrounding squares
                #Use min, max to handle out of bounds case
                for i in range(max(x-1, 0), min(x+2,LAT_COUNT)):
                    for j in range(max(y-1, 0), min(y+2,LNG_COUNT)):
                        product = {
                            'pid' : pid,
                            'sid' : sid,
                            'title' : title,
                            'popularity' : popularity,
                            'quantity' : quantity
                        }
                        self.grid[i][j].append(product)

    #Loads tags and assign tags to shops
    def _load_tags(self, tags_file, taggings_file):
        tags = {}
        with open(tags_file,"r") as f:
            # Skip first line column headers
            next(f)
            for line in csv.reader(f):
                tid = line[0]
                tag = line[1]
                tags[tid] = tag

        with open(taggings_file,"r") as f:
            # Skip first line column headers
            next(f)
            for line in csv.reader(f):
                sid = line[1]
                tid = line[2]
                self.s[sid]['tags'].append(tags[tid])


    def setup(self, data_path):
        #Read and load from shops.csv
        shops_file = u"%s/%s" % (data_path, 'shops.csv')
        self._load_shops(shops_file)


        #Read and load from tags.csv and taggings.csv
        tags_file = u"%s/%s" % (data_path, 'tags.csv')
        taggings_file = u"%s/%s" % (data_path, 'taggings.csv')
        self._load_tags(tags_file, taggings_file)


        #Read and load from products.csv
        products_file = u"%s/%s" % (data_path, 'products.csv')
        self._load_products(products_file)

        # Pre-sort all the grid squares
        for x in range(LAT_COUNT):
            for y in range(LNG_COUNT):
                self.grid[x][y].sort(key=lambda i: i['popularity'], reverse=True)


    # Return search results of products near you.
    # ins - Input class. Validated and Sanitized.
    def search(self, ins):
        lat = ins.lat
        lng = ins.lng
        radius = ins.radius
        count = ins.count
        tags = ins.tags
        res = []
        print(lat, lng, radius, count, tags)

        loc = _map_grid(lat, lng)
        # If not loc, out of bounds, return no results
        if loc:
            for item in self.grid[loc[0]][loc[1]]:
                # break when got desired results
                if len(res) >= count:
                    break

                sid = item['sid']
                shop = self.s[sid]

                # Calculate distance and checks within radius
                # Check if tags match
                dist = haversine((lat,lng), (shop['lat'], shop['lng'])) * 1000
                tagged = False
                print(dist, radius)
                if dist <= radius:
                    print('yay')
                    print(len(tags))
                    print(tags)
                    # TODO : change it to bitset
                    if len(tags) > 0 :
                        for tag in tags:
                            if tag in shop['tags']:
                                tagged = True
                    else:
                        tagged = True

                    if tagged:
                        # Create a new object here instead of returning the product to hide sid and pid
                        res.append({
                            'title' : item['title'],
                            'shop' : shop,
                            'popularity' : item['popularity'],
                            'quantity' : item['quantity']
                            })
        return res
