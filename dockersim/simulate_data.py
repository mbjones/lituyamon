#!/usr/bin/env python
from datetime import datetime
from datetime import timedelta
from time import sleep
import random
import psycopg2


def main():
    try:
        connection = connect_db()
        x = 1
        while(x < 10000):
            record_measures(connection, x)
        #query_db(connection)
    finally:
        #closing database connection.
        if(connection):
            connection.close()
            print("PostgreSQL connection is closed")

def record_measures(connection, x):
    now = datetime.today()
    range_min = 20
    range_max = 40
    humid_min = 30
    humid_max = 80
    value = random.randrange(range_min, range_max)
    insert_metric(connection, x, "Temperature", now, "Engine Room", value)
    value = random.randrange(range_min, range_max)
    insert_metric(connection, x, "Temperature", now, "Salon", value)
    value = random.randrange(range_min, range_max)
    insert_metric(connection, x, "Temperature", now, "Forward Cabin", value)
    humidity = random.randrange(humid_min, humid_max)
    insert_metric(connection, x, "Humidity", now, "Forward Cabin", humidity)
    sleep(1)


def simulate_data():
    print("Simulating data stream....")
    duration = 30
    #duration = 2*365
    x = 50000
    now = datetime.today()
    initial_date = now - timedelta(days=duration)
    sim_date = initial_date
    range_min = 20
    range_max = 40
    humid_min = 30
    humid_max = 80
    while(sim_date <= now):
        x = x + 1
        sim_date = sim_date + timedelta(minutes=5)
        value = random.randrange(range_min, range_max)
        insert_metric(x, "Temperature", sim_date, "Engine Room", value)
        value = random.randrange(range_min, range_max)
        insert_metric(x, "Temperature", sim_date, "Salon", value)
        value = random.randrange(range_min, range_max)
        insert_metric(x, "Temperature", sim_date, "Forward Cabin", value)
        humidity = random.randrange(humid_min, humid_max)
        insert_metric(x, "Humidity", sim_date, "Forward Cabin", humidity)
        if (x % 10 == 0):
            range_min = range_min + 10
            range_max = range_max + 10
            if (range_min > 200):
                range_min = 0
                range_max = 20
        #print("sleep 1")

def connect_db():
    try:
        connection = psycopg2.connect(user="your_user",
                                  password="your_pw",
                                  host="127.0.0.1",
                                  port="5432",
                                  database="your_db")
        return(connection)

    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)


def query_db(connection):
    try:
        cursor = connection.cursor()
        postgreSQL_select_Query = "select * from metrics where location = %s"
        cursor.execute(postgreSQL_select_Query, ('Salon',))

        print("Selecting rows from lituya table using cursor.fetchall")
        mobile_records = cursor.fetchall()
    
        print("Print each row and it's columns values")
        for row in mobile_records:
            print("Id = ", row[0], )
            print("time = ", row[1])
            print("metric  = ", row[2], "\n")

    except (Exception, psycopg2.Error) as error :
        print ("Error while fetching data from PostgreSQL", error)

    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            print("PostgreSQL cursor is closed")

#def insert_metric(id, metric, datetime, location, value):
    #stmt = "INSERT INTO metrics (id, time, metric, location, value) VALUES (" + str(id) +", '" + str(datetime) + "', '" + metric + "', '" + location + "', " + str(value) + ");"
    #print(stmt)

def insert_metric(connection, id, metric, datetime, location, value):
    try:
        cursor = connection.cursor()
        postgres_insert_query = """ INSERT INTO metrics (id, time, metric, location, value) VALUES (%s,%s,%s,%s,%s)"""
        record_to_insert = (str(id), str(datetime), metric, location, value)
        cursor.execute(postgres_insert_query, record_to_insert)
        connection.commit()
        count = cursor.rowcount
        print (count, "Record inserted successfully into metrics")

    except (Exception, psycopg2.Error) as error :
        if(connection):
            print("Failed to insert record into metrics table", error)
    finally:
        #closing database connection.
        if(connection):
            cursor.close()
            print("PostgreSQL cursor is closed")

main()
