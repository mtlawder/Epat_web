from flask import Flask, render_template, redirect, request
from bokeh.plotting import figure, show, output_file, vplot
from bokeh.embed import autoload_server, components
from bokeh.models import Range1d
from bokeh.session import Session
from bokeh.document import Document

app=Flask(__name__)


import pandas as pd
import numpy as np
import sqlite3
import datetime
import re
#from sklearn.linear_model import LinearRegression

#NODE_info=pd.read_csv('N_info.csv')
#NODE_front=[NODE_info['NODE_NAME'][x].split(".")[0] for x in range(len(NODE_info))]

@app.route('/')
def main():
    return redirect('/index_Main')

@app.route('/index_Main',methods=['GET','POST'])
def index_Main():
    if request.method =='GET':
        #conn=sqlite3.connect('misodata.db')
        #A=pd.read_sql('SELECT * FROM LMPdata LIMIT 5',conn)
        #conn.close()
        #B=A.loc[0]['NODE']
        return render_template('/Milestone_Main.html', Nodename="",node1n="",node1s="",node1t="",nodes=['AMMO.UE.AZ','AMIL.EDWARDS2'])

    else:
        return render_template('/Milestone_Main.html', Nodename="",node1n="",node1s="",node1t="",nodes=['AMMO.UE.AZ','AMIL.EDWARDS2'])
    

@app.route('/wind_details', methods=['GET'])
def wind_details():
    #print "This is actually a different page"
    if request.method =='GET':
        return render_template('/wind_details.html')
    else:
        return redirect('/index_Main')
    
@app.route('/wind_analysis',methods=['GET','POST'])
def wind_analysis():
    if request.method =='GET':
        return render_template('/wind_analysis_report.html')
    else:
        node_name=request.form['nodename']
        script,div,script2,div2=run_wind_report(node_name)
        
        return render_template('wind_report.html',div=div,script=script,div2=div2,script2=script2)
    
    


def plotbokeh(nodename,start_date,end_date):
    conn=sqlite3.connect('misodata.db')
    npriceseries=pd.read_sql('SELECT DATE, PRICE FROM LMPdata WHERE NODE="%s" AND DATE>"%s" AND DATE<"%s" ORDER BY DATE' %(nodename,start_date,end_date),conn)
    #vals=pd.read_sql('SELECT NODE, LAT, LONG, STATE FROM LMPdata WHERE NODE="%s" AND DATE="%s"' %(nodename,start_date),conn)
    #lat, lon, state=vals.loc[0]['LAT'],vals.loc[0]['LONG'],vals.loc[0]['STATE']
    conn.close()
    return npriceseries

def movingaverage(interval, window_size):
    window = np.ones(int(window_size))/float(window_size)
    return np.convolve(interval, window, 'same')
    
def wind_speed_lookup(wind_speed,Farm_size):
    high_ws=wind_speed*(100./10)**0.45
    power_out=((high_ws-7.)**3/(30.-7)**3)
    if power_out<0:
        power_out=0.0
    if high_ws>30:
        power_out=1.0
    if high_ws>80:
        power_out=0.0
    return power_out*Farm_size


def plotbokehcomp(node1, node2, start_date,end_date):
    conn=sqlite3.connect('misodata.db')
    datestart, datefinish = start_date, end_date
    comppriceseries=pd.read_sql('SELECT DATE, SUM(CASE WHEN NODE = "%s" THEN PRICE ELSE -1.0 * PRICE END) As DIFF_COST FROM LMPdata WHERE (NODE="%s" OR NODE="%s") AND (DATE>"%s" AND DATE<"%s") GROUP BY DATE ORDER BY DATE' %(node1, node1, node2,datestart,datefinish),conn)
    conn.close()
    return comppriceseries

