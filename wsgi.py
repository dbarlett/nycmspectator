import datetime
import simplekml
from collections import OrderedDict
from urllib import urlencode
from flask import Flask
from flask import request
from flask import render_template
from flask import flash
from flask_wtf import Form
from wtforms import SelectField
from flask_wtf.html5 import IntegerField
from wtforms.validators import Required
from wtforms.validators import NumberRange

# Flask parameters
SECRET_KEY = "CHANGE_ME"  # Set a random value for production use

RACE_DIST = 26.2  # miles

# 2014 wave start times as of 2014-10-15
wave_starts = OrderedDict()
wave_starts["Wheelchair"] = datetime.datetime(2014, 11, 2, 8, 30, 0)
wave_starts["Handcycle/Ambulatory"] = datetime.datetime(2014, 11, 2, 8, 55, 0)
wave_starts["Pro Women"] = datetime.datetime(2014, 11, 2, 9, 10, 0)
wave_starts["Pro Men/Wave 1"] = datetime.datetime(2014, 11, 2, 9, 40, 0)
wave_starts["Wave 2"] = datetime.datetime(2014, 11, 2, 10, 5, 0)
wave_starts["Wave 3"] = datetime.datetime(2014, 11, 2, 10, 30, 0)
wave_starts["Wave 4"] = datetime.datetime(2014, 11, 2, 10, 55, 0)

# Coordinates are lon, lat for KML compatibility
viewing_points = {
    1: {
        "Mile": 8,
        "Location": "Lafayette Ave & Flatbush Ave (Fort Greene, Brooklyn)",
        "Coordinates": (-73.967787, 40.687984),
        "Getting there": (
            "<a href='http://www.barclayscenter.com/getting-here'>Barclays "
            "Center</a>, then walk north to Lafayette Ave"
        ),
        "Leaving": "G train from Clinton Ave Queens bound",
        "Notes": (
            "Stay on the south side of Lafayette Ave, that's the right "
            "side of the road for runners. There is a church and a flea "
            "market at the top of the hill, this will be the easiest "
            "place for me to spot you."
        ),
    },
    2: {
        "Mile": 14.5,
        "Location": "44th Drive & 23rd Street (Long Island City, Queens)",
        "Coordinates": (-73.944461, 40.747435),
        "Getting there": (
            "G train to Long Island City - Court Sq. Walk north on block on "
            "23rd St to the south side of 44th Drive, near the Citibank "
            "Building"
        ),
        "Leaving": (
            "7 train Manhattan bound, or E train Brooklyn bound, then transfer "
            "to the 6 train Bronx bound to 110th street."
        ),
        "Notes": (
            "You have to leave here quickly, because you only have $BETWEEN "
            "minutes to reach the next point."
        ),
    },
    3: {
        "Mile": 18.5,
        "Location": "1st Ave & 106th Street",
        "Coordinates": (-73.940037, 40.789615),
        "Getting there": (
            "6 train to 110th Street, walk east to on 110th Street then south "
            "on 1st Ave"
        ),
        "Leaving": "Walk southwest to the Metropolitan Museum of Art",
        "Notes": (
            "Stay on the west side of 1st Avenue so that you can walk over to "
            "Central Park. I will be looking for you on the left (west) side "
            "of the road between 105th and 110th Streets."
        ),
    },
    4: {
        "Mile": 24,
        "Location": (
            "East side of Central Park loop behind the Metropolitan "
            "Museum of Art"
        ),
        "Coordinates": (-73.964882, 40.7798),
        "Getting there": "Walk from point 3",
        "Leaving": "Walk over to the west side of the park",
        "Notes": (
            "Walk over to 5th Avenue and 79th Street, then walk into Central "
            "Park south of the Met. I will be looking for you on the left side "
            "of the road just past the museum."
        ),
    },
}

application = app = Flask(__name__)
app.secret_key = SECRET_KEY


def write_kml(points):
    kml = simplekml.Kml()
    for loc, details in points.items():
        kml.newpoint(
            name=("Point %d (Mile %d)" % (loc, details["Mile"])),
            coords=[details["Coordinates"]],
            description=("ETA: %s" % details["ETA"].strftime("%I:%M %p"))
        )
    kml.save("nycm_viewing.kml")


def generate_plan(wave, hours, minutes):
    goal_time = datetime.timedelta(
        hours=hours,
        minutes=minutes,
    )
    goal_pace_sec = goal_time.seconds / RACE_DIST
    start_time = wave_starts[wave]
    goal_finish = start_time + goal_time
    beer_time = goal_finish + datetime.timedelta(hours=1)

    for details in viewing_points.values():
        eta = start_time + datetime.timedelta(seconds=details["Mile"] * goal_pace_sec)
        details["ETA"] = eta.strftime("%I:%M %p")

    min_between_2_3 = (viewing_points[3]["Mile"] - viewing_points[2]["Mile"]) * goal_pace_sec / 60
    viewing_points[2]["Notes"] = viewing_points[2]["Notes"].replace(
        "$BETWEEN", str(int(min_between_2_3))
    )

    friend_link = "http://nycmarathon.aws.af.cm/?" + urlencode(
        {"wave": wave, "hours": hours, "minutes": minutes}
    )

    #write_kml(viewing_points)
    return (start_time, goal_pace_sec, goal_finish, beer_time, viewing_points, friend_link)


class GoalTimeForm(Form):
    wave = SelectField(
        label="Start",
        choices=[(value, "%s (%s)" % (
            value, label.strftime("%I:%M %p"))
        ) for value, label in wave_starts.items()],
        default="Pro Men/Wave 1",
    )
    hours = IntegerField(
        label="Hours",
        validators=[
            Required(message="Enter goal time hours"),
            NumberRange(
                min=0,
                max=23,
                message="Enter goal time hours between 0 and 23"
            ),
        ]
    )
    minutes = IntegerField(
        label=u"Minutes",
        validators=[
            NumberRange(
                min=0,
                max=59,
                message="Enter goal time minutes between 0 and 59",
            ),
        ]
    )


@app.route("/", methods=["POST", "GET"])
def run():
    form = GoalTimeForm(request.form)
    if request.method == "POST" and form.validate_on_submit():
        plan = generate_plan(
            form.wave.data,
            form.hours.data,
            form.minutes.data,
        )
        start_time = plan[0].strftime("%I:%M %p")
        goal_pace = "%d:%d" % (plan[1] / 60, plan[1] % 60)
        goal_finish = plan[2].strftime("%I:%M %p")
        beer_time = plan[3].strftime("%I:%M %p")
        plan_points = plan[4]
        friend_link = plan[5]
        return render_template(
            "layout.html",
            form=form,
            viewing_points=plan_points,
            start_time=start_time,
            goal_pace=goal_pace,
            goal_finish=goal_finish,
            beer_time=beer_time,
            friend_link=friend_link,
        )
    else:
        if request.args.get("wave"):
            form.wave.data = request.args.get("wave")
        form.hours.data = request.args.get("hours")
        form.minutes.data = request.args.get("minutes")
        return render_template("layout.html", form=form)

if __name__ == '__main__':
    app.run(debug=True)  # Set to False in production
