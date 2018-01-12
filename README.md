# Заголовок

To restart Postgres

```
source myvenv/bin/activate
sudo service postgresql restart

sudo rabbitmq-server -detached
sudo rabbitmqctl status
sudo rabbitmqctl stop

nohup celery -A integrService worker -l info & 

```