def run_wind_report(node_name):
    conn=sqlite3.connect('misodata.db')
    #LIMITS on dates2012-01-01 until 2015-12-31#
    start_date="2015-01-01"
    end_date="2016-01-01 00:00:00"

    YYYY=start_date[:4]

    Energy_Prices=pd.read_sql('SELECT DATE, NODE, PRICE FROM LMPdata WHERE DATE>"%s" and DATE<"%s" and NODE="%s" ORDER BY DATE' %(start_date,end_date,node_name),conn)

    city_name=re.sub(" ","",pd.read_sql('SELECT City_wind FROM wind_meta WHERE Node_Name="%s"' % (node_name),conn)['City_wind'][0])
    state_name=pd.read_sql('SELECT State FROM wind_meta WHERE Node_Name="%s"' % (node_name),conn)['State'][0]
    Wind_Speeds=pd.read_sql('SELECT * FROM %s_%s WHERE DATE>"%s" and DATE<"%s" ORDER BY DATE' % (state_name,city_name, start_date, end_date),conn)

    X_WindSpeed= [[Wind_Speeds.loc[x]['Wind_Speed']] for x in range(len(Wind_Speeds))]
    X_wind=[float(Wind_Speeds.loc[x]['Wind_Speed'].encode("utf8")) for x in range(len(Wind_Speeds))]
    y_price= [[Energy_Prices.loc[x]['PRICE']] for x in range(len(Energy_Prices))]
    y_p= [Energy_Prices.loc[x]['PRICE'] for x in range(len(Energy_Prices))]
    X_WindSpeed=np.array(X_WindSpeed)
    y_price=np.array(y_price)

    linreg=LinearRegression()
    wind_model=linreg.fit(X_WindSpeed,y_price)

    x_line=[x for x in range(30)]
    y_line=[wind_model.predict(x)[0] for x in range(30)]
    zero_x=[x-1 for x in range(32)]
    zero_y=[0]*32

    TOOLS="ypan,box_zoom,reset"
    pscat = figure(plot_width=480, plot_height=480, tools=TOOLS,toolbar_location="below")
    # add a circle renderer with a size, color, and alpha
    pscat.circle(X_wind,y_p, size=4, color="navy", alpha=0.5)
    pscat.line(x_line,y_line, color='red')
    pscat.line(zero_x,zero_y,color='black')
    pscat.x_range=Range1d(-0.5,30)
    pscat.y_range=Range1d(-20,80)
    #pscat.title = ' Energy Prices vs Ground Wind Speed for ' + node_name
    pscat.xaxis.axis_label = "Wind Speed (mph)"
    pscat.yaxis.axis_label = "Price/MWh ($)"
    script, div = components(pscat)

        

    Farm_size=20.

    Energy_Prices.columns=['Date','NODE','PRICE']
    Merged_Wind_Price=pd.merge(Energy_Prices,Wind_Speeds, on='Date')

    Combined_Revenue=[Merged_Wind_Price.loc[x]["PRICE"]*wind_speed_lookup(float(Merged_Wind_Price.loc[x]['Wind_Speed']),Farm_size) for x in range(len(Merged_Wind_Price))]
    Merged_Wind_Price["Revenue"]=Combined_Revenue

    Day_Summary=[]
    for x in range(len(Merged_Wind_Price)/24):
        Agg_Wind=0
        Agg_Rev=0
        for y in range(24):
            Agg_Wind+=float(Merged_Wind_Price.loc[x*24+y]['Wind_Speed'])
            Agg_Rev+=Merged_Wind_Price.loc[x*24+y]['Revenue']
        Day_Summary+=[[Agg_Wind,Merged_Wind_Price.loc[x*24]['Date'],Agg_Rev]]
    Day_Summary.sort()


    X_Wind=np.array([x[0] for x in Day_Summary])
    y_rev=np.array([x[2] for x in Day_Summary])
    y_moav_rev = movingaverage(y_rev, 35)
    zero_x=[x-1 for x in range(452)]
    zero_y=[0]*452

    TOOLS="ypan,box_zoom,reset"
    pscat2 = figure(plot_width=480, plot_height=480, tools=TOOLS,toolbar_location="below")
    # add a circle renderer with a size, color, and alpha
    pscat2.circle(X_Wind,y_rev, size=4, color="navy", alpha=0.5)
    pscat2.line(X_Wind,y_moav_rev, color='red')
    pscat2.line(zero_x,zero_y,color='black')
    pscat2.x_range=Range1d(0,450)
    pscat2.y_range=Range1d(-1000,10000)
    pscat.xaxis.axis_label = "Daily Energy Production (MWh)"
    pscat.yaxis.axis_label = "Daily Revenue"
    script2, div2 = components(pscat2)
    return script, div, script2, div2
        
    
        
