run:
	python wsgi/aic/app.py

create_db: 
	sudo -u postgres createdb -O aic aic 

drop_db:
	sudo -u postgres dropdb aic

demo_run:
	python wsgi/aic/app.py

demo_set_db:
	sudo -u postgres psql aic < aic_crowd_dump
	sudo -u postgres psql aic < update_times
