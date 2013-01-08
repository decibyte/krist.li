#!/usr/bin/python
# -*- coding: utf-8 -*-

import urllib, re
from flask import Flask, render_template, redirect, make_response

app = Flask(__name__)

url_cache = {} # This is used to remember URLs that has already been looked up, to limit the amount of request that are done to guess canonical URLs.

def lookup_url(dec_id):
    """Fetch the content of the article URL with article_id=dec_id and search for the canonical URL in the returning markup."""
    page = urllib.urlopen('http://www.kristeligt-dagblad.dk/artikel/%i' % dec_id)
    markup = page.read()
    canonical_url = re.search('<link rel="canonical" href="(.+)" />', markup)
    if not canonical_url:
        return None
    else:
        article_title = re.search('<title>([^<]+)</title>', markup)
        if article_title:
            title = article_title.group(1)
        else:
            title = canonical_url.group(1)
        return canonical_url.group(1), title

def get_url(dec_id):
    """Get the URL (and it's number of hits) for article with article_id=dec_id."""
    in_cache = dec_id in url_cache.keys()
    if not in_cache:
        url, title = lookup_url(dec_id)
        if url:
            url_cache[dec_id] = {
                'url' : url,
                'title' : title.decode('iso-8859-1'),
                'hits' : 1,
            }
        else:
            return {
                'url' : None,
                'title' : 'Not Found',
                'hits' : 0,
            }
    else:
        url_cache[dec_id]['hits'] += 1
    return url_cache[dec_id]

@app.route('/')
def index():
    """Front page of the URL shortener."""
    stats = sorted(url_cache.values(), key=lambda k: k['hits'], reverse=True) 
    return render_template('index.html', stats=stats)

@app.route('/x<base36_id>')
def xoops_base36_id(base36_id):
    """
        The route to handle base36 article ID's and redirect to the proper aricle URL.
        Note: The 'x' prefix tells us that this is an Xoops article. Other prefixes will be used in the future.
    """
    try:
        dec_id = int(base36_id, 36)
    except ValueError:
        return render_template('error.html', wrong_id='x%s' % base36_id), 404
    lookup = get_url(dec_id)
    if not lookup['url']:
        return render_template('error.html', wrong_id='x%s' % base36_id), 404
    response = make_response(redirect(lookup['url']))
    response.headers['X-Hits-Since-Last-Restart'] = lookup['hits']
    return response

if __name__ == '__main__':
    #app.debug = True
    app.run()