@app.route('/data_plot',methods=['GET','POST'])
def data_plot():
    if request.method=="GET":
        return redirect('/index_Main')

    else:
        node=request.form['nodename']
        start_date=datetime.datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
        end_date=datetime.datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()


        node=node.upper()


        if any(NODE_info.NODE_NAME==node)==False:
            if node.split(".")[0] in NODE_front:
                Poss_others=", ".join(NODE_info[NODE_info['NODE_NAME'].str.contains(node.split(".")[0])]['NODE_NAME'].tolist())
                nodeout=node.split(".")[1]+ " is not a proper extension for "+node.split(".")[0]+". Did you mean "+Poss_others

            else:
                nodeout=node+' is not a Node name'
            return render_template('Milestone_Main.html', Nodename=nodeout)
        elif end_date < start_date==True:
            nodeout="Problem with Dates. Choose new dates."

            return render_template('Milestone_Main.html', Nodename=nodeout)
        #elif end_date < start_date==True:
        #    nodeout="Problem with Dates. Choose new dates."
        else:
            nodefind=NODE_info.loc[NODE_info['NODE_NAME']==node].index.tolist()[0]
            node1n=NODE_info.loc[nodefind]['NODE_NAME']
            node1s=NODE_info.loc[nodefind]['STATE']
            node1t=NODE_info.loc[nodefind]['TYPE']
            #if nodenum=='1nodes':
            nodenum=request.form['nodenum']
            if nodenum=='1nodes':

                dfprice=plotbokeh(node1n,start_date,end_date)
                bdate=np.array(dfprice['DATE'], dtype=np.datetime64)
                bzero=np.array([0]*len(bdate))
                bprice=np.array(dfprice['PRICE'])
                Avg_price=round(sum(bprice)/float(len(bprice)),2)
                Tot_rev=round(sum(bprice)*100.,2)                                          
                TOOLS="ypan,box_zoom,reset"
                p1=figure(x_axis_type='datetime',toolbar_location="below",tools=TOOLS,plot_width=900, plot_height=400)
                p1.y_range = Range1d(-20, 80)
                p1.x_range = Range1d(start_date, end_date)
                p1.line(bdate,bprice,line_width=2)
                p1.patch(np.append(bdate[0],np.append(bdate,bdate[-1])), np.append([0],np.append(bprice,[0])), alpha=0.8)
                p1.line(bdate,bzero,line_width=1,color='black')

                p1.title = ' Energy Prices for ' + node1n
                p1.xaxis.axis_label = "Date"
                p1.yaxis.axis_label = "Price/MWh"
                script, div = components(p1)

                #script,div='p','q'
                #Avg_price='a'
                cout=""
                return render_template('Onenode_plot.html',node1n=node1n, script=script, div=div,cout=cout,sdate=start_date,edate=end_date,Tot_rev=Tot_rev,Avg_price=Avg_price)

            else:
                node2=request.form['nodename2']
                node2=node2.upper()
                if any(NODE_info.NODE_NAME==node2)==False:
                    if node2.split(".")[0] in NODE_front:
                        Poss_others=", ".join(NODE_info[NODE_info['NODE_NAME'].str.contains(node2.split(".")[0])]['NODE_NAME'].tolist())
                        nodeout=node2.split(".")[1]+ " is not a proper extension for "+node2.split(".")[0]+". Did you mean "+Poss_others
                    else:
                        nodeout=node2+' is not a Node name'
                    return render_template('Milestone_Main.html', Nodename=nodeout)
                else:


                    dfprice=plotbokehcomp(node1n,node2, start_date, end_date)
                    node1df=plotbokeh(node1n,start_date,end_date)
                    node2df=plotbokeh(node2,start_date,end_date)
                    bdate=np.array(dfprice['DATE'], dtype=np.datetime64)
                    bzero=np.array([0]*len(bdate))
                    bprice=np.array(dfprice['DIFF_COST'])
                    n1price=np.array(node1df['PRICE'])
                    n2price=np.array(node2df['PRICE'])
                    transcost=round(sum(n1price-n2price)/float(len(n1price)),2)
                    TOOLS="ypan,box_zoom,reset"
                    p1=figure(x_axis_type='datetime',toolbar_location="below",tools=TOOLS,plot_width=900, plot_height=400)
                    p2=figure(x_axis_type='datetime',toolbar_location="below",tools=TOOLS,plot_width=900, plot_height=400)
                    p1.y_range = Range1d(-30, 30)
                    p1.x_range = Range1d(start_date, end_date)
                    p1.line(bdate,bprice,line_width=2)
                    p1.patch(np.append(bdate[0],np.append(bdate,bdate[-1])), np.append([0],np.append(bprice,[0])), alpha=0.8)
                    p1.line(bdate,bzero,line_width=1,color='black')
                    p2.y_range = Range1d(-20, 80)
                    p2.x_range = Range1d(start_date, end_date)
                    p2.legend
                    p2.line(bdate,n1price,line_width=1,color='green')
                    p2.line(bdate,n2price,line_width=1,color='red')
                    p2.line(bdate,bzero,line_width=1,color='black')
                    p2.legend.location = "bottom_right"
                    p1.title = "Temporal Energy Price Differences"
                    p1.xaxis.axis_label = "Date"
                    p1.yaxis.axis_label = "Transmission Cost($/MWh)"
                    p2.title = "Individual Node Prices"
                    p2.xaxis.axis_label = "Date"
                    p2.yaxis.axis_label = "Price ($/MWh)"
                    script, div = components(p1)
                    script2,div2 = components(p2)
                    Total_Charge=dfprice['DIFF_COST'].sum(axis=0)
                    cout=""
                    #cout= "The total charge was $"+str(Total_Charge)+" per MWh for transmitting energy from "+node1n+" to "+node2+"."
                    #cout2= "This charge is for the time range "+start_date+" to "+end_date+"."
                    #script=bdate
                    #div=bprice
                    #return render_template('/Milestone_Main.html',Nodename="",node1n=node1n,node1s=node1s,node1t=node1t)
                #else:
                #    script='empty'
                #    div='empty'
                    return render_template('Twonode_plot.html',node1n=node1n,node2=node2, script=script, div=div,cout=cout, script2=script2, div2=div2,transcost=transcost)


#@app.route('/Onenode_plot',methods=['GET','POST'])
#def Onenode_plot():
#    return render_template('Onenode_plot.html',node1n=node1n)
    
    
if __name__ == '__main__':
    app.run(host='159.203.65.80',port=33506)


