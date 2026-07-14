from flask import Flask, render_template
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

@app.route("/")
def home():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    cursor = conn.cursor()

    cursor.execute("""
    select
        ds.location_id,
        ds.location_direction,
        ds.time,
        ds.apparent_temperature,
        ds.recommendation_rank,
        ds.eligible,
        sl.latitude,
        sl.longitude,
        ds.reason,
        (
            select array_agg(d2.apparent_temperature order by d2.time)
            from direction_score d2
            where d2.location_id = ds.location_id
        ) as feels_like_sequence
    from direction_score ds
    join stg_locations sl on ds.location_id = sl.location_id
    where ds.time = (select min(time) from direction_score)
    order by ds.recommendation_rank
    """)
    rows = cursor.fetchall()

    cursor.execute("""
        select
            ds.time,
            ds.location_direction,
            ds.apparent_temperature,
            ds.reason
        from direction_score ds
        where ds.recommendation_rank = 1
        order by ds.time
    """)
    outlook = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("index.html", rows=rows, outlook=outlook)

if __name__ == "__main__":
    app.run(debug=True)