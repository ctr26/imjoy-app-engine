FROM python:3

ADD ./ /home/app
RUN pip install /home/app
RUN pip install kubernetes

CMD python -m imjoy_cluster_controller & python -m imjoy --serve --port=4000 --host=0.0.0.0 --allow-origin='*'
