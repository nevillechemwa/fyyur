#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from sqlalchemy.exc import SQLAlchemyError
from flask_wtf import Form
from forms import *
import sys
from models import db, Artist, Venue, Shows
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)
db.init_app(app)

# TODO: connect to a local postgresql database



#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()

  locations = set()
  for venue in venues:
    locations.add((venue.city, venue.state))
  
  data = []
  for location in locations:
    data.append({
      "city": location[0],
      "state": location[1],
      "venues": []
    })
  
  for venue in venues:
    current_time = datetime.now()
    upcoming_shows = [show for show in venue.shows if show.start_time > current_time]
    
    for i in range(0, len(data)):
      if venue.city == data[i]['city'] and venue.state == data[i]['state']:
        data[i]['venues'].append({
          "id": venue.id,
          "name": venue.name,
          "num_upcoming_shows": len(upcoming_shows)
        })
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  search_term = request.form.get('search_term')
  venues = Venue.query.filter(Venue.name.ilike('%{}%'.format(search_term))).all()
  data =[]
  for venue in venues:
    showsAvail = Shows.query.filter_by(venue_id=venue.id)
    numUpcomingShows = (showsAvail.filter(Shows.start_time > datetime.now())).count()
    venue_data = {
      "id" : venue.id,
      'name' : venue.name,
      'num_upcoming_shows' : numUpcomingShows}
    data.append(venue_data)
  response={
    "count": len(data),
    "data": data}
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  venue= Venue.query.filter_by(id=venue_id).first()
  past_shows = []
  upcoming_shows = []
  shows = Shows.query.filter_by(venue_id=venue_id)
  for show in shows:
    artist=Artist.query.filter_by(id=show.artist_id).first()
    artist_info = {
      "artist_id": show.artist_id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time" : str(show.start_time)
    }
    if show.start_time <= datetime.now():
      past_shows.append(artist_info)
    else:
      upcoming_shows.append(artist_info)  
  data={
    "id": venue.id,
    "name": venue.name,
    "genres": venue.genres,
    "address": venue.address,
    "city": venue.city,
    "state": venue.state,
    "phone": venue.phone,
    "website_link": venue.website_link,
    "facebook_link": venue.facebook_link,
    "seeking_talent": venue.seeking_talent,
    "seeking_description": venue.seeking_description,
    "image_link": venue.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  
  # form = VenueForm(request.form)
  # if form.validate():
  try:
    # seeking_talent = False
    # seeking_description = ''
    # if 'seeking_talent' in request.form:
    #   seeking_talent = request.form['seeking_talent'] == 'y'
    # if 'seeking_description' in request.form:
    #   seeking_description = request.form['seeking_description']
    venue = Venue(
      name=request.form['name'],
      genres=request.form.getlist('genres'),
      address=request.form['address'],
      city=request.form['city'],
      state=request.form['state'],
      phone=request.form['phone'],
      website_link=request.form['website_link'],
      facebook_link=request.form['facebook_link'],
      image_link=request.form['image_link'],
      seeking_talent=request.form['seeking_talent'],
      seeking_description=request.form['seeking_description'],
    )
    #insert new venue records into the db
    db.session.add(venue)
    db.session.commit()
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  except SQLAlchemyError as e:
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  try:
    venue = Venue.query.get(venue_id)
    db.session.delete(venue)
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  artists = Artist.query.all()
  data =[]
  for artist in artists:
    reply={"id":artist.id, "name":artist.name}
    data.append(reply)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search_term = request.form.get('search_term')
  artists = Artist.query.filter(Artist.name.ilike('%{}%'.format(search_term))).all()
  data =[]

  for artist in artists:
    showsAvail = Shows.query.filter_by(artist_id=artist.id)
    numUpcomingShows = (showsAvail.filter(Shows.start_time > datetime.now())).count()
    artist_data = {
      "id" : artist.id,
      'name' : artist.name,
      'num_upcoming_shows' : numUpcomingShows
    }
    data.append(artist_data)
    
  response={
    "count": len(data),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id 

  artist = Artist.query.filter_by(id=artist_id).first()
  shows = Shows.query.filter_by(artist_id=artist_id).all()
  past_shows = []
  upcoming_shows = []
  for show in shows:
    venue = Venue.query.filter_by(id=show.venue_id).first()
    venue_data = {"venue_id": show.venue_id, "venue_name": venue.name, "venue_image_link":venue.image_link, "start_time":str(show.start_time)}
    if show.start_time <= datetime.now():
      past_shows.append(venue_data)
    else:
      upcoming_shows.append(venue_data) 
  data={
    "id": artist.id,
    "name": artist.name,
    "genres": artist.genres,
    "city": artist.city,
    "state": artist.state,
    "phone": artist.phone,
    "website_link": artist.website_link,
    "facebook_link": artist.facebook_link,
    "seeking_venue": artist.seeking_venue,
    "seeking_description": artist.seeking_description,
    "image_link": artist.image_link,
    "past_shows": past_shows,
    "upcoming_shows": upcoming_shows,
    "past_shows_count": len(past_shows),
    "upcoming_shows_count": len(upcoming_shows)}
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist=Artist.query.filter_by(id = artist_id).first()

  form.name.data = artist.name
  form.genres.data = artist.city
  form.state.data = artist.state
  form.phone.data = artist.phone
  form.genres.data = artist.genres
  form.image_link.data = artist.image_link
  form.facebook_link.data = artist.facebook_link
  form.website_link.data = artist.website_link
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  artist = Artist.query.filter_by(id=artist_id).first()
  try:
    artist.name = request.form['name']
    artist.city = request.form['city']
    artist.state = request.form['state']
    artist.phone = request.form['phone']
    artist.genres = request.form.getlist('genres')
    artist.image_link = request.form['image_link']
    artist.facebook_link = request.form['facebook_link']
    artist.website_link = request.form['website_link']
    artist.seeking_venue = request.form['seeking_venue']
    artist.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  venue = Venue.query.filter_by(id=venue_id).first()
  try:
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.image_link = request.form['image_link']
    venue.genres = request.form.getlist('genres')
    venue.facebook_link = request.form['facebook_link']
    venue.website_link = request.form['website_link']
    venue.seeking_talent = request.form['seeking_talent']
    venue.seeking_description = request.form['seeking_description']
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  try:
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    phone = request.form['phone']
    genres = request.form.getlist('genres')
    image_link = request.form['image_link']
    facebook_link = request.form['facebook_link']
    website_link = request.form['website_link']
    seeking_venue = request.form['seeking_venue']
    seeking_description = request.form['seeking_description']
    artist = Artist(name=name,city=city,state=state,phone=phone,genres=genres,image_link=image_link,facebook_link=facebook_link,website_link=website_link,seeking_venue=seeking_venue,seeking_description=seeking_description)
    db.session.add(artist)
    db.session.commit()

  except:
    error = True
    print(sys.exc_info())
  finally:
    db.session.close()
    if error:
      # on unsuccessful db insert, flash success
      flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
    else:
      # on successful db insert, flash success
      flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  data=[]
  shows = Shows.query.order_by(Shows.start_time.desc()).all()
  for show in shows:
    artist = Artist.query.filter_by(id=show.artist_id).first()
    venue = Venue.query.filter_by(id=show.venue_id).first()
    info =  {"venue_id": show.venue_id, "venue_name": venue.name, "artist_id": show.artist_id, "artist_name": artist.name, "artist_image_link":artist.image_link, "start_time":str(show.start_time)}
    data.append(info)
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm(request.form)
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead
  try:
    artist_id = request.form['artist_id']
    venue_id = request.form['venue_id']
    start_time = request.form['start_time']
    new_show = Shows(artist_id=artist_id,venue_id=venue_id,start_time=start_time)
    db.session.add(new_show)
    db.session.commit()
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  except:
    db.session.rollback()
    # on unsuccessful db insert, flash Error
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
