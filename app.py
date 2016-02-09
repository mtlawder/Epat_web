from flask import Flask, render_template, redirect, request
from bokeh.plotting import figure, show, output_file, vplot
from bokeh.embed import autoload_server, components
from bokeh.models import Range1d
from bokeh.session import Session
from bokeh.document import Document

app=Flask(__name__)

#import urllib2
#import json
#import pandas as pd
#import numpy as np
#import os
#import sqlite3
#import datetime

#import re
#from sklearn.linear_model import LinearRegression

@app.route('/')
def main():
    return redirect('/index_Main')

@app.route('/index_Main')
def index_Main():
    return render_template('Milestone_Main.html')
    
    
if __name__ == '__main__':
    app.run(host='159.203.65.80',port=33506)


