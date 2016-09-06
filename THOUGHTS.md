Started : August 30, Tuesday - 11:33AM

Goal : to build an API that returns the most popular products
from shops near you.

We have
    * `shops.csv`: shops with their coordinates
    * `products.csv`: products per shop along available quantity and global popularity
    * `tags.csv`: a bunch of tags
    * `taggings.csv`: what tags each shop has

Given:
    1. the number (N) of products to return
    2. a pair of coordinates (the user position)
    3. a search radius (how far the search should extend)
    4. optionally, some tags (what types of shops the user wants to see)
Return:
	N most popular products across all shops near the user


===========THOUGHTS==========
***Product***
Let's start by thinking from customer perspective. 
1) As a customer, I want to know what the most popular products are because..
(Q : Why would a customer want to know the most popular products? What defines popularity?
Most importantly, who is the customer here? Is the customer an average shopper who likes to buy
popular or most buyed items? because the customer thinks popular = good quality? In this case, would
ratings or reviews be better than popularity?)
2) As a customer, I want to know the most popular products around me because..
(Q : Why does the customer care about promiximity and search radius? Again, the answer might depend on
who the customer is. If the customer is an average shopper, maybe the customer wants to know the closest shop s/he can go and buy the product. In this case, the transportation distance would be a better option?)
3. As a customer, I want to refine the search by providing tags of the shops because..
(Q : Does the customer know the tags in advance? Should we provide the tags available in the client? A shop needs to have at least one of the tags to be in the search results. So we are refining the results by having the tags 'OR'ed rather than 'AND'ed. Why 'OR', not 'AND'? Should we also provide an 'AND' usecase?)


Other questions:
Who are the other stakeholders in this product? Maybe there is a content editor or administrator? Maybe,
shops can submit their products? What about the company/business? How critical is this product/feature for the business?


***Code***
I understand this is a coding challenge so enough about product. Assume that we have already sorted out
everything with a product manager. Let's think of it as a coding challenge now.
This problem reminds me immediately of k-nearest. Of course, this is not a data classification problem.
We just need to find out the k-nearest items given a position. Let's do a little bit of Google research.
Here it is.
https://en.wikipedia.org/wiki/Nearest_neighbor_search
There are many algorithms available. We know that the data is static. So we don't need to worry about
complexity for add and remove. We just want the best complexity for search. And of course, we are considering a 2d space. https://en.wikipedia.org/wiki/Fixed-radius_near_neighbors
In the client, the user can only choose 10, 20, 50 products. And 100, 500, 1000, 2000m. And 26 tags.
Here are some solutions I can think of after doing some research.

1) We can be absolutely crazy and do all possible search results and store them. Of course, there are quite a lot of possible search queries. (Infinite points on 2D space x 3 x 4 x Combinations of 26 tags). While crazy, this is quite possible given the static nature of the data and not a high amount of data. With regards to infinite points of 2D space, we just need to round the coordinates to be more managable. Building this huge index of results will be very resource intensive but the search time will be O(1). But we are a startup, we might not have the resources. And most importantly, this is not scalable at all. We are scratching this idea.

2) We can of course build a database like elastic search and do a query on all products fitting the distance and tags criteria and sort the products. Search will take O(n) with n being the number of total products and sorting will take O(n log n). Actually, we only need to do partial sorting. 
https://en.wikipedia.org/wiki/Partial_sorting
So total complexity is O(n + k log k) where k is the number of results required. Maybe we can improve that further?

There are 3 dimensions we need to consider. First is popularity. We only need at most 50 most popular products. Next is distance which is at most 2000m. Next is tags.
There are 10k shops and 75k products so 7.5 products per shop. A quick look and calculation of distance in excel shows that 2000m may return from 0 to 5000 shops. So let's assume that 2500 shops are returned on average for query of 2000m. 

3(a) - We sort all the products by popularity beforehand. Then we goes through each product to see if they fit the distance and tag criteria. Worst case would be O(n) and best case would be O(k) where n is the number of products(75k) and k is the number of results wanted. Average would still be O(n). better than solution 2's O(n log n)

3(b) - What if we don't have to scan all the shops or products? We use a quadtree or similar approach, where we can get all the shops within the distance in O(1). http://bl.ocks.org/mbostock/4343214
We determined that 2500 shops (2500 * 7.5 = 18750 products) will be returned on average. We still need to sort it. The complexity here should be O(18570 + k log k). This is assuming that even if we add more shops, we would still have around 2500 stores per 2000m search radius. 

Let's combine solution 1, 3(a) and 3(b). We divide the map into 2000m x 2000m square grids. For every square, we find the products of all stores within the square and all surrounding squares and store the results sorted by popularity. Everytime, we have a query, rather than scanning through all results, we just scan the stored sorted results of the square the user's location is in until we can return the required number of products.

Pseudocode
def search(lat, lng, k, dist, tags):
	x,y = convert(lat,lng)
	sorted_results = get_square(x,y)
	ans = []
	for res in sorted_results:
		if ans.count == k:
			break;
		if tags in res.tags and res.dist(x,y) < dist:
			ans.add(res)
	return res



1. How would your design change if the data was not static (i.e updated frequently
during the day)?
Yes, we have to change the design now. Because everytime we add a new store/product, we have to update the result of each square. This is not scalable if it is updated frequently. I would change the design to 3(b). With 3(b), we use the quadtree to find only close stores and do a partial sort on the products of the store. This design allows partitioning the database as well.

2. Do you think your design can handle 1000 concurrent requests per second? If not, what
would you change?
Still assuming the data is static.
It depends on the architecture(number of processors), load balancing, caching ,etc.
My design stores everything in the memory currently so it might run in to out of memory error (dependin on how much VM we have). It also depends on how long it will take to process one request. If one request takes 30 ms and there is only one machine and single processor, all requests will take 30 seconds in total or the last request will take 30 sec to be returned. This might not be acceptable. 
Again, this will also change when we are using database. 


AFTERTOUGHTS
I went with the design mentioned above. It worked very well. Average query takes 13 sec in my local server. Load test with 10,000 requests took 130 seconds to complete and did not break the server. 1000 concurrent requests will take 13 seconds. This might be acceptable during high bursts. We should show an alert saying that we are experience high load in the front end in this case. But again, we are not using threading, caching and also load balancing. 
We are using a presorted localized search as the alogrithm and putting them in memory. This is not scalable at all and might be overkill. (Need to compare with a traditional database approach to compare performance)

==TODO==
- add comments, documentation
- add unit test, integration tests
- (optional) tags to bitset
- change the data into models and database (not needed right now because data is static and in memory is faster)
- better serving html pages. Right now,, it is a completely static html file served by flask.
- Front end needs a lot of work. The map is not displaying sufficient data to customer. Error handling is poor. Markers(products from same shop) can overlap(temporarily fixed by moving the products randomly a little bit)
- Input/Output validation and sanitiation.
- Error logging and handling
- (optional) caching and threading?


