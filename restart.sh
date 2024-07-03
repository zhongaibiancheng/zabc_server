cd log
cat gunicorn.pid|xargs kill -9
rm -rf *.*
cd ../
gunicorn --config=gunicorn_config.py zabcsystem:app
