# Web robot honeypot

This web robot honeypot was created as an experiment to see what kind of data bots, spammers, hackers and everyone else send to websites in their HTTP requests. The honeypot is just a simple single page website that takes everything the visitors send in their requests, puts it in a database, and then displays the data for everyone. The website always returns the same HTML page even for "invalid" requests unless the visitor requests CSS, JavaScript or any other valid resource. The web page also contains hidden login and message sending forms to collect a bit more data from forum spammers. Going to the web page normally with a web browser however, will not record any data unless the browser sets a referrer (which it probably does).

If you are eager to see some results right now! There's one honeypot set up right here: [bottest.dy.fi](http://bottest.dy.fi)

The website may be down sometimes but it'll come back eventually.

## Collected data

Currently the honeypot saves all invalid queries, cookies, referrers, messages, and login attempts, and also tries to identify bots based on the User-Agent string. For detected bots, the hostname is figured out to make it possible to identify impersonators. The pages requested by bots are also shown, in order to see which bots check the robots.txt file and if they request more than just the HTML.

## Technical stuff

The honeypot is coded in Python and uses the CherryPy web framework to provide the framework for the web server. As such, this Python program can act a web server on its own without a need for a separate proxy server, but it is still possible to run this honeypot behind a proxy.

The program has a custom database implementation which basically consists of storing all the data into a Python dict and dumping the data in JSON format into a file. The data is saved periodically and the program can be stopped and restarted any time without losing data. The program also saves the IPs of visitors and hits in a very tight format, which is arguably a somewhat useless feature.

The server also tries to hide the fact that it is running on CherryPy by removing the "server" header and any error pages and such provided by CherryPy. There is a problem however, when a client sends an invalid HTTP request, the CherryPy server automatically responds with its own 400 bad request page that gives information about the server. There doesn't seem to be a way to override this default behavior.
