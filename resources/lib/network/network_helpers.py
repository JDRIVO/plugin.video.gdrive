import urllib.parse


def addQueryString(url, params):
	return f"{url}?{urllib.parse.urlencode(params)}"


def mergePaths(baseURL, paths):
	return f"{baseURL}/{paths if isinstance(paths, str) else '/'.join(paths)}"


def parseQuery(query):
	return dict(urllib.parse.parse_qsl(query))


def parseURL(urlString):
	url = urllib.parse.urlparse(urlString)
	query = url.query

	if query:
		query = parseQuery(query)

	return {"path": url.path, "query": query}


def quote(string):
	return urllib.parse.quote(string)
