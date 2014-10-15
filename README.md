#2014 TCS New York City Marathon Spectator Guide
Copyright 2014 [Dylan Barlett](http://www.dylanbarlett.com) and Brian Danza.

Sample deployment: http://nycmarathon.aws.af.cm/

####Usage

````sh
git clone https://github.com/dbarlett/nycmspectator.git
cd nycmspectator
virtualenv .
source bin/activate
pip install -r requirements.txt
python wsgi.py
````
Browse to http://localhost:5000.

Before deploying to your server, follow the instructions on lines 16 and 204 of `wsgi.py`.
If you have a Google Analytics account, set the ID and domain in `templates/layout.html`.