import os

RSS_URL = 'http://finance.yahoo.com/news/?format=rss'
SECRET_KEY = "klasfiasdf12kCF(uL>ASJ123r5b129cfujxzl;kjashb124e12edljcv"

MAIN_LISTEN_ADDRESS = '0.0.0.0'
MAIN_LISTEN_PORT = 5000
CROWD_LISTEN_ADDRESS = '0.0.0.0'
CROWD_LISTEN_PORT = 5001

production = os.environ.get('OPENSHIFT_POSTGRESQL_DB_URL') is not None

if production:
    DB_URL = os.environ.get('OPENSHIFT_POSTGRESQL_DB_URL')
    DOMAIN = 'http://aic13lab2topic2-mobileworks.rhcloud.com'
    CROWD_DOMAIN = 'http://aic13lab2topic2-mobileworks.rhcloud.com'
else:
    DB_URL = 'postgresql://aic:aic@127.0.0.1/aic'
    DOMAIN = "http://" + MAIN_LISTEN_ADDRESS + ":" + str(MAIN_LISTEN_PORT)
    CROWD_DOMAIN = "http://" + CROWD_LISTEN_ADDRESS + ":" + str(CROWD_LISTEN_PORT)
