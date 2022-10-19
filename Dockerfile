# pull base image
FROM eahazardswatch.icpac.net/python-gdal:latest

WORKDIR /usr/src/app/

# install dependencies
RUN pip install --upgrade pip
COPY ./requirements.txt /usr/src/app/requirements.txt
RUN pip install -r requirements.txt

# we have a custom geos, thus install shapely this way, then cartopy
RUN pip install --ignore-installed --no-binary :all: shapely

RUN pip install gunicorn

# copy project
COPY . /usr/src/app/