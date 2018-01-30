# Заголовок

To start system

```
source myvenv/bin/activate
sudo service postgresql restart

sudo rabbitmq-server -detached
sudo rabbitmqctl status
sudo rabbitmqctl stop

celery -A integrService worker -l info --detach
celery -A integrService status
pkill -9 -f 'celery worker'
celery purge

celery multi start w1 -A integrService -l info # start one or more workers in the background
celery multi restart w1 -A integrService -l info  # restart workers
celery multi stop w1 -A integrService -l info  # stop workers aynchronously
celery multi stopwait w1 -A integrService -l info  # stop after executing tasks are completed

python manage.py runserver $IP:$PORT

rm -rf *.log

```